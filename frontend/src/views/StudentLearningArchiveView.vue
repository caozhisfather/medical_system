<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, Check, ClipboardList, Crosshair, GraduationCap, Layers3, LoaderCircle, RefreshCw, ScanLine, Sparkles, TriangleAlert, Users } from '@lucide/vue';
import { generateAiClassroomGuidance, getAnatomyGlossary, getAnatomyMistakes, getAnatomyRecords, getMyClassroomGuidance, getMyClassrooms, getQuizMistakes, getQuizRecords, joinClassroom } from '../api';
import MarkdownContent from '../components/MarkdownContent.vue';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';
import { trainingStore } from '../stores/training';
import type { AnatomyAttempt, AnatomyLearningSummary, AnatomyMistake, ClassroomGuidance, ClassroomSummary, QuizAttempt } from '../types';

type ArchiveTab = 'records' | 'mistakes' | 'quiz-mistakes';

const route = useRoute();
const router = useRouter();
const activeTab = ref<ArchiveTab>(
  route.query.tab === 'mistakes' ? 'mistakes' : route.query.tab === 'quiz-mistakes' ? 'quiz-mistakes' : 'records'
);
const termCount = ref(0);
const structureCount = ref(0);
const loading = ref(false);
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

watch(() => route.query.tab, (tab) => {
  activeTab.value = tab === 'mistakes' ? 'mistakes' : tab === 'quiz-mistakes' ? 'quiz-mistakes' : 'records';
});

function selectTab(tab: ArchiveTab) {
  activeTab.value = tab;
  void router.replace({ path: '/student/archive', query: { tab } });
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
  await loadArchive();
  await loadClassroom();
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
    <section class="archive-heading">
      <div>
        <span class="section-kicker">学习沉淀与持续改进</span>
        <h1>学习档案</h1>
        <p>汇总二维器官与精细结构定位测验的作答记录、得分和错题，用于安排下一次复习。</p>
      </div>
      <span class="archive-summary"><Sparkles :size="18" /><strong>探索—测验—复习</strong><small>形成连续学习闭环</small></span>
    </section>

    <section class="archive-classroom">
      <div class="classroom-summary">
        <span class="classroom-icon"><GraduationCap :size="22" /></span>
        <div v-if="activeClass">
          <small>当前班级</small>
          <strong>{{ activeClass.name }}</strong>
          <p>{{ activeClass.teacher_name }} · {{ activeClass.student_count }} 名学生 · 班级码 {{ activeClass.code }}</p>
        </div>
        <div v-else>
          <small>教师班级</small>
          <strong>尚未加入班级</strong>
          <p>向老师获取班级码，加入后可以接收教师指导和AI学习建议。</p>
        </div>
        <select v-if="classrooms.length > 1" :value="activeClassId" aria-label="切换班级" @change="selectClassroom(($event.target as HTMLSelectElement).value)">
          <option v-for="item in classrooms" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <button v-if="activeClass" class="button-secondary" type="button" :disabled="aiGuidanceLoading" @click="requestAiGuidance">
          <LoaderCircle v-if="aiGuidanceLoading" class="spin" :size="16" /><Sparkles v-else :size="16" />{{ aiGuidanceLoading ? '分析中' : 'AI学习建议' }}
        </button>
      </div>

      <form class="classroom-join" @submit.prevent="joinTeacherClass">
        <label><span>加入教师班级</span><input v-model="joinCode" maxlength="16" placeholder="输入 6 位班级码" /></label>
        <button class="button-primary" type="submit" :disabled="joining || joinCode.trim().length < 4">
          <LoaderCircle v-if="joining" class="spin" :size="16" /><Users v-else :size="16" />{{ joining ? '加入中' : '加入班级' }}
        </button>
      </form>

      <p v-if="classroomError" class="classroom-feedback is-error"><TriangleAlert :size="15" />{{ classroomError }}</p>
      <p v-else-if="classroomMessage" class="classroom-feedback is-ok"><Check :size="15" />{{ classroomMessage }}</p>

      <div v-if="visibleGuidance.length" class="student-guidance-list">
        <article v-for="item in visibleGuidance" :key="item.id" :class="{ ai: item.source === 'ai' }">
          <header><strong>{{ displayText(item.author_name) }}</strong><span>{{ formatTime(item.created_at) }}</span></header>
          <MarkdownContent :content="displayText(item.content)" />
          <small v-if="item.recommended_score !== null && item.recommended_score !== undefined">建议目标：{{ item.recommended_score }} 分</small>
        </article>
      </div>
    </section>

    <section class="archive-coverage">
      <article><Layers3 :size="19" /><span><small>教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong></span></article>
      <article><ScanLine :size="19" /><span><small>可探索结构</small><strong>{{ structureCount || '—' }}</strong></span></article>
      <article><ClipboardList :size="19" /><span><small>已答题目</small><strong>{{ summary.total }}</strong></span></article>
      <article><BookOpenCheck :size="19" /><span><small>中文解剖名</small><strong>{{ termCount || '—' }}</strong></span></article>
      <article><Sparkles :size="19" /><span><small>刷题作答</small><strong>{{ quizSummary.total }}</strong></span></article>
    </section>

    <nav class="archive-tabs" data-tour="archive-tabs" aria-label="学习档案分类">
      <button type="button" :class="{ active: activeTab === 'records' }" @click="selectTab('records')">
        <ClipboardList :size="18" /><span><strong>测验记录</strong><small>{{ records.length }} 次作答 · 平均 {{ summary.average_score }} 分</small></span>
      </button>
      <button type="button" :class="{ active: activeTab === 'mistakes' }" @click="selectTab('mistakes')">
        <TriangleAlert :size="18" /><span><strong>错题本</strong><small>{{ mistakes.length }} 个待复习结构</small></span>
      </button>
      <button type="button" :class="{ active: activeTab === 'quiz-mistakes' }" @click="selectTab('quiz-mistakes')">
        <BookOpenCheck :size="18" /><span><strong>刷题错题</strong><small>{{ quizMistakes.length }} 道待复盘题</small></span>
      </button>
      <button class="archive-refresh" type="button" :disabled="loading" @click="loadArchive">
        <RefreshCw :size="17" :class="{ spin: loading }" />刷新
      </button>
    </nav>

    <section class="archive-content">
      <div v-if="loading" class="archive-state"><RefreshCw class="spin" :size="24" />正在读取学习记录</div>
      <div v-else-if="loadError" class="archive-state is-error"><TriangleAlert :size="24" />{{ loadError }}</div>

      <template v-else-if="activeTab === 'records' && records.length">
        <div class="archive-scoreboard">
          <article><small>累计作答</small><strong>{{ summary.total }}</strong><span>次</span></article>
          <article><small>定位正确</small><strong>{{ summary.correct }}</strong><span>次</span></article>
          <article><small>正确率</small><strong>{{ summary.accuracy }}</strong><span>%</span></article>
          <article><small>平均得分</small><strong>{{ summary.average_score }}</strong><span>分</span></article>
        </div>
        <div class="archive-record-list">
          <article v-for="item in records" :key="item.id" class="archive-record-item">
            <header>
              <span>{{ item.system }}<template v-if="item.organ"> · {{ item.organ }}</template></span>
              <b :class="item.correct ? 'is-correct' : 'is-wrong'">{{ item.correct ? '定位正确' : '需要复习' }}</b>
            </header>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.feedback }}</p>
            </div>
            <footer>
              <span>{{ formatTime(item.created_at) }} · 目标 {{ item.target }}</span>
              <strong>{{ item.score }} 分</strong>
            </footer>
          </article>
        </div>
      </template>

      <template v-else-if="activeTab === 'mistakes' && mistakes.length">
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

      <div v-else class="archive-empty">
        <Crosshair :size="30" />
        <strong>{{ activeTab === 'records' ? '还没有测验记录' : activeTab === 'mistakes' ? '错题本还是空的' : '刷题错题还是空的' }}</strong>
        <p>{{ activeTab === 'records' ? '进入虚拟解剖室，在二维器官或精细结构图中完成定位并提交，记录会自动汇总到这里。' : activeTab === 'mistakes' ? '答错的题目会自动收进错题本，并按所属系统归类，方便集中复习。' : '完成教师配置的结构刷题后，答错题目会自动保存到这里。' }}</p>
        <button class="button-primary" type="button" @click="startQuiz">开始空间定位测验 <ArrowRight :size="17" /></button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.archive-classroom { display: grid; gap: 12px; margin-top: 14px; padding: 17px; border: 1px solid #d8e6e3; border-radius: 10px; background: #fff; }
.classroom-summary { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto auto; align-items: center; gap: 12px; }
.classroom-icon { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 9px; background: #e5f3ef; color: #0f7068; }
.classroom-summary > div { display: grid; gap: 2px; min-width: 0; }
.classroom-summary small { color: #6d858a; font-size: 10px; }
.classroom-summary strong { color: #214c53; font-size: 16px; }
.classroom-summary p { margin: 0; color: #71878b; font-size: 11px; }
.classroom-summary select { min-height: 36px; padding: 0 9px; border: 1px solid #d4e1df; border-radius: 7px; background: #f9fcfb; color: #35565c; }
.classroom-join { display: grid; grid-template-columns: minmax(0,1fr) auto; align-items: end; gap: 10px; padding: 11px; border-radius: 8px; background: #f3f8f7; }
.classroom-join label { display: grid; gap: 5px; color: #49676d; font-size: 11px; font-weight: 700; }
.classroom-join input { min-height: 38px; padding: 0 11px; border: 1px solid #d1dfdd; border-radius: 7px; background: #fff; color: #294b52; font: inherit; text-transform: uppercase; }
.classroom-feedback { display: flex; align-items: center; gap: 6px; margin: 0; padding: 8px 10px; border-radius: 6px; font-size: 11px; }
.classroom-feedback.is-error { background: #fdeeec; color: #a44237; }
.classroom-feedback.is-ok { background: #e8f6ee; color: #1c7358; }
.student-guidance-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.student-guidance-list article { display: grid; gap: 6px; padding: 11px; border-left: 3px solid #1b8177; border-radius: 6px; background: #f6faf9; }
.student-guidance-list article.ai { border-left-color: #d08a30; background: #fff9f0; }
.student-guidance-list header { display: flex; justify-content: space-between; gap: 8px; }
.student-guidance-list header strong { color: #31575e; font-size: 11px; }
.student-guidance-list header span, .student-guidance-list small { color: #839497; font-size: 9px; }
.student-guidance-list :deep(.markdown-content) { max-height: 160px; margin: 0; overflow: auto; color: #506d72; font-size: 12px; line-height: 1.7; }
.student-guidance-list :deep(.markdown-content h1),
.student-guidance-list :deep(.markdown-content h2),
.student-guidance-list :deep(.markdown-content h3) { margin: 8px 0 4px; font-size: 13px; }
.student-guidance-list :deep(.markdown-content p) { margin: 4px 0; font-size: inherit; }
.student-guidance-list :deep(.markdown-content ul),
.student-guidance-list :deep(.markdown-content ol) { margin: 4px 0; padding-left: 16px; }
.archive-coverage { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.archive-coverage article { display: flex; align-items: center; gap: 10px; padding: 14px; border-radius: 8px; background: #eef6f4; color: var(--teal-dark); }
.archive-coverage span { display: grid; gap: 2px; }
.archive-coverage small { color: #6d8a8d; font-size: 11px; }
.archive-coverage strong { color: #21484e; font-size: 20px; }
.archive-tabs .archive-refresh { margin-left: auto; display: inline-flex; min-height: 40px; align-items: center; gap: 6px; padding: 0 12px; border: 1px solid #cbdada; border-radius: 7px; background: #fff; color: #4c6a70; cursor: pointer; }
.archive-state { display: flex; min-height: 180px; align-items: center; justify-content: center; gap: 9px; color: #607a80; }
.archive-state.is-error { color: #a24c43; }
.archive-scoreboard { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.archive-scoreboard article { padding: 14px; border: 1px solid #d9e6e4; border-radius: 8px; background: #f8fbfa; }
.archive-scoreboard small { display: block; margin-bottom: 5px; color: #698286; font-size: 11px; }
.archive-scoreboard strong { color: #174f4a; font-size: 26px; font-variant-numeric: tabular-nums; }
.archive-scoreboard span { margin-left: 4px; color: #728b8e; font-size: 11px; }
.archive-record-list, .archive-mistake-list { display: grid; gap: 10px; }
.archive-quiz-list { display: grid; gap: 10px; }
.archive-record-item, .archive-mistake-item, .archive-quiz-item { display: grid; gap: 10px; padding: 15px 16px; border: 1px solid #dce7e6; border-radius: 8px; background: #fff; }
.archive-record-item header, .archive-mistake-item header, .archive-quiz-item header, .archive-record-item footer, .archive-mistake-item footer, .archive-quiz-item footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.archive-record-item header span, .archive-mistake-item header span, .archive-quiz-item header span { color: #6a8287; font-size: 11px; }
.archive-record-item header b, .archive-mistake-item header b, .archive-quiz-item header b { padding: 3px 8px; border-radius: 999px; font-size: 10px; }
.archive-record-item header b.is-correct { background: #e5f4ef; color: #137162; }
.archive-record-item header b.is-wrong, .archive-mistake-item header b { background: #fae9e6; color: #a34d43; }
.archive-record-item h3, .archive-mistake-item h3, .archive-quiz-item h3 { margin: 0; color: #21484e; font-size: 15px; }
.archive-record-item p, .archive-mistake-item p, .archive-quiz-item p { margin: 5px 0 0; color: #526d72; font-size: 12px; line-height: 1.65; }
.archive-mistake-item small { color: #8a6c34; font-size: 11px; line-height: 1.55; }
.archive-record-item footer span, .archive-mistake-item footer span, .archive-quiz-item footer span { color: #84979a; font-size: 10px; }
.archive-record-item footer strong, .archive-mistake-item footer strong, .archive-quiz-item footer strong { color: #176b5d; font-size: 13px; }
.archive-quiz-item header b { background: #fae9e6; color: #a34d43; }
.quiz-answer-compare { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.quiz-answer-compare p { display: grid; gap: 3px; margin: 0; padding: 9px; border-radius: 6px; background: #f3f8f7; }
.quiz-answer-compare small { color: #789094; font-size: 9px; }
.quiz-answer-compare strong { color: #31575e; font-size: 11px; }
.quiz-missed-points { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; }
.quiz-missed-points small { color: #a4681c; font-size: 10px; font-weight: 800; }
.quiz-missed-points span { padding: 3px 6px; border-radius: 4px; background: #fff2df; color: #8a5e25; font-size: 10px; }
.archive-empty { display: grid; justify-items: center; gap: 8px; padding: 46px 24px; border-radius: 8px; background: #fbfdfd; box-shadow: 0 10px 30px rgba(23,63,72,.06); color: #6d8a8d; text-align: center; }
.archive-empty strong { color: #21484e; font-size: 16px; }
.archive-empty p { max-width: 520px; margin: 0; font-size: 13px; line-height: 1.65; }
.archive-empty button { margin-top: 6px; }
@media (max-width: 900px) {
  .archive-coverage, .archive-scoreboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .classroom-summary { grid-template-columns: 42px minmax(0,1fr); }
  .classroom-summary > button, .classroom-summary > select { grid-column: 2; justify-self: start; }
  .student-guidance-list { grid-template-columns: 1fr; }
  .archive-tabs { flex-wrap: wrap; }
  .archive-tabs .archive-refresh { margin-left: 0; }
}
@media (max-width: 620px) {
  .archive-coverage, .archive-scoreboard, .classroom-join, .quiz-answer-compare { grid-template-columns: 1fr; }
}
</style>
