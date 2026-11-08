<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowRight, BarChart3, BookOpenCheck, CalendarDays, Check, ChevronRight, ClipboardList, FileSearch, GraduationCap, Layers3, LoaderCircle, Play, RefreshCw, ScanLine, Sparkles, TrendingUp, TriangleAlert, Users } from '@lucide/vue';
import { generateAiClassroomGuidance, getAnatomyGlossary, getAnatomyMistakes, getAnatomyRecords, getMyClassroomGuidance, getMyClassrooms, getQuizMistakes, getQuizRecords, joinClassroom } from '../api';
import emptyIllustration from '../assets/medical/archive-empty.webp';
import MarkdownContent from '../components/MarkdownContent.vue';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';
import { trainingStore } from '../stores/training';
import type { AnatomyAttempt, AnatomyLearningSummary, AnatomyMistake, ClassroomGuidance, ClassroomSummary, QuizAttempt } from '../types';

type ArchiveTab = 'records' | 'statistics' | 'mistakes' | 'quiz-mistakes';

const route = useRoute();
const router = useRouter();
const activeTab = computed(() => {
  const tab = route.query.tab;
  if (tab === 'mistakes' || tab === 'quiz-mistakes' || tab === 'statistics') return tab;
  return tab === 'review' ? 'statistics' : 'records';
});
const termCount = ref(0);
const structureCount = ref(0);
const loading = ref(true);
const records = ref<AnatomyAttempt[]>([]);
const mistakes = ref<AnatomyMistake[]>([]);
const summary = ref<AnatomyLearningSummary>({ total: 0, correct: 0, accuracy: 0, average_score: 0 });
const quizRecords = ref<QuizAttempt[]>([]);
const quizMistakes = ref<QuizAttempt[]>([]);
const quizSummary = ref<AnatomyLearningSummary>({ total: 0, correct: 0, accuracy: 0, average_score: 0 });
const classrooms = ref<ClassroomSummary[]>([]);
const activeClassId = ref('');
const guidance = ref<ClassroomGuidance[]>([]);
const joinCode = ref('');
const joining = ref(false);
const aiGuidanceLoading = ref(false);
const classroomMessage = ref('');
const classroomError = ref('');
const loadError = ref('');

const visibleGuidance = computed(() => {
  let hasAi = false;
  return guidance.value.filter((item) => {
    if (item.source !== 'ai') return true;
    if (hasAi) return false;
    hasAi = true;
    return true;
  }).slice(0, 4);
});

function displayText(value: string) {
  if (!value) return value;
  try {
    const repaired = value.replace(/[\ufffd]/g, '');
    return repaired || value;
  } catch {
    return value;
  }
}

const activeClass = computed(() => classrooms.value.find((item) => item.id === activeClassId.value) ?? classrooms.value[0] ?? null);

function selectTab(tab: ArchiveTab) {
  void router.replace({ path: '/student/archive', query: { tab } });
}

const showAll = ref(false);
const classCodeInput = ref<HTMLInputElement | null>(null);
const classroomPanel = ref<HTMLElement | null>(null);
const latestRecords = computed(() => [
  ...records.value.map((item) => ({
    key: 'location-' + item.id, title: item.title, time: item.created_at,
    context: [item.system, item.organ, item.target].filter(Boolean).join(' · '),
    kind: '空间定位', score: item.score, correct: item.correct, feedback: item.feedback
  })),
  ...quizRecords.value.map((item) => ({
    key: 'quiz-' + item.id, title: item.question_stem, time: item.updated_at || item.created_at,
    context: item.structure_label, kind: '结构刷题', score: item.score, correct: item.correct, feedback: item.feedback
  }))
].sort((a, b) => Date.parse(b.time) - Date.parse(a.time)));
const visibleRecords = computed(() => showAll.value ? latestRecords.value : latestRecords.value.slice(0, 3));
const totals = computed(() => {
  const total = summary.value.total + quizSummary.value.total;
  const correct = summary.value.correct + quizSummary.value.correct;
  const wrong = total - correct;
  return { total, correct, wrong, errorRate: total ? Math.round(wrong / total * 100) : 0 };
});
const trend = computed(() => {
  const days = new Map<string, { total: number; wrong: number }>();
  for (const item of latestRecords.value) {
    const date = new Date(item.time);
    if (Number.isNaN(date.getTime())) continue;
    const day = date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
    const count = days.get(day) ?? { total: 0, wrong: 0 };
    count.total += 1;
    count.wrong += Number(!item.correct);
    days.set(day, count);
  }
  const recent = [...days].slice(0, 7).reverse();
  return recent.map(([day, count], index) => {
    const rate = Math.round(count.wrong / count.total * 100);
    return {
      day, label: day.split('/').slice(-2).join('-'), rate,
      x: recent.length === 1 ? 145 : 34 + index * 222 / (recent.length - 1),
      y: 85 - rate * 0.72
    };
  });
});
const trendLine = computed(() => trend.value.map(({ x, y }) => x + ',' + y).join(' '));
const statisticGroups = [
  { label: '空间定位', summary, tab: 'mistakes' },
  { label: '结构刷题', summary: quizSummary, tab: 'quiz-mistakes' }
] as const;

async function openReviewAdvice() {
  if (activeClass.value) {
    const advice = requestAiGuidance();
    await nextTick();
    classroomPanel.value?.scrollIntoView({ block: 'start' });
    await advice;
  } else {
    classCodeInput.value?.focus();
  }
}

function startQuiz() {
  router.push({ path: '/student/anatomy', query: { mode: 'practice' } });
}

function formatTime(value: string) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function loadArchive() {
  loading.value = true;
  loadError.value = '';
  const [recordResult, mistakeResult, quizRecordResult, quizMistakeResult] = await Promise.allSettled([
    getAnatomyRecords(),
    getAnatomyMistakes(),
    getQuizRecords(),
    getQuizMistakes()
  ]);
  if (recordResult.status === 'fulfilled') {
    records.value = recordResult.value.items;
    summary.value = recordResult.value.summary;
  } else {
    loadError.value = '测验记录暂时无法读取。';
  }
  if (mistakeResult.status === 'fulfilled') {
    mistakes.value = mistakeResult.value.items;
  } else {
    loadError.value = '错题本暂时无法读取。';
  }
  if (quizRecordResult.status === 'fulfilled') {
    quizRecords.value = quizRecordResult.value.items;
    quizSummary.value = quizRecordResult.value.summary;
  } else {
    loadError.value = '刷题记录暂时无法读取。';
  }
  if (quizMistakeResult.status === 'fulfilled') {
    quizMistakes.value = quizMistakeResult.value.items;
  } else {
    loadError.value = '刷题错题暂时无法读取。';
  }
  loading.value = false;
}

async function loadClassroom() {
  classroomError.value = '';
  try {
    const result = await getMyClassrooms();
    classrooms.value = result.items;
    if (!classrooms.value.some((item) => item.id === activeClassId.value)) {
      activeClassId.value = classrooms.value[0]?.id ?? '';
    }
    if (activeClassId.value) {
      guidance.value = (await getMyClassroomGuidance(activeClassId.value)).items;
      if (activeClass.value) trainingStore.saveProfile({ className: activeClass.value.name });
    } else {
      guidance.value = [];
    }
  } catch (reason) {
    classroomError.value = reason instanceof Error ? reason.message : '班级信息暂时无法读取';
  }
}

async function joinTeacherClass() {
  const code = joinCode.value.trim();
  if (!code || joining.value) return;
  joining.value = true;
  classroomError.value = '';
  classroomMessage.value = '';
  try {
    const classroom = await joinClassroom(code);
    const existing = classrooms.value.find((item) => item.id === classroom.id);
    if (existing) Object.assign(existing, classroom);
    else classrooms.value = [classroom, ...classrooms.value];
    activeClassId.value = classroom.id;
    joinCode.value = '';
    classroomMessage.value = `已加入“${classroom.name}”`;
    await loadClassroom();
  } catch (reason) {
    classroomError.value = reason instanceof Error ? reason.message : '加入班级失败';
  } finally {
    joining.value = false;
  }
}

async function selectClassroom(classId: string) {
  activeClassId.value = classId;
  guidance.value = [];
  try {
    guidance.value = (await getMyClassroomGuidance(classId)).items;
  } catch (reason) {
    classroomError.value = reason instanceof Error ? reason.message : '指导记录读取失败';
  }
}

async function requestAiGuidance() {
  if (!activeClass.value || aiGuidanceLoading.value) return;
  aiGuidanceLoading.value = true;
  classroomError.value = '';
  try {
    const created = await generateAiClassroomGuidance(activeClass.value.id);
    guidance.value = [created, ...guidance.value.filter((item) => item.id !== created.id)];
    classroomMessage.value = created.reused ? '已显示最近一次 AI 学习建议。' : 'AI 学习教练已根据你的真实错题生成新建议。';
  } catch (reason) {
    classroomError.value = reason instanceof Error ? reason.message : 'AI建议生成失败';
  } finally {
    aiGuidanceLoading.value = false;
  }
}

onMounted(async () => {
  void loadArchive();
  void loadClassroom();
  try {
    termCount.value = (await getAnatomyGlossary()).count;
  } catch {
    termCount.value = 0;
  }
  try {
    const manifest = await fetch('/anatomy/atlas.json').then((response) => response.json());
    structureCount.value = manifest.parts?.length ?? 0;
  } catch {
    structureCount.value = 0;
  }
});
</script>

<template>
  <div class="workspace-page learning-archive-page">
    <section class="archive-banner" aria-labelledby="archive-title">
      <div class="archive-banner-copy">
        <h1 id="archive-title"><BarChart3 aria-hidden="true" />学习档案</h1>
        <p>汇总空间定位和结构刷题的作答记录、得分和错题，用于安排下一次复习。</p>
        <nav class="archive-pills" data-tour="archive-tabs" aria-label="学习档案分类">
          <button type="button" :aria-pressed="activeTab === 'records'" @click="selectTab('records')">学习记录</button>
          <button type="button" :aria-pressed="activeTab !== 'records'" @click="selectTab('statistics')">测验统计</button>
        </nav>
      </div>
      <button class="archive-advice" type="button" :disabled="aiGuidanceLoading" @click="openReviewAdvice">
        <LoaderCircle v-if="aiGuidanceLoading" class="spin" :size="25" />
        <Sparkles v-else :size="25" />
        <span><strong>{{ aiGuidanceLoading ? '正在生成建议' : '智能复习建议' }}</strong><small>基于学习表现生成</small></span>
        <ChevronRight :size="16" />
      </button>
    </section>

    <section ref="classroomPanel" class="archive-surface archive-class-strip" aria-label="班级与学习指导">
      <div class="archive-class-info">
        <span class="archive-medallion"><GraduationCap :size="26" /></span>
        <div>
          <h2>{{ activeClass?.name ?? '加入班级' }}</h2>
          <p v-if="activeClass">{{ activeClass.teacher_name }} · {{ activeClass.student_count }} 名学生 · 班级码 {{ activeClass.code }}</p>
          <p v-else>向老师获取班级码，加入后可接收教师指导和学习建议。</p>
        </div>
      </div>
      <form class="archive-join" @submit.prevent="joinTeacherClass">
        <label><span aria-hidden="true">#</span><input ref="classCodeInput" v-model="joinCode" maxlength="16" aria-label="班级码" placeholder="请输入 6 位班级码" /></label>
        <button class="button-primary" type="submit" :disabled="joining || joinCode.trim().length < 4">
          <LoaderCircle v-if="joining" class="spin" :size="17" /><Users v-else :size="17" />{{ joining ? '加入中' : '加入班级' }}
        </button>
      </form>
      <select v-if="classrooms.length > 1" class="archive-class-select" :value="activeClassId" aria-label="切换班级" @change="selectClassroom(($event.target as HTMLSelectElement).value)">
        <option v-for="item in classrooms" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select>
      <p v-if="classroomError" class="archive-feedback is-error" role="alert"><TriangleAlert :size="15" />{{ classroomError }}</p>
      <p v-else-if="classroomMessage" class="archive-feedback" role="status"><Check :size="15" />{{ classroomMessage }}</p>
      <div v-if="visibleGuidance.length" class="archive-guidance">
        <article v-for="item in visibleGuidance" :key="item.id">
          <header><strong>{{ displayText(item.author_name) }}</strong><small>{{ formatTime(item.created_at) }}</small></header>
          <MarkdownContent :content="displayText(item.content)" />
          <small v-if="item.recommended_score != null">建议目标 {{ item.recommended_score }} 分</small>
        </article>
      </div>
    </section>

    <section class="archive-metrics" aria-label="学习指标">
      <article class="archive-surface"><span class="archive-medallion"><Layers3 /></span><div><small>教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }} <small>个</small></strong></div></article>
      <article class="archive-surface"><span class="archive-medallion"><ScanLine /></span><div><small>可探索结构</small><strong>{{ structureCount || '—' }}</strong></div></article>
      <article class="archive-surface"><span class="archive-medallion"><ClipboardList /></span><div><small>定位作答</small><strong>{{ loading || loadError ? '—' : summary.total }}</strong></div></article>
      <article class="archive-surface"><span class="archive-medallion"><BookOpenCheck /></span><div><small>中文对照名</small><strong>{{ termCount || '—' }}</strong></div></article>
      <article class="archive-surface"><span class="archive-medallion"><TrendingUp /></span><div><small>刷题作答</small><strong>{{ loading || loadError ? '—' : quizSummary.total }}</strong></div></article>
    </section>

    <section v-if="loading || loadError" class="archive-surface archive-status" role="status">
      <LoaderCircle v-if="loading" class="spin" :size="19" />
      <TriangleAlert v-else :size="19" />
      {{ loading ? '正在读取学习记录' : loadError }}
      <button v-if="loadError && !loading" class="archive-link" type="button" @click="loadArchive"><RefreshCw :size="14" />重试</button>
    </section>

    <template v-else>
      <div class="archive-overview">
        <section v-if="activeTab === 'records'" class="archive-surface archive-panel">
          <header class="archive-panel-heading">
            <h2><ClipboardList />学习记录</h2>
            <button v-if="latestRecords.length > 3" class="archive-link" type="button" :aria-expanded="showAll" @click="showAll = !showAll">{{ showAll ? '收起记录' : '全部记录' }}<ChevronRight :size="16" /></button>
          </header>
          <div v-if="visibleRecords.length" class="archive-records">
            <details v-for="item in visibleRecords" :key="item.key">
              <summary>
                <span class="archive-record-play"><Play :size="15" fill="currentColor" /></span>
                <span class="archive-record-text"><strong>{{ item.title }}</strong><small><CalendarDays :size="13" />{{ formatTime(item.time) }} · {{ item.kind }}</small></span>
                <strong class="archive-record-score">{{ item.score }} 分</strong>
                <ChevronRight class="archive-record-arrow" :size="16" />
              </summary>
              <div class="archive-record-detail"><b>{{ item.correct ? '作答正确' : '建议复习' }}</b> · {{ item.context }}<p v-if="item.feedback">{{ item.feedback }}</p></div>
            </details>
          </div>
          <p v-else class="archive-quiet">完成测验后，这里会显示最近的学习记录。</p>
        </section>

        <section v-else class="archive-surface archive-panel">
          <header class="archive-panel-heading">
            <h2><BarChart3 />测验统计</h2>
            <button class="archive-link" type="button" @click="loadArchive"><RefreshCw :size="14" />刷新</button>
          </header>
          <div class="archive-stat-groups">
            <article v-for="group in statisticGroups" :key="group.tab">
              <strong>{{ group.label }}</strong>
              <p>{{ group.summary.value.total }} 次作答 · {{ group.summary.value.correct }} 次正确</p>
              <p>平均得分 {{ group.summary.value.total ? group.summary.value.average_score + ' 分' : '—' }}</p>
              <button class="archive-link" type="button" :aria-pressed="activeTab === group.tab" @click="selectTab(group.tab)">查看错题<ChevronRight :size="14" /></button>
            </article>
          </div>
        </section>

        <section class="archive-surface archive-panel">
          <header class="archive-panel-heading"><h2><TriangleAlert />错题分析</h2></header>
          <div class="archive-analysis">
            <div class="archive-rates">
              <div class="archive-donut" :style="{ '--error-rate': totals.errorRate + '%' }">
                <strong>{{ totals.total ? totals.errorRate + '%' : '—' }}</strong><small>错题率</small>
              </div>
              <dl class="archive-legend">
                <div><dt>答错</dt><dd>{{ totals.wrong }} 次</dd></div>
                <div><dt>答对</dt><dd>{{ totals.correct }} 次</dd></div>
                <div><dt>总作答</dt><dd>{{ totals.total }} 次</dd></div>
              </dl>
            </div>
            <div class="archive-trend">
              <h3>近 7 个作答日错题率</h3>
              <svg v-if="trend.length" viewBox="0 0 275 110" role="img" :aria-label="trend.map(point => point.day + ' 错题率 ' + point.rate + '%').join('，')">
                <g v-for="tick in [0, 50, 100]" :key="tick" class="archive-gridline">
                  <line x1="34" x2="256" :y1="85 - tick * .72" :y2="85 - tick * .72" />
                  <text x="0" :y="89 - tick * .72">{{ tick }}%</text>
                </g>
                <polygon v-if="trend.length > 1" class="archive-trend-area" :points="trend[0].x + ',85 ' + trendLine + ' ' + trend[trend.length - 1].x + ',85'" />
                <polyline class="archive-trend-line" :points="trendLine" />
                <g v-for="point in trend" :key="point.day">
                  <circle :cx="point.x" :cy="point.y" r="3.2"><title>{{ point.day }} · {{ point.rate }}%</title></circle>
                  <text :x="point.x" y="103" text-anchor="middle">{{ point.label }}</text>
                </g>
              </svg>
              <p v-else class="archive-quiet">暂无作答趋势</p>
            </div>
          </div>
        </section>
      </div>

      <section v-if="activeTab === 'mistakes' || activeTab === 'quiz-mistakes'" class="archive-surface archive-panel">
        <header class="archive-panel-heading"><h2><BookOpenCheck />{{ activeTab === 'mistakes' ? '定位错题' : '刷题错题' }}</h2></header>
      <template v-if="activeTab === 'mistakes' && mistakes.length">
        <div class="archive-mistake-list">
          <article v-for="item in mistakes" :key="item.exercise_id" class="archive-mistake-item">
            <header><span>{{ item.system }}<template v-if="item.organ"> · {{ item.organ }}</template></span><b>错误 {{ item.attempt_count }} 次</b></header>
            <h3>{{ item.title }} · {{ item.target }}</h3>
            <p>{{ item.explanation }}</p>
            <small>{{ item.clinical_link }}</small>
            <footer><span>最近作答 {{ formatTime(item.latest_at) }}</span><strong>最高 {{ item.best_score }} 分</strong></footer>
          </article>
        </div>
      </template>

      <template v-else-if="activeTab === 'quiz-mistakes' && quizMistakes.length">
        <div class="archive-quiz-list">
          <article v-for="item in quizMistakes" :key="item.question_id" class="archive-quiz-item">
            <header>
              <span>{{ item.system || item.structure_label }} · {{ item.question_type === 'single_choice' ? '选择题' : item.question_type === 'true_false' ? '判断题' : '简答题' }}</span>
              <b>{{ item.score }} 分</b>
            </header>
            <h3>{{ item.question_stem }}</h3>
            <div class="quiz-answer-compare">
              <p><small>我的答案</small><strong>{{ item.answer || '未作答' }}</strong></p>
              <p><small>正确答案</small><strong>{{ item.correct_answer || '见答案解析' }}</strong></p>
            </div>
            <p>{{ item.feedback }}</p>
            <div v-if="item.missed_points.length" class="quiz-missed-points">
              <small>遗漏要点</small>
              <span v-for="point in item.missed_points" :key="point">{{ point }}</span>
            </div>
            <footer><span>最近作答 {{ formatTime(item.updated_at) }}</span><strong>{{ item.structure_label }}</strong></footer>
          </article>
        </div>
      </template>

        <p v-else class="archive-quiet">暂无错题记录。</p>
      </section>

      <section v-if="activeTab === 'records' && !latestRecords.length" class="archive-surface archive-empty">
        <img :src="emptyIllustration" alt="" width="540" height="360" />
        <div>
          <FileSearch :size="34" aria-hidden="true" />
          <h2>还没有测验记录</h2>
          <p>进入虚拟解剖室，在二维器官或精细结构图中完成定位并提交，记录会自动汇总到这里。</p>
          <button class="button-primary" type="button" @click="startQuiz">开始空间定位测验<ArrowRight :size="17" /></button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped src="../learning-archive.css"></style>
