<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { BookOpenCheck, Check, FileClock, LoaderCircle, Plus, Sparkles, TriangleAlert, Users } from '@lucide/vue';
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
    const nextId = preferredId || activeClassId.value || classrooms.value[0]?.id || '';
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
  activeClassId.value = classId;
  loadingDetail.value = true;
  error.value = '';
  try {
    detail.value = await getClassroomDetail(classId);
    const nextStudentId = detail.value.students[0]?.student_id ?? '';
    selectedStudentId.value = nextStudentId;
    if (nextStudentId) await loadGuidance(nextStudentId);
    else guidance.value = [];
  } catch (reason) {
    detail.value = null;
    error.value = reason instanceof Error ? reason.message : '班级详情读取失败';
  } finally {
    loadingDetail.value = false;
  }
}

async function loadGuidance(studentId: string) {
  if (!activeClassId.value || !studentId) return;
  loadingGuidance.value = true;
  try {
    guidance.value = (await getClassroomGuidance(activeClassId.value, studentId)).items;
  } catch {
    guidance.value = [];
  } finally {
    loadingGuidance.value = false;
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
  sending.value = true;
  error.value = '';
  try {
    const created = await sendClassroomGuidance(activeClassId.value, {
      student_id: student.student_id,
      content,
      recommended_score: guidanceForm.value.recommendedScore
    });
    guidance.value = [created, ...guidance.value];
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
  aiLoading.value = true;
  error.value = '';
  try {
    const created = await generateAiClassroomGuidance(activeClassId.value, student.student_id);
    guidance.value = [created, ...guidance.value];
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
  <div class="workspace-page classroom-page">
    <section class="classroom-hero">
      <div>
        <span class="section-kicker">教师端 · 班级与学情</span>
        <h1>班级管理</h1>
        <p>创建班级后把班级码发给学生。学生加入后，你可以查看真实作答表现、发送指导，也可以让AI学习教练生成复练建议。</p>
      </div>
      <button class="button-primary" type="button" @click="showCreate = !showCreate"><Plus :size="17" />创建班级</button>
    </section>

    <section v-if="showCreate" class="classroom-create">
      <label><span>班级名称</span><input v-model="createForm.name" maxlength="60" placeholder="例如：临床医学 2026-1 班" /></label>
      <label><span>班级说明</span><input v-model="createForm.description" maxlength="500" placeholder="课程、学期或教学范围" /></label>
      <button class="button-primary" type="button" :disabled="creating || createForm.name.trim().length < 2" @click="createClass">
        <LoaderCircle v-if="creating" class="spin" :size="16" /><Plus v-else :size="16" />{{ creating ? '创建中' : '确认创建' }}
      </button>
    </section>

    <p v-if="error" class="classroom-banner is-error"><TriangleAlert :size="16" />{{ error }}</p>
    <p v-else-if="message" class="classroom-banner is-ok"><Check :size="16" />{{ message }}</p>

    <div v-if="loadingClasses" class="classroom-state"><LoaderCircle class="spin" :size="22" />正在读取班级</div>

    <div v-else-if="!classrooms.length" class="classroom-empty">
      <Users :size="30" />
      <strong>还没有班级</strong>
      <p>先创建班级，再把系统生成的班级码发给学生。</p>
      <button class="button-primary" type="button" @click="showCreate = true"><Plus :size="17" />创建第一个班级</button>
    </div>

    <div v-else class="classroom-layout">
      <aside class="classroom-list">
        <button v-for="item in classrooms" :key="item.id" type="button" :class="{ active: item.id === activeClassId }" @click="selectClass(item.id)">
          <span><strong>{{ item.name }}</strong><small>{{ item.student_count }} 名学生</small></span>
          <b>{{ item.code }}</b>
        </button>
      </aside>

      <main v-if="loadingDetail" class="classroom-state"><LoaderCircle class="spin" :size="22" />正在统计学情</main>
      <main v-else-if="detail" class="classroom-detail">
        <header class="classroom-detail-head">
          <div><span>{{ detail.teacher_name }}</span><h2>{{ detail.name }}</h2><p>{{ detail.description || '暂无班级说明' }}</p></div>
          <button type="button" class="class-code" @click="copyCode"><small>班级码</small><strong>{{ detail.code }}</strong><span>{{ codeCopied ? '已复制' : '点击复制' }}</span></button>
        </header>

        <section class="classroom-metrics">
          <article><small>班级人数</small><strong>{{ detail.students.length }}</strong></article>
          <article><small>平均得分</small><strong>{{ detail.students.length ? Math.round(detail.students.reduce((sum, item) => sum + item.average_score, 0) / detail.students.length) : 0 }}</strong></article>
          <article><small>累计作答</small><strong>{{ detail.students.reduce((sum, item) => sum + item.total_attempts, 0) }}</strong></article>
        </section>

        <section class="student-grid">
          <button v-for="student in detail.students" :key="student.student_id" type="button" :class="{ active: student.student_id === selectedStudentId }" @click="selectStudent(student.student_id)">
            <header><strong>{{ student.student_name }}</strong><span>{{ student.average_score }} 分</span></header>
            <p>{{ student.total_attempts }} 次作答 · 定位 {{ student.anatomy.total }} · 刷题 {{ student.quiz.total }}</p>
            <small>{{ student.weak_points.length ? `重点：${student.weak_points.slice(0, 2).join('、')}` : '暂无明确薄弱项' }}</small>
          </button>
          <div v-if="!detail.students.length" class="classroom-empty compact"><Users :size="24" /><strong>暂时没有学生加入</strong><p>把班级码 {{ detail.code }} 发给学生即可。</p></div>
        </section>

        <section v-if="selectedStudent" class="student-guidance">
          <header>
            <div><span>学生指导</span><h3>{{ selectedStudent.student_name }}</h3></div>
            <button class="button-secondary" type="button" :disabled="aiLoading" @click="generateAiGuidance">
              <LoaderCircle v-if="aiLoading" class="spin" :size="16" /><Sparkles v-else :size="16" />{{ aiLoading ? '生成中' : 'AI生成建议' }}
            </button>
          </header>

          <div class="student-performance">
            <article><small>综合得分</small><strong>{{ selectedStudent.average_score }}</strong></article>
            <article><small>定位正确率</small><strong>{{ selectedStudent.anatomy.accuracy }}%</strong></article>
            <article><small>刷题正确率</small><strong>{{ selectedStudent.quiz.accuracy }}%</strong></article>
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
</style>
