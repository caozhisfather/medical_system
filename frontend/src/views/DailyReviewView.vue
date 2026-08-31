<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Activity, AlertTriangle, ArrowRight, BookOpenCheck, Bot, CalendarCheck2, ChartNetwork, ClipboardList, LoaderCircle, Route, Stethoscope } from '@lucide/vue';
import { generateDailyReview, getDailyReviewHistory, getTodayDailyReview } from '../api';
import DigitalHumanWorkspace from '../components/DigitalHumanWorkspace.vue';
import { mockDailyReview, mockDailyReviewHistory } from '../data/dailyReview';
import { trainingStore } from '../stores/training';
import type { DailyReview, DigitalHumanState } from '../types';

const router = useRouter();
const review = ref<DailyReview>(mockDailyReview);
const history = ref<DailyReview[]>(mockDailyReviewHistory);
const generating = ref(false);
const initialLoading = ref(true);
const speakKey = ref(0);

const studentId = computed(() => trainingStore.state.profile.name || 'student_001');
const hasRisk = computed(() => review.value.high_risk_misses.length > 0 || review.value.teacher_attention_required);
const digitalHumanState = computed<DigitalHumanState>(() => hasRisk.value ? 'warning' : 'reviewing');
const performanceLabels: Record<string, string> = {
  inquiry_completeness: '问诊完整性',
  differential_diagnosis: '鉴别诊断能力',
  exam_selection: '检查选择能力',
  guideline_evidence: '指南依据使用',
  anatomy_accuracy: '解剖定位准确率',
  clinical_safety: '临床安全意识'
};
const performanceKeys = Object.keys(performanceLabels);
const radarAxes = performanceKeys.map((key, index) => {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / performanceKeys.length;
  return { key, label: performanceLabels[key], x: 50 + Math.cos(angle) * 43, y: 50 + Math.sin(angle) * 43, angle };
});
const radarGrid = [25, 50, 75, 100].map((level) => performanceKeys.map((_, index) => {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / performanceKeys.length;
  return `${50 + Math.cos(angle) * 43 * level / 100},${50 + Math.sin(angle) * 43 * level / 100}`;
}).join(' '));
const radarPoints = computed(() => performanceKeys.map((key, index) => {
  const score = Number(review.value.performance[key] ?? 0);
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / performanceKeys.length;
  return `${50 + Math.cos(angle) * 43 * score / 100},${50 + Math.sin(angle) * 43 * score / 100}`;
}).join(' '));

onMounted(async () => {
  try {
    const [today, records] = await Promise.all([
      getTodayDailyReview(studentId.value),
      getDailyReviewHistory(studentId.value)
    ]);
    review.value = today;
    history.value = records;
  } catch {
    review.value = mockDailyReview;
    history.value = mockDailyReviewHistory;
  } finally {
    initialLoading.value = false;
  }
});

async function generateReview() {
  if (generating.value) return;
  generating.value = true;
  try {
    review.value = await generateDailyReview(studentId.value);
  } catch {
    review.value = { ...mockDailyReview, review_id: `DR-${Date.now()}`, status: '已生成' };
  } finally {
    generating.value = false;
    speakKey.value += 1;
  }
}

function openWeakPoint(point: string) {
  if (point.includes('解剖') || point.includes('肝胆胰')) {
    router.push({ path: '/student/anatomy', query: { exercise: 'liver_position' } });
    return;
  }
  if (point.includes('腹痛') || point.includes('查体')) {
    router.push({ path: '/student/case/new', query: { case: 'acute_abdominal_pain' } });
    return;
  }
  router.push({ path: '/knowledge-graph', query: { q: point } });
}
</script>

<template>
  <div class="workspace-page daily-review-page">
    <section class="daily-review-hero" data-tour="daily-review">
      <div>
        <span class="section-kicker">今日复盘 · {{ review.date }}</span>
        <h1>学习任务、AI 训练、反馈复盘和明日计划已闭环</h1>
        <p>{{ review.summary }}</p>
        <div class="review-actions">
          <button class="button-primary" type="button" :disabled="generating" @click="generateReview">
            <LoaderCircle v-if="generating" class="spin" :size="18" />
            <CalendarCheck2 v-else :size="18" />
            {{ generating ? '正在生成复盘' : '生成 mock 今日复盘' }}
          </button>
          <button class="button-secondary" type="button" @click="speakKey += 1"><Bot :size="17" /> 数字人讲解复盘</button>
        </div>
      </div>
      <aside class="review-status-card" :class="{ risk: hasRisk }">
        <strong>{{ review.status }}</strong>
        <span>{{ hasRisk ? '需要优先处理高风险遗漏' : '今日训练可进入巩固阶段' }}</span>
        <b>{{ review.average_score }}</b>
        <small>今日平均分</small>
      </aside>
    </section>

    <section v-if="initialLoading" class="review-skeleton" aria-label="正在加载今日复盘" aria-busy="true">
      <span v-for="index in 4" :key="index"></span>
      <i></i>
      <i></i>
    </section>

    <section v-else class="review-metrics">
      <article><Stethoscope :size="19" /><span>完成病例数</span><strong>{{ review.completed_cases }}</strong></article>
      <article><Activity :size="19" /><span>解剖练习次数</span><strong>{{ review.anatomy_practices }}</strong></article>
      <article><BookOpenCheck :size="19" /><span>知识库检索次数</span><strong>{{ review.knowledge_searches }}</strong></article>
      <article><AlertTriangle :size="19" /><span>高风险遗漏</span><strong>{{ review.high_risk_misses.length }}</strong></article>
    </section>

    <div v-if="!initialLoading" class="daily-review-grid">
      <section class="surface-panel performance-panel">
        <div class="section-heading"><div><span class="section-kicker">今日表现分析</span><h2>六维能力画像</h2></div></div>
        <div class="performance-radar-wrap">
          <svg class="performance-radar" viewBox="0 0 100 100" role="img" aria-label="六维能力雷达图">
            <polygon v-for="(grid, index) in radarGrid" :key="index" :points="grid" class="radar-grid" />
            <line v-for="axis in radarAxes" :key="axis.key" x1="50" y1="50" :x2="axis.x" :y2="axis.y" class="radar-axis" />
            <polygon :points="radarPoints" class="radar-value" />
            <circle v-for="(axis, index) in radarAxes" :key="`point-${axis.key}`" :cx="radarPoints.split(' ')[index]?.split(',')[0]" :cy="radarPoints.split(' ')[index]?.split(',')[1]" r="1.6" class="radar-dot" />
            <text v-for="axis in radarAxes" :key="`label-${axis.key}`" :x="axis.x" :y="axis.y" class="radar-label" :text-anchor="axis.x < 43 ? 'end' : axis.x > 57 ? 'start' : 'middle'">{{ performanceLabels[axis.key] }}</text>
          </svg>
        </div>
        <div class="performance-list">
          <div v-for="(score, key) in review.performance" :key="key">
            <span><strong>{{ performanceLabels[key] }}</strong><b>{{ score }}%</b></span>
            <i><em :style="{ width: `${score}%` }"></em></i>
          </div>
        </div>
      </section>

      <section class="surface-panel weak-point-panel">
        <div class="section-heading"><div><span class="section-kicker">主要薄弱点</span><h2>点击进入复训资源</h2></div></div>
        <button v-for="point in review.weak_points" :key="point" type="button" @click="openWeakPoint(point)">
          <AlertTriangle :size="17" />
          <span><strong>{{ point }}</strong><small>病例 / 知识库 / 图谱 / 解剖训练联动</small></span>
          <ArrowRight :size="16" />
        </button>
      </section>

      <section class="surface-panel tomorrow-plan-panel">
        <div class="section-heading"><div><span class="section-kicker">明日学习建议</span><h2>复训计划</h2></div><Route :size="20" /></div>
        <ol>
          <li v-for="item in review.tomorrow_plan" :key="item">{{ item }}</li>
        </ol>
        <div class="recommendation-clusters">
          <article><strong>推荐复训病例</strong><span v-for="item in review.recommended_cases" :key="item">{{ item }}</span></article>
          <article><strong>推荐知识点</strong><span v-for="item in review.recommended_knowledge.slice(0, 5)" :key="item">{{ item }}</span></article>
          <article><strong>知识图谱路径</strong><span v-for="item in review.recommended_graph_path" :key="item">{{ item }}</span></article>
        </div>
      </section>

      <DigitalHumanWorkspace
        name="数字人复盘导师"
        description="根据复盘状态切换讲解与风险提醒"
        :subtitle="review.summary"
        :state="digitalHumanState"
        :speak-key="speakKey"
      />
    </div>

    <div v-if="!initialLoading" class="daily-review-grid lower">
      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">历史复盘</span><h2>最近 7 天</h2></div><ClipboardList :size="20" /></div>
        <div class="review-history-list">
          <article v-for="item in history" :key="item.review_id">
            <span>{{ item.date.slice(5) }}</span>
            <div><strong>{{ item.status }}</strong><small>{{ item.completed_cases }} 个病例 · 均分 {{ item.average_score }}</small></div>
            <b :class="{ risk: item.teacher_attention_required }">{{ item.teacher_attention_required ? '关注' : '完成' }}</b>
          </article>
        </div>
      </section>
      <section class="surface-panel graph-path-panel">
        <div class="section-heading"><div><span class="section-kicker">推荐知识图谱路径</span><h2>从薄弱点到结构化学习</h2></div><ChartNetwork :size="20" /></div>
        <ol>
          <li v-for="(item, index) in review.recommended_graph_path" :key="item"><span>{{ index + 1 }}</span>{{ item }}</li>
        </ol>
        <button class="button-secondary" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: review.recommended_graph_path[0] } })">打开图谱路径 <ArrowRight :size="16" /></button>
      </section>
    </div>
  </div>
</template>
