<script setup lang="ts">
import overviewBanner from '../assets/medical/teaching-overview-reference-banner.webp';
import { computed, onMounted, ref } from 'vue';
import { ArrowRight, BookOpenCheck, ChartNetwork, ChartColumn, Check, ChevronRight, ClipboardList, Database, GraduationCap, Layers3, ListChecks, LoaderCircle, Megaphone, Pencil, RefreshCw, SlidersHorizontal, Users } from '@lucide/vue';
import { getExamSettings, getMyClassrooms, getTeachingKnowledge } from '../api';
import MarkdownContent from '../components/MarkdownContent.vue';
import type { CaseLibraryEntry, ClassroomSummary, ExamSettings } from '../types';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';

const knowledgeTotal = ref(0);
const typeCounts = ref<Record<string, number>>({});
const knowledgeItems = ref<CaseLibraryEntry[]>([]);
const classrooms = ref<ClassroomSummary[]>([]);
const settings = ref<ExamSettings | null>(null);
const loading = ref(true);
const errors = ref<string[]>([]);
const knowledgeReady = ref(false);
const classroomReady = ref(false);
const colors = ['#2782ff', '#55b9fa', '#a69aff'];

const enabledTypes = computed(() => {
  const types = settings.value?.question_types;
  if (!types) return [];
  const labels: Array<[string, { enabled: boolean; weight: number }]> = [
    ['选择题', types.single_choice], ['判断题', types.true_false], ['简答题', types.short_answer]
  ];
  const enabled = labels.filter(([, value]) => value.enabled);
  const total = enabled.reduce((sum, [, value]) => sum + Math.max(0, value.weight), 0);
  return enabled.map(([label, value], index) => ({
    label, weight: value.weight, share: total ? Math.max(0, value.weight) / total * 100 : 0, color: colors[index]
  }));
});
const donutFill = computed(() => {
  let stop = 0;
  const segments = enabledTypes.value.map(type => {
    const start = stop;
    stop += type.share;
    return type.color + ' ' + start + '% ' + stop + '%';
  });
  return stop ? 'conic-gradient(' + segments.join(', ') + ')' : '#dfe8f8';
});
const difficultyLabel = computed(() => {
  const labels: Record<string, string> = { basic: '基础识记', exam: '考试标准', clinical: '临床应用' };
  return labels[settings.value?.difficulty ?? ''] ?? '—';
});
const generationLabel = computed(() => settings.value?.generation_mode === 'realtime' ? '实时生成' : '预生成题库');
const documentTypes = computed(() => {
  const types = [
    { key: 'case', label: '病例资料' }, { key: 'textbook', label: '教材' }, { key: 'evidence', label: '权威依据' }
  ];
  const extras = Object.keys(typeCounts.value).filter(key => key !== 'all' && !types.some(type => type.key === key));
  return [...types, ...extras.map(key => ({ key, label: key }))].map(item => ({
    ...item, value: typeCounts.value[item.key] ?? 0
  }));
});
const sourceCeiling = computed(() => {
  const largest = Math.max(1, ...documentTypes.value.map(type => type.value));
  const step = Math.max(1, 10 ** Math.floor(Math.log10(largest)) / 5);
  return Math.max(1, Math.ceil(largest / step) * step);
});
const chartTicks = computed(() => [1, .75, .5, .25, 0].map(value => Math.round(sourceCeiling.value * value)));
const shortcuts = [
  { label: '班级与学情', path: '/teacher/classrooms', icon: Users },
  { label: '配置题型与提示词', path: '/teacher/exam-settings', icon: SlidersHorizontal },
  { label: '管理教学知识库', path: '/teacher/knowledge', icon: BookOpenCheck },
  { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork }
];
const studentCount = computed(() => classrooms.value.reduce((sum, item) => sum + item.student_count, 0));
const activities = computed(() => {
  const entries = knowledgeItems.value.map(item => ({
    key: 'knowledge-' + item.id, text: '知识库更新 · ' + item.title,
    time: item.updated_at || item.created_at, path: '/teacher/knowledge'
  }));
  if (settings.value?.updated_at) entries.push({
    key: 'settings', text: '命题配置已更新', time: settings.value.updated_at, path: '/teacher/exam-settings'
  });
  for (const item of classrooms.value) entries.push({
    key: 'class-' + item.id, text: '创建班级 · ' + item.name, time: item.created_at, path: '/teacher/classrooms'
  });
  return entries.filter(entry => Number.isFinite(Date.parse(entry.time)))
    .sort((a, b) => Date.parse(b.time) - Date.parse(a.time)).slice(0, 4);
});
function formatDate(value: string) {
  return new Date(value).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}
async function loadOverview() {
  if (loading.value && (settings.value || knowledgeReady.value)) return;
  loading.value = true;
  errors.value = [];
  const [knowledge, exam, classes] = await Promise.allSettled([
    getTeachingKnowledge({}, 'teacher'), getExamSettings(), getMyClassrooms()
  ]);
  if (knowledge.status === 'fulfilled') {
    knowledgeTotal.value = knowledge.value.total ?? knowledge.value.items.length;
    knowledgeItems.value = knowledge.value.items;
    typeCounts.value = knowledge.value.type_counts ?? {};
    knowledgeReady.value = true;
  } else errors.value.push('知识库数据读取失败');
  if (exam.status === 'fulfilled') settings.value = exam.value;
  else errors.value.push('命题配置读取失败');
  if (classes.status === 'fulfilled') {
    classrooms.value = classes.value.items;
    classroomReady.value = true;
  } else errors.value.push('班级数据读取失败');
  loading.value = false;
}
onMounted(loadOverview);
</script>

<template>
  <div class="workspace-page teaching-overview">
    <section class="teaching-banner" data-tour="teacher-dashboard-hero" :style="{'--overview-banner':`url(${overviewBanner})`}">
      <span class="teaching-breadcrumb">教师工作台 <b>›</b> 教学总览</span>
      <h1>教学总览</h1>
      <p>掌握教学动态，统筹班级、知识资源与命题配置。</p>
    </section>

    <div v-if="errors.length" class="teaching-error" role="alert">
      <span>{{ errors.join('，') }}。</span>
      <button type="button" :disabled="loading" @click="loadOverview"><RefreshCw :size="14" />重新读取</button>
    </div>

    <section class="teaching-metrics" aria-label="教学指标">
      <article><span class="teaching-icon"><Database /></span><div><small>知识点总量</small><strong>{{ loading || !knowledgeReady ? '—' : knowledgeTotal }}</strong></div></article>
      <article><span class="teaching-icon"><Layers3 /></span><div><small>课程教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong></div></article>
      <article><span class="teaching-icon"><ListChecks /></span><div><small>应用题型</small><strong>{{ loading || !settings ? '—' : enabledTypes.length + ' 种' }}</strong></div></article>
      <article><span class="teaching-icon"><GraduationCap /></span><div><small>当前出题难度</small><strong class="teaching-metric-text">{{ difficultyLabel }}</strong></div></article>
      <article><span class="teaching-icon"><Users /></span><div><small>教学班级</small><strong>{{ loading || !classroomReady ? '—' : classrooms.length }} <small v-if="classroomReady && !loading">个</small></strong></div></article>
    </section>

    <div class="teaching-charts">
      <section class="teaching-panel">
        <header><h2><ClipboardList />学生将遇到的题型</h2><RouterLink to="/teacher/exam-settings">查看详情<ArrowRight :size="15" /></RouterLink></header>
        <div v-if="settings" class="teaching-question-chart">
          <div class="teaching-donut" :style="{ background: donutFill }" role="img" :aria-label="enabledTypes.map(type => type.label + ' ' + Math.round(type.share) + '%').join('，') || '未启用题型'"><strong>题型占比</strong></div>
          <ul>
            <li v-for="type in enabledTypes" :key="type.label"><i :style="{ background: type.color }"></i><span>{{ type.label }}</span><strong>{{ Math.round(type.share) }}%</strong></li>
            <li v-if="!enabledTypes.length" class="teaching-quiet">尚未启用题型</li>
          </ul>
        </div>
        <p v-else class="teaching-placeholder"><LoaderCircle v-if="loading" class="spin" :size="18" />{{ loading ? '正在读取题型配置' : '题型配置暂不可用' }}</p>
        <p v-if="settings" class="teaching-caption">出题方式 · {{ generationLabel }}</p>
      </section>

      <section class="teaching-panel">
        <header><h2><ChartColumn />知识库来源分布</h2><RouterLink to="/teacher/knowledge">查看详情<ArrowRight :size="15" /></RouterLink></header>
        <div v-if="knowledgeReady" class="teaching-bar-chart" role="img" :aria-label="documentTypes.map(type => type.label + ' ' + type.value + ' 条').join('，')">
          <div class="teaching-chart-axis"><span v-for="(tick, index) in chartTicks" :key="index">{{ tick }}</span></div>
          <div class="teaching-plot">
            <div class="teaching-grid" aria-hidden="true"><i v-for="tick in 5" :key="tick"></i></div>
            <div v-for="item in documentTypes" :key="item.key" class="teaching-bar-column">
              <div><span :style="{ height: item.value / sourceCeiling * 100 + '%' }"><b>{{ item.value }}</b></span></div>
              <small>{{ item.label }}</small>
            </div>
          </div>
        </div>
        <p v-else class="teaching-placeholder">{{ loading ? '正在读取知识库' : '知识库数据暂不可用' }}</p>
      </section>
    </div>

    <nav class="teaching-shortcuts" aria-label="常用入口">
      <strong>常用入口</strong>
      <RouterLink v-for="item in shortcuts" :key="item.path" :to="item.path"><span class="teaching-icon"><component :is="item.icon" /></span><b>{{ item.label }}</b><ArrowRight :size="16" /></RouterLink>
    </nav>

    <div class="teaching-lower">
      <section class="teaching-panel teaching-prompt">
        <header><h2><ClipboardList />当前出题指令</h2><RouterLink to="/teacher/exam-settings"><Pencil :size="14" />编辑</RouterLink></header>
        <MarkdownContent v-if="settings?.system_prompt" :content="settings.system_prompt" />
        <p v-else class="teaching-quiet">{{ loading ? '正在读取出题指令' : '尚未配置出题指令' }}</p>
      </section>

      <section class="teaching-panel teaching-workbench">
        <header><h2><ListChecks />教学工作台</h2></header>
        <RouterLink to="/teacher/classrooms"><Users :size="17" /><span>管理教学班级</span><strong>{{ classroomReady ? classrooms.length : '—' }}</strong><ChevronRight :size="15" /></RouterLink>
        <RouterLink to="/teacher/classrooms"><GraduationCap :size="17" /><span>查看班级学生</span><strong>{{ classroomReady ? studentCount : '—' }}</strong><ChevronRight :size="15" /></RouterLink>
        <RouterLink to="/teacher/exam-settings"><Check :size="17" /><span>已启用题型</span><strong>{{ settings ? enabledTypes.length : '—' }}</strong><ChevronRight :size="15" /></RouterLink>
        <p class="teaching-caption">班级与学情用于查看学生作答和学习建议。</p>
      </section>

      <section class="teaching-panel teaching-activity">
        <header><h2><Megaphone />最近更新</h2><button type="button" :disabled="loading" aria-label="刷新教学总览" @click="loadOverview"><RefreshCw :size="15" :class="{ spin: loading }" /></button></header>
        <ul v-if="activities.length">
          <li v-for="item in activities" :key="item.key"><RouterLink :to="item.path"><i></i><span :title="item.text">{{ item.text }}</span><time :datetime="item.time">{{ formatDate(item.time) }}</time></RouterLink></li>
        </ul>
        <p v-else class="teaching-quiet">{{ loading ? '正在读取更新记录' : '暂无可显示的更新记录' }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.teaching-overview { display: grid; gap: 12px; color: #10214b; }
.teaching-banner { min-height: 148px; padding: 26px clamp(18px, 3vw, 44px); border: 1px solid #ffffffce; border-radius: 18px; background: linear-gradient(90deg, #e6f0ff 0%, #e6f0ffed 30%, #e6f0ff00 76%), #e6f0ff url('../assets/medical/teacher-overview-medical-v2.webp') right center / auto 135% no-repeat; box-shadow: 0 4px 14px #244da012; }
.teaching-banner h1 { margin: 0 0 7px; font-size: clamp(26px, 2.6vw, 38px); line-height: 1.2; }
.teaching-banner p { max-width: 65%; margin: 0; color: #3a527a; font-size: 14px; line-height: 1.6; }
.teaching-panel, .teaching-metrics article, .teaching-shortcuts > a { min-width: 0; border: 1px solid #fff; border-radius: 15px; background: linear-gradient(145deg, #fcfdfff5, #eef5ffeb); box-shadow: 0 4px 12px #22478112; }
.teaching-metrics { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.teaching-metrics article { display: flex; align-items: center; gap: 12px; padding: 14px clamp(9px, 1.4vw, 20px); }
.teaching-icon { display: grid; flex: 0 0 auto; width: 44px; aspect-ratio: 1; place-items: center; border-radius: 14px; background: linear-gradient(135deg, #e4f2ff, #d1e1ff); color: #1262f5; }
.teaching-icon svg { width: 24px; height: 24px; }
.teaching-metrics article > div { display: grid; min-width: 0; gap: 5px; }
.teaching-metrics small { color: #3c5276; font-size: 12px; }
.teaching-metrics strong { color: #074aee; font-size: 27px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.teaching-metrics strong.teaching-metric-text { font-size: clamp(16px, 1.6vw, 23px); }
.teaching-charts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.teaching-panel { padding: 14px clamp(12px, 1.5vw, 22px); }
.teaching-panel > header { display: flex; align-items: center; justify-content: space-between; gap: 9px; margin-bottom: 12px; }
.teaching-panel h2 { display: flex; align-items: center; gap: 9px; margin: 0; font-size: 17px; line-height: 1.3; }
.teaching-panel h2 svg { flex: 0 0 auto; width: 22px; height: 22px; color: #1262f5; }
.teaching-panel header :is(a, button) { display: inline-flex; align-items: center; gap: 6px; padding: 3px; border: 0; border-radius: 5px; background: transparent; color: #154cb1; font-size: 12px; white-space: nowrap; text-decoration: none; cursor: pointer; }
.teaching-panel header a:hover { text-decoration: underline; }
.teaching-question-chart { display: grid; grid-template-columns: 1fr 1fr; align-items: center; justify-items: center; gap: 20px; min-height: 157px; }
.teaching-donut { position: relative; isolation: isolate; display: grid; width: clamp(115px, 11vw, 160px); aspect-ratio: 1; place-items: center; border-radius: 50%; }
.teaching-donut::before { position: absolute; inset: 18%; z-index: -1; border-radius: inherit; background: #f3f8ff; content: ''; }
.teaching-donut strong { font-size: 13px; }
.teaching-question-chart ul { display: grid; gap: 8px; width: 100%; max-width: 210px; margin: 0; padding: 0; list-style: none; }
.teaching-question-chart li { display: flex; align-items: center; gap: 9px; padding: 5px 0 8px; border-bottom: 1px solid #e2eaf8; font-size: 13px; }
.teaching-question-chart li i { width: 9px; height: 9px; border-radius: 3px; }
.teaching-question-chart li strong { margin-left: auto; font-size: 17px; }
.teaching-caption { margin: 8px 0 0; color: #546c8d; font-size: 11px; line-height: 1.6; }
.teaching-bar-chart { display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 8px; padding: 12px 4px 0; }
.teaching-chart-axis { display: flex; height: 143px; flex-direction: column; justify-content: space-between; color: #425a81; font-size: 11px; }
.teaching-plot { position: relative; display: flex; gap: 8px; align-items: stretch; padding: 0 10px; border-left: 1px solid #a5b8d5; }
.teaching-grid { position: absolute; top: 0; right: 0; left: 0; display: flex; height: 143px; flex-direction: column; justify-content: space-between; pointer-events: none; }
.teaching-grid i { border-top: 1px solid #d9e6fb; }
.teaching-bar-column { position: relative; z-index: 1; display: grid; flex: 1; min-width: 0; gap: 7px; text-align: center; }
.teaching-bar-column > div { display: flex; height: 143px; justify-content: center; align-items: flex-end; }
.teaching-bar-column > div > span { position: relative; width: min(70%, 65px); border-radius: 5px 5px 0 0; background: linear-gradient(180deg, #2987ff, #326de6); }
.teaching-bar-column b { position: absolute; bottom: calc(100% + 3px); left: 0; width: 100%; font-size: 13px; }
.teaching-bar-column small { color: #3a5276; font-size: 11px; }
.teaching-shortcuts { display: grid; grid-template-columns: auto repeat(4, minmax(0, 1fr)); align-items: center; gap: 10px; padding: 3px 0; }
.teaching-shortcuts > strong { font-size: 14px; white-space: nowrap; }
.teaching-shortcuts > a { display: flex; align-items: center; justify-content: center; gap: 9px; min-height: 61px; padding: 7px 9px; color: #142c55; text-decoration: none; }
.teaching-shortcuts > a:hover { border-color: #a5c7ff; background: #e6f0ff; }
.teaching-shortcuts .teaching-icon { width: 36px; border-radius: 50%; }
.teaching-shortcuts .teaching-icon svg { width: 20px; height: 20px; }
.teaching-shortcuts b { font-size: 12px; }
.teaching-shortcuts > a > svg { flex: 0 0 auto; color: #155dee; }
.teaching-lower { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, .95fr) minmax(0, 1fr); gap: 12px; }
.teaching-prompt :deep(.markdown-content) { max-height: 167px; margin: 0; overflow: auto; padding: 10px 12px; border-radius: 10px; background: #eaf2ff; color: #30496f; font-size: 12px; line-height: 1.7; }
.teaching-prompt :deep(.markdown-content p) { margin: 0 0 3px; }
.teaching-prompt :deep(.markdown-content ol), .teaching-prompt :deep(.markdown-content ul) { margin: 4px 0; padding-left: 20px; }
.teaching-workbench > a { display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; align-items: center; gap: 7px; padding: 11px 0; border-bottom: 1px solid #dee8f9; color: #29446e; font-size: 12px; text-decoration: none; }
.teaching-workbench > a > svg { color: #2366df; }
.teaching-workbench > a:hover { color: #1258dc; }
.teaching-activity ul { margin: 0; padding: 0; list-style: none; }
.teaching-activity li + li { border-top: 1px solid #e1eafa; }
.teaching-activity li a { display: grid; grid-template-columns: 6px minmax(0, 1fr) auto; align-items: center; gap: 8px; padding: 10px 0; color: #324c73; text-decoration: none; font-size: 12px; }
.teaching-activity li a:hover { color: #1258dc; }
.teaching-activity li i { width: 5px; height: 5px; border-radius: 50%; background: #2875f7; }
.teaching-activity li span { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.teaching-activity time { color: #536c8e; font-size: 11px; }
.teaching-error { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; padding: 8px 12px; border: 1px solid #f3cca5; border-radius: 10px; background: #fff5e7; color: #854d22; font-size: 13px; }
.teaching-error button { display: inline-flex; gap: 5px; align-items: center; border: 0; background: transparent; color: inherit; cursor: pointer; }
.teaching-placeholder { display: flex; min-height: 170px; align-items: center; justify-content: center; gap: 7px; margin: 0; color: #546c8d; font-size: 13px; }
.teaching-quiet { color: #546c8d; font-size: 13px; }
@media (max-width: 1100px) {
  .teaching-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .teaching-shortcuts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .teaching-shortcuts > strong { grid-column: 1 / -1; }
  .teaching-lower { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .teaching-prompt { grid-column: 1 / -1; }
}
@media (max-width: 650px) {
  .teaching-banner { min-height: 165px; background-position: right center; background-size: auto, auto 100%; background-image: linear-gradient(90deg, #e6f0fff5, #e6f0ffb8 58%, #e6f0ff10), url('../assets/medical/teacher-overview-medical-v2.webp'); }
  .teaching-banner p { max-width: 70%; font-size: 12px; }
  .teaching-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .teaching-charts, .teaching-lower { grid-template-columns: minmax(0, 1fr); }
  .teaching-shortcuts > a { gap: 6px; }
  .teaching-metrics article { gap: 7px; }
  .teaching-metrics .teaching-icon { width: 34px; border-radius: 10px; }
  .teaching-shortcuts .teaching-icon { width: 28px; }
  .teaching-shortcuts > a > svg { width: 13px; }
}

/* Reference-style hero, scoped to teaching overview only. */
.teaching-banner{min-height:142px;padding:15px 32px;border:1px solid #e1ebff;border-radius:20px;overflow:hidden;background-color:#deecff;background-image:linear-gradient(90deg,#e0edff 0%,#deecff12 75%),var(--overview-banner);background-size:100% 100%,auto 200%;background-repeat:no-repeat;background-position:center,right center;box-shadow:0 4px 12px #244da010}
.teaching-breadcrumb{display:block;font-size:12px;line-height:1.6;font-weight:700;color:#0754f5}.teaching-breadcrumb b{padding:0 10px;color:#7ba9fa;font-weight:500}.teaching-banner h1{margin:12px 0 8px;font-size:38px;line-height:1.2;font-weight:800;letter-spacing:-.5px}.teaching-banner p{max-width:65%;font-size:13px;line-height:1.8;color:#36547f;margin:0}
@media(max-width:1100px) and (min-width:651px){.teaching-banner{min-height:150px;padding:18px 26px;background-size:100% 100%,auto 175%}.teaching-banner h1{font-size:32px}.teaching-banner p{max-width:64%;font-size:12px}}
@media(max-width:650px){.teaching-banner{min-height:170px;padding:19px 22px;background-image:linear-gradient(90deg,#e0edfffa 0%,#e0edffdf 60%,#deecff60),var(--overview-banner);background-size:100% 100%,auto 175%;background-position:center,right center}.teaching-banner h1{font-size:28px;margin:12px 0 10px}.teaching-banner p{max-width:90%;font-size:12px}.teaching-breadcrumb{font-size:11px}}
</style>
