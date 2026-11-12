<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ArrowRight, BarChart3, BookOpenCheck, Check, ChevronRight, ClipboardList, FileClock, GraduationCap, Layers3, LoaderCircle, Plus, RefreshCw, Search, Sparkles, Target, TriangleAlert, Users } from '@lucide/vue';
import {
  createClassroom,
  generateAiClassroomGuidance,
  getClassroomDetail,
  getClassroomGuidance,
  getMyClassrooms,
  sendClassroomGuidance
} from '../api';
import MarkdownContent from '../components/MarkdownContent.vue';
import type { ClassroomDetail, ClassroomGuidance, ClassroomStudent, ClassroomSummary } from '../types';

const classSearch = ref('');
const studentSection = ref<HTMLElement | null>(null);
const guidanceSection = ref<HTMLElement | null>(null);
let detailRequest = 0;
let guidanceRequest = 0;
const classrooms = ref<ClassroomSummary[]>([]);
const activeClassId = ref('');
const detail = ref<ClassroomDetail | null>(null);
const selectedStudentId = ref('');
const guidance = ref<ClassroomGuidance[]>([]);
const loadingClasses = ref(true);
const loadingDetail = ref(false);
const loadingGuidance = ref(false);
const creating = ref(false);
const sending = ref(false);
const aiLoading = ref(false);
const error = ref('');
const message = ref('');
const codeCopied = ref(false);
const showCreate = ref(false);
const createForm = ref({ name: '', description: '' });
const guidanceForm = ref({ content: '', recommendedScore: null as number | null });

const selectedStudent = computed<ClassroomStudent | null>(() =>
  detail.value?.students.find((item) => item.student_id === selectedStudentId.value) ?? null
);
const latestGuidance = computed(() => guidance.value[0] ?? null);
const earlierGuidance = computed(() => guidance.value.slice(1, 11));

const filteredClasses = computed(() => classrooms.value.filter(item => item.name.toLocaleLowerCase().includes(classSearch.value.trim().toLocaleLowerCase())));
const classStats = computed(() => {
  const students = detail.value?.students ?? [];
  const practiced = students.filter(student => student.total_attempts > 0).length;
  const attempts = students.reduce((sum, student) => sum + student.total_attempts, 0);
  const correct = students.reduce((sum, student) => sum + student.anatomy.correct + student.quiz.correct, 0);
  return { count: students.length, practiced, pending: students.length - practiced, attempts,
    accuracy: attempts ? Math.round(correct / attempts * 100) : null,
    average: practiced ? Math.round(students.reduce((sum, student) => sum + (student.total_attempts ? student.average_score : 0), 0) / practiced) : null };
});
const practicedShare = computed(() => classStats.value.count ? classStats.value.practiced / classStats.value.count * 100 : 0);
const needsReview = computed(() => (detail.value?.students ?? []).filter(student => student.weak_points.length));
const practiceCounts = computed(() => [
  { label: '空间定位', count: (detail.value?.students ?? []).reduce((sum, student) => sum + student.anatomy.total, 0) },
  { label: '结构刷题', count: (detail.value?.students ?? []).reduce((sum, student) => sum + student.quiz.total, 0) }
]);
const practiceMaximum = computed(() => Math.max(1, ...practiceCounts.value.map(item => item.count)));
const recentEvents = computed(() => [
  ...(detail.value?.students ?? []).map(student => ({ id: student.student_id, text: student.student_name + ' 加入班级', time: student.joined_at })),
  ...guidance.value.map(item => ({ id: item.id, text: item.source === 'ai' ? '已生成 AI 学习建议 · ' + (selectedStudent.value?.student_name ?? '') : '已发送教师指导 · ' + (selectedStudent.value?.student_name ?? ''), time: item.created_at }))
].filter(item => Number.isFinite(Date.parse(item.time))).sort((a, b) => Date.parse(b.time) - Date.parse(a.time)).slice(0, 4));

function formatTime(value: string) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN');
}

async function loadClasses(preferredId = '') {
  loadingClasses.value = true;
  error.value = '';
  try {
    classrooms.value = (await getMyClassrooms()).items;
    const preferred = preferredId || activeClassId.value;
    const nextId = classrooms.value.find(item => item.id === preferred)?.id || classrooms.value[0]?.id || '';
    if (nextId) await selectClass(nextId);
    else {
      activeClassId.value = '';
      detail.value = null;
      selectedStudentId.value = '';
      guidance.value = [];
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '班级数据暂时无法读取';
  } finally {
    loadingClasses.value = false;
  }
}

async function selectClass(classId: string) {
  const request = ++detailRequest;
  ++guidanceRequest;
  activeClassId.value = classId;
  detail.value = null;
  selectedStudentId.value = '';
  guidance.value = [];
  guidanceForm.value = { content: '', recommendedScore: null };
  loadingGuidance.value = false;
  loadingDetail.value = true;
  error.value = '';
  try {
    const loaded = await getClassroomDetail(classId);
    if (request !== detailRequest) return;
    detail.value = loaded;
    const nextStudentId = loaded.students[0]?.student_id ?? '';
    selectedStudentId.value = nextStudentId;
    if (nextStudentId) await loadGuidance(nextStudentId);
  } catch (reason) {
    if (request === detailRequest) error.value = reason instanceof Error ? reason.message : '班级详情读取失败';
  } finally {
    if (request === detailRequest) loadingDetail.value = false;
  }
}

async function loadGuidance(studentId: string) {
  const classId = activeClassId.value;
  if (!classId || !studentId) return;
  const request = ++guidanceRequest;
  loadingGuidance.value = true;
  guidance.value = [];
  try {
    const result = await getClassroomGuidance(classId, studentId);
    if (request === guidanceRequest) guidance.value = result.items;
  } catch {
    if (request === guidanceRequest) {
      guidance.value = [];
      error.value = '指导记录读取失败，请重新选择学生重试。';
    }
  } finally {
    if (request === guidanceRequest) loadingGuidance.value = false;
  }
}

function selectStudent(studentId: string) {
  selectedStudentId.value = studentId;
  guidanceForm.value = { content: '', recommendedScore: null };
  void loadGuidance(studentId);
}

async function createClass() {
  if (createForm.value.name.trim().length < 2 || creating.value) return;
  creating.value = true;
  error.value = '';
  try {
    const created = await createClassroom({
      name: createForm.value.name.trim(),
      description: createForm.value.description.trim()
    });
    createForm.value = { name: '', description: '' };
    showCreate.value = false;
    message.value = `班级“${created.name}”已创建，班级码 ${created.code}`;
    await loadClasses(created.id);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '班级创建失败';
  } finally {
    creating.value = false;
  }
}

async function copyCode() {
  if (!detail.value?.code) return;
  try {
    await navigator.clipboard.writeText(detail.value.code);
    codeCopied.value = true;
    window.setTimeout(() => { codeCopied.value = false; }, 1500);
  } catch {
    error.value = '浏览器未允许复制班级码，请手动记录。';
  }
}

async function sendGuidance() {
  const student = selectedStudent.value;
  const content = guidanceForm.value.content.trim();
  if (!student || !content || sending.value) return;
  const classId = activeClassId.value;
  sending.value = true;
  error.value = '';
  try {
    const created = await sendClassroomGuidance(classId, {
      student_id: student.student_id,
      content,
      recommended_score: guidanceForm.value.recommendedScore
    });
    if (activeClassId.value !== classId || selectedStudentId.value !== student.student_id) return;
    guidance.value = [created, ...guidance.value.filter(item => item.id !== created.id)];
    guidanceForm.value = { content: '', recommendedScore: null };
    message.value = `已向${student.student_name}发送学习指导。`;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '指导发送失败';
  } finally {
    sending.value = false;
  }
}

async function generateAiGuidance() {
  const student = selectedStudent.value;
  if (!student || aiLoading.value) return;
  const classId = activeClassId.value;
  aiLoading.value = true;
  error.value = '';
  try {
    const created = await generateAiClassroomGuidance(classId, student.student_id);
    guidance.value = [created, ...guidance.value.filter(item => item.id !== created.id)];
    if (detail.value) {
      detail.value.students = detail.value.students.map((item) =>
        item.student_id === student.student_id
          ? { ...item, ...(created.performance as unknown as ClassroomStudent) }
          : item
      );
    }
    message.value = `已为${student.student_name}生成AI学习建议。`;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'AI指导生成失败';
  } finally {
    aiLoading.value = false;
  }
}

onMounted(() => { void loadClasses(); });
</script>

<template>
  <div class="workspace-page classroom-page class-management">
    <section class="class-banner">
      <span>教师工作台 <ChevronRight :size="13" />班级管理</span>
      <h1>班级管理</h1>
      <p>管理教学班级，掌握学生作答表现，发送学习指导与复习建议。</p>
    </section>
    <section class="class-top-metrics" aria-label="班级统计">
      <article><Users /><div><small>班级总数</small><strong>{{ loadingClasses ? '—' : classrooms.length }}</strong></div></article>
      <article><GraduationCap /><div><small>班级成员人次</small><strong>{{ loadingClasses ? '—' : classrooms.reduce((sum, item) => sum + item.student_count, 0) }}</strong></div></article>
      <article><ClipboardList /><div><small>当前班级累计作答</small><strong>{{ detail ? classStats.attempts : '—' }}</strong></div></article>
      <article><Target /><div><small>当前班级正确率</small><strong>{{ classStats.accuracy == null ? '—' : classStats.accuracy + '%' }}</strong></div></article>
      <article><BarChart3 /><div><small>已作答学生均分</small><strong>{{ classStats.average == null ? '—' : classStats.average }}</strong></div></article>
    </section>
    <section v-if="showCreate" class="classroom-create">
      <label><span>班级名称</span><input v-model="createForm.name" maxlength="60" placeholder="例如：临床医学 2026-1 班" /></label>
      <label><span>班级说明</span><input v-model="createForm.description" maxlength="500" placeholder="课程、学期或教学范围" /></label>
      <button class="button-primary" type="button" :disabled="creating || createForm.name.trim().length < 2" @click="createClass">
        <LoaderCircle v-if="creating" class="spin" :size="16" /><Plus v-else :size="16" />{{ creating ? '创建中' : '确认创建' }}
      </button>
    </section>

    <p v-if="error" class="classroom-banner is-error" role="alert"><TriangleAlert :size="16" />{{ error }}</p>
    <p v-else-if="message" class="classroom-banner is-ok" role="status"><Check :size="16" />{{ message }}</p>

    <div class="classroom-layout">
      <aside class="class-list-panel">
        <header><h2>班级列表</h2><button class="button-primary" type="button" :aria-expanded="showCreate" @click="showCreate = !showCreate"><Plus :size="15" />创建班级</button></header>
        <label class="class-search"><Search :size="16" /><input v-model="classSearch" aria-label="搜索班级名称" placeholder="搜索班级名称" /></label>
        <div class="class-list-items">
          <button v-for="item in filteredClasses" :key="item.id" type="button" :class="{ active: item.id === activeClassId }" :aria-pressed="item.id === activeClassId" @click="selectClass(item.id)">
            <GraduationCap :size="20" /><strong>{{ item.name }}</strong><small>{{ item.student_count }} 人</small><ChevronRight :size="15" />
          </button>
          <p v-if="loadingClasses" class="class-quiet" role="status">正在读取班级…</p>
          <p v-else-if="!filteredClasses.length" class="class-quiet">{{ classrooms.length ? '没有匹配的班级' : error ? '班级列表暂时无法读取' : '尚未创建班级' }}</p>
        </div>
        <button class="class-refresh" type="button" :disabled="loadingClasses" @click="loadClasses()"><RefreshCw :size="14" />刷新班级</button>
      </aside>

      <main class="classroom-detail">
        <nav class="class-quick-panel" aria-label="快捷功能">
          <h2>快捷功能</h2>
          <div>
            <button type="button" :disabled="!detail" @click="studentSection?.scrollIntoView({ block: 'start' })"><Users />学生学情</button>
            <button type="button" :disabled="!selectedStudent" @click="guidanceSection?.scrollIntoView({ block: 'start' })"><BookOpenCheck />教师指导</button>
            <button type="button" :disabled="!selectedStudent || aiLoading" @click="generateAiGuidance"><Sparkles />AI 学习建议</button>
            <RouterLink to="/teacher/exam-settings"><ClipboardList />题型与测验</RouterLink>
            <RouterLink to="/teacher/knowledge"><Layers3 />教学资料</RouterLink>
            <button type="button" :disabled="!detail" @click="copyCode"><Check />复制班级码</button>
          </div>
        </nav>

        <div v-if="loadingClasses || loadingDetail" class="classroom-state class-card" role="status"><LoaderCircle class="spin" :size="22" />正在读取班级与学情</div>
        <section v-else-if="!detail" class="classroom-empty class-card">
          <Users :size="28" />
          <strong>{{ error ? '班级数据暂不可用' : '还没有班级' }}</strong>
          <p>{{ error ? '请刷新班级列表后重试。' : '点击创建班级，生成班级码后邀请学生加入。这里会展示真实学情、练习分布和指导记录。' }}</p>
          <button v-if="!error" class="button-primary" type="button" @click="showCreate = true"><Plus :size="16" />创建第一个班级</button>
          <button v-else class="button-secondary" type="button" @click="loadClasses()"><RefreshCw :size="16" />重新读取</button>
        </section>

        <header v-if="detail" class="classroom-detail-head">
          <div><span>{{ detail.teacher_name }}</span><h2>{{ detail.name }}</h2><p>{{ detail.description || '暂无班级说明' }}</p></div>
          <button type="button" class="class-code" @click="copyCode"><small>班级码</small><strong>{{ detail.code }}</strong><span>{{ codeCopied ? '已复制' : '点击复制' }}</span></button>
        </header>

        <div class="class-overview-grid">
          <section class="class-card">
            <header><h2>班级概览</h2><small>{{ detail?.name || '创建班级后查看' }}</small></header>
            <div class="class-participation">
              <div class="class-donut" :style="{ background: 'conic-gradient(#2476ff ' + practicedShare + '%, #dce7fb 0)' }"><strong>{{ detail ? classStats.count : '—' }}</strong><small>班级人数</small></div>
              <dl><div><dt>已作答学生</dt><dd>{{ detail ? classStats.practiced : '—' }} 人</dd></div><div><dt>尚未作答</dt><dd>{{ detail ? classStats.pending : '—' }} 人</dd></div></dl>
            </div>
          </section>
          <section class="class-card">
            <header><h2>班级练习分布</h2><small>累计作答次数</small></header>
            <div class="class-practice-bars">
              <div v-for="item in practiceCounts" :key="item.label"><span>{{ item.label }}</span><i><b :style="{ width: item.count / practiceMaximum * 100 + '%' }"></b></i><strong>{{ detail ? item.count : '—' }}</strong></div>
            </div>
          </section>
          <section class="class-card class-recent">
            <header><h2><FileClock :size="18" />近期动态</h2></header>
            <ul v-if="recentEvents.length"><li v-for="item in recentEvents" :key="item.id"><span>{{ item.text }}</span><time :datetime="item.time">{{ formatTime(item.time) }}</time></li></ul>
            <p v-else class="class-quiet">暂无入班和指导记录。</p>
            <small>显示学生入班及当前学生的指导记录。</small>
          </section>
          <section class="class-card class-review">
            <header><h2><Target :size="18" />复习关注</h2><small>{{ detail ? needsReview.length : '—' }} 名学生</small></header>
            <button v-for="student in needsReview.slice(0, 3)" :key="student.student_id" type="button" @click="selectStudent(student.student_id); guidanceSection?.scrollIntoView({ block: 'start' })"><span><strong>{{ student.student_name }}</strong><small>{{ student.weak_points.slice(0, 2).join('、') }}</small></span><ChevronRight :size="15" /></button>
            <p v-if="!needsReview.length" class="class-quiet">{{ classStats.attempts ? '当前暂无明确薄弱项。' : '完成作答后可在这里查看复习关注项。' }}</p>
          </section>
        </div>
        <section v-if="detail" ref="studentSection" class="class-students-panel">
          <header><h2><Users :size="18" />学生学情</h2><small>{{ detail.students.length }} 名学生</small></header>
          <div class="student-grid">

          <button v-for="student in detail.students" :key="student.student_id" type="button" :class="{ active: student.student_id === selectedStudentId }" @click="selectStudent(student.student_id)">
            <header><strong>{{ student.student_name }}</strong><span>{{ student.average_score }} 分</span></header>
            <p>{{ student.total_attempts }} 次作答 · 定位 {{ student.anatomy.total }} · 刷题 {{ student.quiz.total }}</p>
            <small>{{ student.weak_points.length ? `重点：${student.weak_points.slice(0, 2).join('、')}` : '暂无明确薄弱项' }}</small>
          </button>
          <div v-if="!detail.students.length" class="classroom-empty compact"><Users :size="24" /><strong>暂时没有学生加入</strong><p>把班级码 {{ detail.code }} 发给学生即可。</p></div>
          </div>
        </section>

        <section v-if="selectedStudent" ref="guidanceSection" class="student-guidance">
          <header>
            <div><span>学生指导</span><h3>{{ selectedStudent.student_name }}</h3></div>
            <button class="button-secondary" type="button" :disabled="aiLoading" @click="generateAiGuidance">
              <LoaderCircle v-if="aiLoading" class="spin" :size="16" /><Sparkles v-else :size="16" />{{ aiLoading ? '生成中' : 'AI生成建议' }}
            </button>
          </header>

          <div class="student-performance">
            <article><small>综合得分</small><strong>{{ selectedStudent.average_score }}</strong></article>
            <article><small>定位正确率</small><strong>{{ Math.round(selectedStudent.anatomy.accuracy * 10) / 10 }}%</strong></article>
            <article><small>刷题正确率</small><strong>{{ Math.round(selectedStudent.quiz.accuracy * 10) / 10 }}%</strong></article>
          </div>

          <div class="guidance-grid">
            <div class="guidance-form">
              <label><span>建议目标分</span><input v-model.number="guidanceForm.recommendedScore" type="number" min="0" max="100" placeholder="可选" /></label>
              <label><span>教师指导</span><textarea v-model="guidanceForm.content" rows="4" placeholder="指出优先复习结构、下一次训练目标或课堂观察。" /></label>
              <button class="button-primary" type="button" :disabled="sending || !guidanceForm.content.trim()" @click="sendGuidance">
                <LoaderCircle v-if="sending" class="spin" :size="16" /><BookOpenCheck v-else :size="16" />{{ sending ? '发送中' : '发送给学生' }}
              </button>
            </div>

            <div class="guidance-workspace">
              <div v-if="loadingGuidance" class="classroom-state compact"><LoaderCircle class="spin" :size="18" />读取指导记录</div>
              <article v-else-if="latestGuidance" class="guidance-latest" :class="{ ai: latestGuidance.source === 'ai' }">
                <header>
                  <span class="guidance-source"><Sparkles v-if="latestGuidance.source === 'ai'" :size="16" /><BookOpenCheck v-else :size="16" />{{ latestGuidance.author_name }}</span>
                  <time>{{ formatTime(latestGuidance.created_at) }}</time>
                </header>
                <MarkdownContent :content="latestGuidance.content" />
                <footer v-if="latestGuidance.recommended_score !== null && latestGuidance.recommended_score !== undefined">
                  <small>建议目标</small><strong>{{ latestGuidance.recommended_score }} 分</strong>
                </footer>
              </article>
              <div v-else class="classroom-empty compact"><BookOpenCheck :size="22" /><strong>还没有指导记录</strong><p>发送教师指导，或让 AI 学习教练生成首条建议。</p></div>
            </div>
          </div>

          <details v-if="earlierGuidance.length" class="guidance-history-details">
            <summary>
              <span><FileClock :size="16" />历史指导记录</span>
              <b>{{ earlierGuidance.length }} 条</b>
            </summary>
            <div class="guidance-history">
              <article v-for="item in earlierGuidance" :key="item.id" :class="{ ai: item.source === 'ai' }">
                <header><strong>{{ item.author_name }}</strong><span>{{ formatTime(item.created_at) }}</span></header>
                <MarkdownContent :content="item.content" />
                <small v-if="item.recommended_score !== null && item.recommended_score !== undefined">建议目标：{{ item.recommended_score }} 分</small>
              </article>
            </div>
          </details>
        </section>
      </main>
    </div>
  </div>
</template>

<style scoped>
.classroom-page { display: grid; gap: 16px; }
.classroom-hero { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px 24px; border-radius: 10px; background: #eef6f4; }
.classroom-hero h1 { margin: 4px 0 6px; color: #16414a; font-size: 1.7rem; }
.classroom-hero p { max-width: 720px; margin: 0; color: #5d767b; font-size: 13px; line-height: 1.65; }
.classroom-create { display: grid; grid-template-columns: 1fr 1.5fr auto; align-items: end; gap: 12px; padding: 16px; border: 1px solid #dbe6e4; border-radius: 9px; background: #fff; }
.classroom-create label, .guidance-form label { display: grid; gap: 6px; color: #49666c; font-size: 12px; font-weight: 700; }
.classroom-create input, .guidance-form input, .guidance-form textarea { width: 100%; border: 1px solid #d5e1df; border-radius: 7px; background: #fbfdfd; color: #294b52; font: inherit; }
.classroom-create input, .guidance-form input { min-height: 40px; padding: 0 11px; }
.guidance-form textarea { padding: 10px 11px; line-height: 1.6; resize: vertical; }
.classroom-banner { display: flex; align-items: center; gap: 7px; margin: 0; padding: 10px 12px; border-radius: 7px; font-size: 12px; }
.classroom-banner.is-error { background: #fdeeec; color: #a44237; }
.classroom-banner.is-ok { background: #e8f6ee; color: #1c7358; }
.classroom-state { display: flex; min-height: 180px; align-items: center; justify-content: center; gap: 8px; color: #637d82; }
.classroom-state.compact { min-height: 60px; font-size: 12px; }
.classroom-empty { display: grid; justify-items: center; gap: 8px; padding: 44px 24px; border-radius: 9px; background: #fbfdfd; color: #71898d; text-align: center; }
.classroom-empty.compact { padding: 22px; }
.classroom-empty strong { color: #31585f; }
.classroom-empty p { max-width: 520px; margin: 0; font-size: 12px; line-height: 1.6; }
.classroom-layout { display: grid; grid-template-columns: 270px minmax(0, 1fr); gap: 16px; min-height: 520px; }
.classroom-list { display: flex; max-height: 760px; overflow-y: auto; flex-direction: column; gap: 7px; padding: 10px; border: 1px solid #dbe6e4; border-radius: 9px; background: #f5f9f8; }
.classroom-list button { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 11px; border: 1px solid transparent; border-radius: 7px; background: #fff; color: #3f5e64; text-align: left; cursor: pointer; }
.classroom-list button.active { border-color: rgba(15,118,110,.38); background: #e4f2ef; }
.classroom-list button span { display: grid; gap: 2px; min-width: 0; }
.classroom-list button strong { overflow: hidden; color: #294f56; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.classroom-list button small { color: #7e9295; font-size: 10px; }
.classroom-list button b { padding: 3px 6px; border-radius: 4px; background: #edf5f3; color: #176c63; font-size: 10px; letter-spacing: .05em; }
.classroom-detail { display: grid; align-content: start; gap: 14px; min-width: 0; }
.classroom-detail-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 18px; border: 1px solid #dbe6e4; border-radius: 9px; background: #fff; }
.classroom-detail-head span { color: #188077; font-size: 11px; font-weight: 800; }
.classroom-detail-head h2 { margin: 3px 0 5px; color: #21484e; font-size: 20px; }
.classroom-detail-head p { margin: 0; color: #71878b; font-size: 12px; }
.class-code { display: grid; justify-items: end; gap: 2px; padding: 9px 12px; border: 1px solid rgba(15,118,110,.22); border-radius: 7px; background: #edf7f4; cursor: pointer; }
.class-code small, .class-code span { color: #6e8a8d; font-size: 9px; }
.class-code strong { color: #075f59; font-size: 18px; letter-spacing: .12em; }
.classroom-metrics, .student-performance { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.classroom-metrics article, .student-performance article { display: grid; gap: 3px; padding: 13px; border: 1px solid #dce7e5; border-radius: 8px; background: #f8fbfa; }
.classroom-metrics small, .student-performance small { color: #71898d; font-size: 10px; }
.classroom-metrics strong, .student-performance strong { color: #174f4a; font-size: 24px; }
.student-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.student-grid > button { display: grid; gap: 7px; padding: 13px; border: 1px solid #dce7e5; border-radius: 8px; background: #fff; color: #4a676d; text-align: left; cursor: pointer; }
.student-grid > button.active { border-color: rgba(15,118,110,.45); background: #eef7f5; }
.student-grid header { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.student-grid header strong { color: #294f56; font-size: 14px; }
.student-grid header span { color: #168073; font-size: 15px; font-weight: 800; }
.student-grid p, .student-grid small { margin: 0; font-size: 11px; line-height: 1.5; }
.student-grid small { color: #8b6d32; }
.student-guidance { display: grid; gap: 12px; padding: 16px; border: 1px solid #dbe6e4; border-radius: 9px; background: #fff; }
.student-guidance > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.student-guidance > header span { color: #188077; font-size: 10px; font-weight: 800; }
.student-guidance h3 { margin: 2px 0 0; color: #21484e; font-size: 17px; }
.guidance-grid { display: grid; grid-template-columns: minmax(300px, .82fr) minmax(0, 1.18fr); align-items: start; gap: 14px; }
.guidance-form { display: grid; grid-template-columns: 1fr; align-items: stretch; gap: 12px; padding: 14px; border: 1px solid #dbe6f4; border-radius: 9px; background: #f7faff; }
.guidance-form .button-primary { justify-self: start; }
.guidance-workspace { min-width: 0; }
.guidance-latest { display: grid; gap: 10px; max-height: 470px; overflow: auto; padding: 16px; border: 1px solid #cfdcf0; border-left: 4px solid #0b46df; border-radius: 9px; background: #f7faff; }
.guidance-latest.ai { border-left-color: #0b46df; background: #f1f6ff; }
.guidance-latest > header { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding-bottom: 9px; border-bottom: 1px solid #dce5f2; }
.guidance-latest .guidance-source { display: inline-flex; align-items: center; gap: 7px; color: #0b46df; font-size: 12px; font-weight: 900; }
.guidance-latest time { color: #7887a2; font-size: 10px; }
.guidance-latest footer { display: flex; align-items: baseline; justify-content: flex-end; gap: 7px; padding-top: 9px; border-top: 1px solid #dce5f2; }
.guidance-latest footer small { color: #71809b; font-size: 10px; }
.guidance-latest footer strong { color: #0b46df; font-size: 17px; }
.guidance-latest :deep(.markdown-content) { margin: 0; color: #42536f; font-size: 13px; line-height: 1.65; }
.guidance-latest :deep(.markdown-content h1),
.guidance-latest :deep(.markdown-content h2),
.guidance-latest :deep(.markdown-content h3) { margin: 11px 0 5px; color: #17336b; font-size: 14px; }
.guidance-latest :deep(.markdown-content h1:first-child),
.guidance-latest :deep(.markdown-content h2:first-child),
.guidance-latest :deep(.markdown-content h3:first-child),
.guidance-latest :deep(.markdown-content p:first-child) { margin-top: 0; }
.guidance-latest :deep(.markdown-content p) { margin: 5px 0; font-size: inherit; }
.guidance-latest :deep(.markdown-content ul),
.guidance-latest :deep(.markdown-content ol) { margin: 5px 0; padding-left: 19px; }
.guidance-history-details { border: 1px solid #dbe6f4; border-radius: 9px; background: #fff; }
.guidance-history-details summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 46px; padding: 0 14px; color: #31466f; cursor: pointer; list-style: none; }
.guidance-history-details summary::-webkit-details-marker { display: none; }
.guidance-history-details summary span { display: inline-flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 900; }
.guidance-history-details summary b { padding: 3px 8px; border-radius: 999px; background: #edf3ff; color: #0b46df; font-size: 10px; }
.guidance-history-details[open] summary { border-bottom: 1px solid #dce5f2; }
.guidance-history-details .guidance-history { max-height: 520px; overflow: auto; padding: 12px; }
.guidance-history { display: grid; gap: 8px; }
.guidance-history article { display: grid; gap: 6px; padding: 12px; border-left: 3px solid #0b46df; border-radius: 6px; background: #f7faff; }
.guidance-history article.ai { border-left-color: #0b46df; background: #f1f6ff; }
.guidance-history header { display: flex; justify-content: space-between; gap: 10px; }
.guidance-history header strong { color: #31575e; font-size: 12px; }
.guidance-history header span, .guidance-history small { color: #839497; font-size: 10px; }
.guidance-history :deep(.markdown-content) { margin: 0; color: #506d72; font-size: 13px; line-height: 1.72; }
.guidance-history :deep(.markdown-content h1),
.guidance-history :deep(.markdown-content h2),
.guidance-history :deep(.markdown-content h3) { margin: 8px 0 4px; font-size: 14px; }
.guidance-history :deep(.markdown-content p) { margin: 4px 0; font-size: inherit; }
.guidance-history :deep(.markdown-content ul),
.guidance-history :deep(.markdown-content ol) { margin: 4px 0; padding-left: 18px; }
@media (max-width: 980px) {
  .classroom-layout { grid-template-columns: 1fr; }
  .classroom-list { max-height: 220px; }
  .classroom-create, .guidance-grid { grid-template-columns: 1fr; }
}
@media (max-width: 680px) {
  .classroom-hero, .classroom-detail-head { align-items: stretch; flex-direction: column; }
  .class-code { justify-items: start; }
  .classroom-metrics, .student-performance, .student-grid { grid-template-columns: 1fr; }
}

.class-management { gap: 12px; color: #10234e; }
.class-banner { padding: 17px 27px; min-height: 132px; border: 1px solid #f5faff; border-radius: 17px; background: linear-gradient(90deg, #dcecff, #d8e8ff00 80%), #cbdffa url('../assets/medical/teacher-overview-banner.webp') right center / auto 100% no-repeat; }
.class-banner > span { display: flex; align-items: center; gap: 5px; color: #155bdc; font-size: 12px; font-weight: 750; }
.class-banner h1 { margin: 6px 0; font-size: 31px; line-height: 1.2; }
.class-banner p { max-width: 70%; margin: 0; color: #405a80; font-size: 13px; line-height: 1.6; }
.class-top-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.class-top-metrics article, .class-list-panel, .class-card, .class-quick-panel, .class-students-panel {
  min-width: 0; border: 1px solid #fff; border-radius: 15px; background: linear-gradient(145deg, #fcfdff, #eef5ff); box-shadow: 0 4px 13px #153b7e13;
}
.class-top-metrics article { display: flex; align-items: center; gap: 13px; padding: 14px; }
.class-top-metrics article > svg { width: 42px; height: 42px; flex: 0 0 auto; padding: 9px; border-radius: 50%; background: #e1edff; color: #1566fa; }
.class-top-metrics article > div { display: grid; gap: 4px; }
.class-top-metrics small { color: #415b80; font-size: 11px; }
.class-top-metrics strong { font-size: 25px; color: #0c50eb; line-height: 1.1; }
.class-management .classroom-layout { grid-template-columns: minmax(230px, .85fr) minmax(0, 2.65fr); gap: 12px; }
.class-list-panel { display: flex; flex-direction: column; gap: 12px; padding: 13px; align-self: start; min-height: 550px; }
.class-list-panel header, .class-card header, .class-students-panel > header { display: flex; align-items: center; justify-content: space-between; gap: 7px; }
.class-management h2 { margin: 0; color: #10234e; font-size: 17px; }
.class-list-panel .button-primary { min-height: 31px; padding: 0 8px; font-size: 11px; }
.class-search { display: flex; align-items: center; gap: 6px; padding: 0 9px; border: 1px solid #cdddF5; border-radius: 9px; background: #f9fbff; color: #607fa9; }
.class-search input { width: 100%; min-width: 0; min-height: 34px; border: 0; background: transparent; color: #294771; font-size: 12px; }
.class-list-items { display: grid; align-content: start; gap: 6px; max-height: 580px; overflow: auto; }
.class-list-items > button { display: grid; grid-template-columns: auto minmax(0,1fr) auto auto; align-items: center; gap: 7px; min-height: 49px; padding: 7px; border: 1px solid #e0eafa; border-radius: 9px; background: #f4f8ff; color: #36577f; text-align: left; }
.class-list-items > button.active { border-color: #82aaff; background: #dfebff; }
.class-list-items > button strong { overflow: hidden; color: #17325a; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.class-list-items > button svg { color: #1e64f0; }
.class-list-items > button small { font-size: 11px; white-space: nowrap; }
.class-refresh { display: inline-flex; align-items: center; gap: 6px; justify-content: center; margin-top: auto; padding: 7px; border: 0; background: #e7f0ff; color: #26578f; border-radius: 8px; font-size: 12px; }
.class-management .classroom-detail { gap: 10px; }
.class-quick-panel { padding: 13px; }
.class-quick-panel h2 { margin-bottom: 10px; }
.class-quick-panel > div { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 7px; }
.class-quick-panel :is(button, a) { display: grid; min-width: 0; justify-items: center; place-content: center; gap: 7px; min-height: 66px; padding: 5px; border: 0; border-radius: 9px; background: #e5eeff; color: #193b76; text-decoration: none; font-size: 11px; }
.class-quick-panel :is(button, a) svg { width: 23px; height: 23px; color: #1c68fa; }
.class-quick-panel :is(button, a):hover:not(:disabled) { background: #d9e8ff; }
.class-management .classroom-detail-head { padding: 12px; border-color: #fff; border-radius: 13px; background: #f4f8ff; }
.class-management .classroom-detail-head h2 { margin: 2px 0; }
.class-management .classroom-detail-head p { color: #516b8f; }
.class-management .class-code { background: #e4efff; border-color: #cedfff; }
.class-management .class-code strong { color: #1353d4; font-size: 16px; }
.class-overview-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; }
.class-card { padding: 13px; }
.class-card header small { color: #577193; font-size: 11px; }
.class-card header h2, .class-students-panel > header h2 { display: flex; align-items: center; gap: 6px; }
.class-card header h2 svg, .class-students-panel h2 svg { color: #236af0; }
.class-participation { display: flex; align-items: center; justify-content: space-around; gap: 12px; min-height: 137px; padding-top: 10px; }
.class-donut { position: relative; isolation: isolate; display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 0 0 auto; width: 113px; aspect-ratio: 1; border-radius: 50%; }
.class-donut::before { position: absolute; z-index: -1; inset: 18%; border-radius: inherit; background: #f4f9ff; content: ''; }
.class-donut strong { font-size: 27px; }
.class-donut small { color: #3d5e8c; font-size: 11px; }
.class-participation dl { display: grid; gap: 13px; font-size: 12px; }
.class-participation dl > div { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.class-participation dd { margin: 0; font-weight: 750; white-space: nowrap; }
.class-participation dt::before { display: inline-block; width: 8px; height: 8px; margin-right: 5px; border-radius: 50%; background: #2476ff; content: ''; }
.class-participation dl > div:last-child dt::before { background: #c6d7f3; }
.class-practice-bars { display: grid; align-content: center; gap: 22px; min-height: 137px; }
.class-practice-bars > div { display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: 8px; font-size: 12px; }
.class-practice-bars i { height: 10px; border-radius: 99px; background: #dfeafb; overflow: hidden; }
.class-practice-bars b { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #56a6ff, #276af4); }
.class-recent ul { margin: 8px 0; padding: 0; list-style: none; }
.class-recent li { display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 7px; padding: 9px 0; border-bottom: 1px solid #e1eafa; color: #355378; font-size: 11px; }
.class-recent time { font-size: 10px; color: #647a9c; }
.class-recent > small { font-size: 10px; color: #5a7193; }
.class-review > button { display: flex; width: 100%; justify-content: space-between; align-items: center; gap: 6px; padding: 9px 0; border: 0; border-bottom: 1px solid #e0eafa; background: transparent; color: #27527f; text-align: left; }
.class-review > button span { display: grid; gap: 4px; min-width: 0; }
.class-review > button small { color: #617591; overflow-wrap: anywhere; }
.class-quiet { color: #59718f; font-size: 12px; line-height: 1.7; }
.class-students-panel { padding: 13px; scroll-margin-top: 85px; }
.class-students-panel > header { margin-bottom: 10px; }
.class-students-panel > header small { color: #59718f; font-size: 11px; }
.class-management .student-grid > button.active { border-color: #8eb8ff; background: #e9f2ff; }
.class-management .student-grid header strong { color: #173760; }
.class-management .student-guidance { scroll-margin-top: 85px; border-color: #fff; border-radius: 14px; background: #f5f9ff; }
.class-management .student-performance strong { color: #1756c9; }
.class-management .student-performance article { min-width: 0; }
.class-management .student-performance strong { font-size: clamp(18px, 2vw, 24px); overflow-wrap: anywhere; }
.class-management .class-review > button strong { font-size: 13px; }
.class-management .class-review > button small { font-size: 11px; }
.class-management .guidance-grid { grid-template-columns: minmax(0,1fr) minmax(0,1.2fr); }
.class-management .classroom-create { border-color: #d8e7ff; border-radius: 12px; background: #f8fbff; }
@media (max-width: 1100px) {
  .class-top-metrics { grid-template-columns: repeat(3,minmax(0,1fr)); }
  .class-management .classroom-layout { grid-template-columns: minmax(200px,.8fr) minmax(0,2.2fr); }
  .class-overview-grid { grid-template-columns: minmax(0,1fr); }
  .class-quick-panel > div { grid-template-columns: repeat(3,minmax(0,1fr)); }
  .class-management .guidance-grid { grid-template-columns: minmax(0,1fr); }
}
@media (max-width: 760px) {
  .class-management .classroom-layout { grid-template-columns: minmax(0,1fr); }
  .class-list-panel { min-height: 0; }
  .class-list-items { max-height: 200px; }
  .class-banner { padding: 17px; }
  .class-banner p { max-width: 80%; }
  .class-top-metrics { grid-template-columns: repeat(2,minmax(0,1fr)); }
  .class-top-metrics article { gap: 7px; padding: 10px; }
  .class-top-metrics article > svg { width: 34px; height: 34px; padding: 7px; }
  .class-management .classroom-detail-head { flex-direction: column; }
}

</style>
