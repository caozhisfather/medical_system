<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  Download,
  RotateCcw,
  Sparkles
} from '@lucide/vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore, type ReportDimension } from '../stores/training';

const route = useRoute();
const router = useRouter();
const teacherComment = ref('');
const report = computed(() => trainingStore.reportById(String(route.params.sessionId)));
const dimensions = computed<ReportDimension[]>(() => report.value.dimensions.length ? report.value.dimensions : [
  { label: '问诊完整性', score: report.value.score, feedback: '历史演示数据' },
  { label: '关键信息捕捉', score: report.value.score + 3, feedback: '历史演示数据' },
  { label: '鉴别诊断覆盖', score: report.value.score - 4, feedback: '历史演示数据' },
  { label: '临床推理逻辑', score: report.value.score, feedback: '历史演示数据' },
  { label: '检查处理合理性', score: report.value.score + 2, feedback: '历史演示数据' },
  { label: '医患沟通能力', score: report.value.score - 1, feedback: '历史演示数据' },
  { label: '证据引用准确率', score: report.value.score - 5, feedback: '历史演示数据' }
]);
const radarPoints = computed(() => {
  const center = 115;
  const radius = 82;
  return dimensions.value.map((item, index) => {
    const angle = -Math.PI / 2 + index * (Math.PI * 2 / dimensions.value.length);
    const r = radius * item.score / 100;
    return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
  }).join(' ');
});

function saveReview() {
  if (!teacherComment.value.trim()) return;
  report.value.teacherComment = teacherComment.value.trim();
  report.value.status = '教师已复核';
}
</script>

<template>
  <main class="report-screen">
    <header class="report-topbar">
      <button class="icon-button" type="button" title="返回" @click="router.back()"><ArrowLeft :size="19" /></button>
      <div><strong>临床思维训练报告</strong><small>{{ report.id }} · {{ report.completedAt }}</small></div>
      <SafetyNotice compact />
      <button class="button-secondary" type="button"><Download :size="16" /> 导出教学报告</button>
    </header>

    <div class="report-canvas">
      <section class="report-summary-band">
        <div><span class="section-kicker">本次训练</span><h1>{{ report.caseTitle }}</h1><p>{{ report.diagnosisPath.slice(0, 3).join(' → ') }}</p></div>
        <div class="report-total"><strong>{{ report.score }}</strong><span>综合评分</span><small>班级参考均值 82</small></div>
        <div class="report-status"><span :class="{ pending: report.status === '待教师复核' }">{{ report.status }}</span><small>{{ report.duration }}</small></div>
      </section>

      <div class="report-primary-grid">
        <section class="surface-panel radar-panel">
          <div class="section-heading"><div><span class="section-kicker">七维能力评估</span><h2>临床思维画像</h2></div><b>本次</b></div>
          <div class="radar-wrap">
            <svg viewBox="0 0 230 230" role="img" aria-label="临床思维雷达图">
              <polygon v-for="scale in [1, .75, .5, .25]" :key="scale" :points="dimensions.map((_, index) => { const a = -Math.PI / 2 + index * (Math.PI * 2 / dimensions.length); return `${115 + Math.cos(a) * 82 * scale},${115 + Math.sin(a) * 82 * scale}`; }).join(' ')" class="radar-grid" />
              <line v-for="(_, index) in dimensions" :key="index" x1="115" y1="115" :x2="115 + Math.cos(-Math.PI / 2 + index * (Math.PI * 2 / dimensions.length)) * 82" :y2="115 + Math.sin(-Math.PI / 2 + index * (Math.PI * 2 / dimensions.length)) * 82" />
              <polygon :points="radarPoints" class="radar-value" />
            </svg>
            <div class="radar-labels"><span v-for="item in dimensions" :key="item.label"><b>{{ item.score }}</b>{{ item.label }}</span></div>
          </div>
        </section>

        <section class="surface-panel dimension-panel">
          <div class="section-heading"><div><span class="section-kicker">逐项反馈</span><h2>评分明细</h2></div></div>
          <div class="dimension-list">
            <article v-for="item in dimensions" :key="item.label">
              <div><strong>{{ item.label }}</strong><b>{{ item.score }}</b></div>
              <span><i :style="{ width: `${item.score}%` }"></i></span>
              <p>{{ item.feedback }}</p>
            </article>
          </div>
        </section>
      </div>

      <div class="report-secondary-grid">
        <section class="surface-panel report-analysis">
          <div class="section-heading"><div><span class="section-kicker">错因与风险</span><h2>教学分析</h2></div></div>
          <div class="analysis-columns">
            <div><h3><CheckCircle2 :size="17" /> 做得好的地方</h3><p v-for="item in report.strengths" :key="item">{{ item }}</p></div>
            <div><h3><Sparkles :size="17" /> 需要改进</h3><p v-for="item in report.improvements" :key="item">{{ item }}</p></div>
          </div>
          <div class="high-risk-block"><AlertTriangle :size="18" /><div><strong>高风险遗漏提醒</strong><p>{{ report.highRiskMisses.join('；') || '本次未发现未处理的高风险遗漏。' }}</p></div></div>
        </section>

        <section class="surface-panel diagnosis-path">
          <div class="section-heading"><div><span class="section-kicker">过程回放</span><h2>诊断路径</h2></div></div>
          <ol><li v-for="(item, index) in report.diagnosisPath" :key="item"><span>{{ index + 1 }}</span><p>{{ item }}</p></li></ol>
        </section>
      </div>

      <div class="report-secondary-grid evidence-review-grid">
        <section class="surface-panel evidence-panel">
          <div class="section-heading"><div><span class="section-kicker">可追溯依据</span><h2>指南证据引用</h2></div><BookOpenCheck :size="20" /></div>
          <article v-for="citation in report.citations" :key="citation.id">
            <span>{{ citation.source }}</span><strong>{{ citation.title }}</strong><p>{{ citation.snippet }}</p><button type="button" @click="router.push({ path: '/knowledge-graph', query: { q: citation.title } })">查看依据 <ArrowRight :size="15" /></button>
          </article>
          <p v-if="!report.citations.length" class="empty-copy">历史记录暂未保存证据片段，建议复训时完成引用。</p>
        </section>
        <section class="surface-panel teacher-review">
          <div class="section-heading"><div><span class="section-kicker">人工监督</span><h2>教师复核意见</h2></div><ClipboardCheck :size="20" /></div>
          <blockquote v-if="report.teacherComment">{{ report.teacherComment }}</blockquote>
          <template v-else-if="trainingStore.state.profile.role === 'teacher'">
            <textarea v-model="teacherComment" rows="5" placeholder="补充教学评价、风险提醒或复训要求" />
            <button class="button-primary" type="button" @click="saveReview">提交复核意见</button>
          </template>
          <div v-else class="review-pending"><span></span><strong>等待教师复核</strong><p>人工复核会补充课程要求和个性化建议。</p></div>
        </section>
      </div>

      <section class="learning-path-band">
        <div><span class="section-kicker">推荐学习路径</span><h2>下一步训练计划</h2></div>
        <ol><li v-for="(item, index) in report.learningPath" :key="item"><span>{{ index + 1 }}</span><strong>{{ item }}</strong></li></ol>
        <button class="button-primary" type="button" @click="router.push({ path: '/student/case/new', query: { case: report.caseId } })"><RotateCcw :size="17" /> 使用本病例复训</button>
      </section>
    </div>
  </main>
</template>
