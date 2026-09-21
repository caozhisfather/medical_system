<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, ChartNetwork, Database, Layers3, ListChecks, SlidersHorizontal, Sparkles } from '@lucide/vue';
import { getExamSettings, getTeachingKnowledge } from '../api';
import type { ExamSettings } from '../types';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';

const router = useRouter();
const knowledgeTotal = ref(0);
const typeCounts = ref<Record<string, number>>({});
const settings = ref<ExamSettings | null>(null);
const loading = ref(true);

const enabledTypes = computed(() => {
  const types = settings.value?.question_types;
  if (!types) return [];
  const labels: Array<[string, { enabled: boolean; weight: number }]> = [
    ['选择题', types.single_choice],
    ['判断题', types.true_false],
    ['简答题', types.short_answer]
  ];
  return labels.filter(([, value]) => value.enabled).map(([label, value]) => ({ label, weight: value.weight }));
});

const difficultyLabel = computed(() => {
  const map: Record<string, string> = { basic: '基础识记', exam: '考试标准', clinical: '临床应用' };
  return map[settings.value?.difficulty ?? ''] ?? '未设置';
});

const generationLabel = computed(() => (settings.value?.generation_mode === 'realtime' ? '实时生成' : '预生成题库'));

const documentTypes = computed(() =>
  Object.entries(typeCounts.value).map(([key, value]) => ({
    key,
    label: key === 'textbook' ? '教材' : key === 'evidence' ? '权威依据' : key === 'case' ? '病例资料' : key,
    value
  }))
);

onMounted(async () => {
  const [knowledge, exam] = await Promise.allSettled([getTeachingKnowledge({}, 'teacher'), getExamSettings()]);
  if (knowledge.status === 'fulfilled') {
    knowledgeTotal.value = knowledge.value.total ?? knowledge.value.items?.length ?? 0;
    typeCounts.value = knowledge.value.type_counts ?? {};
  }
  if (exam.status === 'fulfilled') settings.value = exam.value;
  loading.value = false;
});
</script>

<template>
  <div class="workspace-page teacher-page">
    <section class="teacher-dashboard-hero" data-tour="teacher-dashboard-hero">
      <div>
        <span class="section-kicker">解剖学课程 · 2023-2 班</span>
        <h1>教学知识库与命题控制</h1>
        <p>维护可追溯的教学依据，决定学生做哪些题型、按什么难度和提示词出题。</p>
      </div>
      <button class="button-primary" type="button" @click="router.push('/teacher/exam-settings')">配置题型与提示词 <ArrowRight :size="18" /></button>
    </section>

    <section class="metric-strip teacher-metrics">
      <article><Database :size="19" /><span><small>知识库条目</small><strong>{{ loading ? '—' : knowledgeTotal }}</strong></span><b>可检索依据</b></article>
      <article><Layers3 :size="19" /><span><small>覆盖教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong></span><b>三维模型</b></article>
      <article><ListChecks :size="19" /><span><small>启用题型</small><strong>{{ enabledTypes.length }} 种</strong></span><b>学生可见</b></article>
      <article><BookOpenCheck :size="19" /><span><small>当前难度</small><strong>{{ difficultyLabel }}</strong></span><b>可随时调整</b></article>
    </section>

    <div class="teacher-dashboard-grid">
      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">命题配置</span><h2>学生将遇到的题型</h2></div><SlidersHorizontal :size="20" /></div>
        <ul class="teacher-config-list">
          <li v-for="item in enabledTypes" :key="item.label"><span>{{ item.label }}</span><strong>{{ item.weight }}%</strong></li>
          <li v-if="!enabledTypes.length" class="is-empty">尚未启用任何题型，学生端不会出题。</li>
        </ul>
        <p class="teacher-config-note">出题方式：{{ generationLabel }}。修改后即时生效，无需重新部署。</p>
        <button class="button-secondary" type="button" @click="router.push('/teacher/exam-settings')">调整配置 <ArrowRight :size="16" /></button>
      </section>

      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">知识库构成</span><h2>依据来源分布</h2></div><Database :size="20" /></div>
        <article v-for="item in documentTypes" :key="item.key" class="teacher-type-row">
          <span>{{ item.label }}</span>
          <b :style="{ width: `${knowledgeTotal ? Math.round((item.value / knowledgeTotal) * 100) : 0}%` }" />
          <strong>{{ item.value }}</strong>
        </article>
        <p v-if="!documentTypes.length" class="empty-copy">知识库还没有条目，先导入教材或权威医学依据。</p>
        <button class="button-secondary" type="button" @click="router.push('/teacher/knowledge')">管理教学知识库 <ArrowRight :size="16" /></button>
      </section>
    </div>

    <div class="teacher-dashboard-grid lower">
      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">提示词</span><h2>当前出题指令</h2></div><Sparkles :size="20" /></div>
        <p class="teacher-prompt-preview">{{ settings?.system_prompt || '尚未加载提示词配置。' }}</p>
        <button class="text-button" type="button" @click="router.push('/teacher/exam-settings')">编辑系统提示词 <ArrowRight :size="15" /></button>
      </section>
      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">结构关联</span><h2>知识图谱</h2></div><ChartNetwork :size="20" /></div>
        <p class="teacher-prompt-preview">解剖结构节点连接功能、临床联系与检查处置，用于支撑讲解与命题的依据链。</p>
        <button class="text-button" type="button" @click="router.push('/knowledge-graph')">打开知识图谱 <ArrowRight :size="15" /></button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.teacher-dashboard-hero { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 22px 24px; border-radius: 8px; background: #eef6f4; }
.teacher-dashboard-hero h1 { margin: 4px 0 6px; color: #16414a; font-size: 1.6rem; }
.teacher-dashboard-hero p { margin: 0; max-width: 640px; color: #5a757b; font-size: 13px; line-height: 1.6; }
.teacher-config-list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
.teacher-config-list li { display: flex; align-items: center; justify-content: space-between; padding: 9px 11px; border-radius: 7px; background: #f2f7f6; color: #35535a; font-size: 13px; }
.teacher-config-list li strong { color: var(--teal-dark, #075b57); }
.teacher-config-list li.is-empty { justify-content: flex-start; color: #8b9a9c; font-size: 12px; }
.teacher-config-note { margin: 0; color: #6d8a8d; font-size: 12px; }
.teacher-type-row { position: relative; display: grid; grid-template-columns: 1fr 64px; align-items: center; gap: 8px; padding: 9px 11px; border-radius: 7px; background: #f2f7f6; }
.teacher-type-row span { color: #35535a; font-size: 13px; }
.teacher-type-row strong { color: #21484e; text-align: right; }
.teacher-type-row b { position: absolute; left: 11px; bottom: 5px; height: 3px; border-radius: 2px; background: rgba(15,118,110,.35); }
.teacher-prompt-preview { margin: 0; max-height: 150px; overflow: auto; color: #4f6b70; font-size: 12px; line-height: 1.65; white-space: pre-wrap; }
.empty-copy { color: #8b9a9c; font-size: 12px; }
</style>
