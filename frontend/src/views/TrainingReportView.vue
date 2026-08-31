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
  MessageSquareText,
  Pill,
  RotateCcw,
  Sparkles,
  TrendingUp
} from '@lucide/vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore, type ReportDimension } from '../stores/training';

const route = useRoute();
const router = useRouter();
const teacherComment = ref('');
const activeStep = ref(0);
const reportSteps = [
  { label: '多维能力评估', target: 'report-step-assessment' },
  { label: '逐项反馈', target: 'report-step-feedback' },
  { label: '错因与风险', target: 'report-step-risk' },
  { label: '过程回放', target: 'report-step-replay' },
  { label: '学生提交', target: 'report-step-submission' },
  { label: '可追溯依据', target: 'report-step-evidence' },
  { label: '人工监督', target: 'report-step-supervision' }
];
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
const priorityDimensions = computed(() => dimensions.value.filter((item) => item.score < 80).sort((a, b) => a.score - b.score));
const retrainingCaseId = computed(() => report.value.caseId || 'emergency_chest_pain');
const previousReport = computed(() => {
  const currentIndex = trainingStore.state.history.findIndex((item) => item.id === report.value.id);
  if (currentIndex < 0) return null;
  return trainingStore.state.history.slice(currentIndex + 1).find((item) => item.caseId === report.value.caseId) ?? null;
});
const scoreDelta = computed(() => previousReport.value ? report.value.score - previousReport.value.score : 0);
const dimensionComparisons = computed(() => dimensions.value.map((item) => {
  const previous = previousReport.value?.dimensions.find((candidate) => candidate.label === item.label);
  return { ...item, previousScore: previous?.score, delta: previous ? item.score - previous.score : null };
}));
const repeatedProblems = computed(() => previousReport.value ? report.value.improvements.filter((item) => previousReport.value?.improvements.includes(item)) : []);
const resolvedProblems = computed(() => previousReport.value ? previousReport.value.improvements.filter((item) => !report.value.improvements.includes(item)) : []);
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

function goToStep(index: number) {
  const ordered = reportSteps.map((step, stepIndex) => ({ ...step, stepIndex })).filter((step) => document.getElementById(step.target));
  const target = ordered.find((step) => step.stepIndex === index) || ordered.find((step) => step.stepIndex > index) || ordered[ordered.length - 1];
  if (!target) return;
  activeStep.value = target.stepIndex;
  document.getElementById(target.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
        <div><span class="section-kicker">本次训练</span><h1>{{ report.caseTitle }}</h1><p>{{ report.diagnosisPath.slice(0, 3).join(' → ') }}</p><small v-if="report.assessmentSource">{{ report.assessmentSource === 'backend-ai' ? '后台 ScoringAgent 已完成评估' : '后端不可用，本次采用离线评分' }}</small></div>
        <div class="report-total"><strong>{{ report.score }}</strong><span>综合评分</span><small>班级参考均值 82</small></div>
        <div class="report-status"><span :class="{ pending: report.status === '待教师复核' }">{{ report.status }}</span><small>{{ report.duration }}</small></div>
      </section>

      <nav class="report-step-nav" aria-label="报告分析流程">
        <button v-for="(step, index) in reportSteps" :key="step.target" type="button" :class="{ active: activeStep === index }" :aria-current="activeStep === index ? 'step' : undefined" @click="goToStep(index)">
          <span>{{ index + 1 }}</span><strong>{{ step.label }}</strong><ArrowRight v-if="index < reportSteps.length - 1" :size="14" />
        </button>
      </nav>

      <section class="surface-panel retraining-comparison">
        <div class="section-heading"><div><span class="section-kicker">同病例复训追踪</span><h2>本次与上次表现对比</h2></div><TrendingUp :size="20" /></div>
        <template v-if="previousReport">
          <div class="comparison-summary">
            <article><small>上次得分</small><strong>{{ previousReport.score }}</strong><span>{{ previousReport.completedAt }}</span></article>
            <article :class="{ improved: scoreDelta > 0, declined: scoreDelta < 0 }"><small>本次变化</small><strong>{{ scoreDelta > 0 ? '+' : '' }}{{ scoreDelta }}</strong><span>{{ scoreDelta > 0 ? '复训后提升' : scoreDelta < 0 ? '需要继续巩固' : '与上次持平' }}</span></article>
            <article><small>已改善问题</small><strong>{{ resolvedProblems.length }}</strong><span>上次问题本次未再出现</span></article>
            <article><small>重复问题</small><strong>{{ repeatedProblems.length }}</strong><span>建议列为下一次专项重点</span></article>
          </div>
          <div class="comparison-dimensions">
            <article v-for="item in dimensionComparisons.filter((entry) => entry.previousScore !== undefined)" :key="item.label">
              <span><strong>{{ item.label }}</strong><small>上次 {{ item.previousScore }} → 本次 {{ item.score }}</small></span>
              <b :class="{ up: (item.delta ?? 0) > 0, down: (item.delta ?? 0) < 0 }">{{ (item.delta ?? 0) > 0 ? '+' : '' }}{{ item.delta }}</b>
            </article>
          </div>
          <div v-if="repeatedProblems.length" class="comparison-warning"><AlertTriangle :size="17" /><span><strong>仍重复出现</strong><small>{{ repeatedProblems.join('；') }}</small></span></div>
        </template>
        <div v-else class="comparison-empty"><RotateCcw :size="22" /><div><strong>这是该病例的首次训练记录</strong><p>完成一次同病例复训后，系统会自动展示分数变化、能力提升和重复问题。</p></div><button class="button-secondary" type="button" @click="router.push({ path: '/student/case/new', query: { case: retrainingCaseId, focus: priorityDimensions[0]?.label || report.learningPath[0] } })">开始首次复训 <ArrowRight :size="16" /></button></div>
      </section>

      <div class="report-primary-grid">
        <section id="report-step-assessment" class="surface-panel radar-panel">
          <div class="section-heading"><div><span class="section-kicker">多维能力评估</span><h2>临床思维画像</h2></div><b>本次</b></div>
          <div class="radar-wrap">
            <svg viewBox="0 0 230 230" role="img" aria-label="临床思维雷达图">
              <polygon v-for="scale in [1, .75, .5, .25]" :key="scale" :points="dimensions.map((_, index) => { const a = -Math.PI / 2 + index * (Math.PI * 2 / dimensions.length); return `${115 + Math.cos(a) * 82 * scale},${115 + Math.sin(a) * 82 * scale}`; }).join(' ')" class="radar-grid" />
              <line v-for="(_, index) in dimensions" :key="index" x1="115" y1="115" :x2="115 + Math.cos(-Math.PI / 2 + index * (Math.PI * 2 / dimensions.length)) * 82" :y2="115 + Math.sin(-Math.PI / 2 + index * (Math.PI * 2 / dimensions.length)) * 82" />
              <polygon :points="radarPoints" class="radar-value" />
            </svg>
            <div class="radar-labels"><span v-for="item in dimensions" :key="item.label"><b>{{ item.score }}</b>{{ item.label }}</span></div>
          </div>
        </section>

        <section id="report-step-feedback" class="surface-panel dimension-panel">
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
        <section id="report-step-risk" class="surface-panel report-analysis">
          <div class="section-heading"><div><span class="section-kicker">错因与风险</span><h2>教学分析</h2></div></div>
          <div class="analysis-columns">
            <div><h3><CheckCircle2 :size="17" /> 做得好的地方</h3><p v-for="item in report.strengths" :key="item">{{ item }}</p></div>
            <div><h3><Sparkles :size="17" /> 需要改进</h3><p v-for="item in report.improvements" :key="item">{{ item }}</p></div>
          </div>
          <div class="high-risk-block"><AlertTriangle :size="18" /><div><strong>高风险遗漏提醒</strong><p>{{ report.highRiskMisses.join('；') || '本次未发现未处理的高风险遗漏。' }}</p></div></div>
        </section>

        <section id="report-step-replay" class="surface-panel diagnosis-path">
          <div class="section-heading"><div><span class="section-kicker">过程回放</span><h2>诊断路径</h2></div></div>
          <ol><li v-for="(item, index) in report.diagnosisPath" :key="item"><span>{{ index + 1 }}</span><p>{{ item }}</p></li></ol>
        </section>
      </div>

      <div v-if="report.clinicalDecision || report.transcript?.length" class="report-secondary-grid clinical-review-grid">
        <section v-if="report.clinicalDecision" id="report-step-submission" class="surface-panel decision-review">
          <div class="section-heading"><div><span class="section-kicker">学生提交</span><h2>诊疗决策回放</h2></div><Pill :size="20" /></div>
          <dl>
            <div><dt>初步诊断</dt><dd>{{ report.clinicalDecision.diagnosis }}</dd></div>
            <div><dt>鉴别诊断</dt><dd>{{ report.clinicalDecision.differentials }}</dd></div>
            <div><dt>检查依据</dt><dd>{{ report.clinicalDecision.examinations }}</dd></div>
            <div><dt>处理原则</dt><dd>{{ report.clinicalDecision.treatment }}</dd></div>
            <div class="medication-row"><dt>教学用药</dt><dd>{{ report.clinicalDecision.medicationPlan }}</dd></div>
            <div><dt>指南证据</dt><dd>{{ report.clinicalDecision.evidence }}</dd></div>
          </dl>
        </section>
        <section v-if="report.transcript?.length" class="surface-panel transcript-review">
          <div class="section-heading"><div><span class="section-kicker">完整过程</span><h2>AI 病人对话记录</h2></div><MessageSquareText :size="20" /></div>
          <div class="transcript-list">
            <article v-for="(message, index) in report.transcript" :key="index" :class="`transcript-${message.role}`">
              <span>{{ message.role === 'student' ? '医学生' : message.role === 'patient' ? 'AI 标准化病人' : '智能导师' }}</span><p>{{ message.content }}</p>
            </article>
          </div>
        </section>
      </div>

      <div class="report-secondary-grid evidence-review-grid">
        <section id="report-step-evidence" class="surface-panel evidence-panel">
          <div class="section-heading"><div><span class="section-kicker">可追溯依据</span><h2>指南证据引用</h2></div><BookOpenCheck :size="20" /></div>
          <article v-for="citation in report.citations" :key="citation.id">
            <span>{{ citation.source }}</span><strong>{{ citation.title }}</strong><p>{{ citation.snippet }}</p><button type="button" @click="router.push({ path: '/knowledge-graph', query: { q: citation.title } })">查看依据 <ArrowRight :size="15" /></button>
          </article>
          <p v-if="!report.citations.length" class="empty-copy">历史记录暂未保存证据片段，建议复训时完成引用。</p>
        </section>
        <section id="report-step-supervision" class="surface-panel teacher-review">
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
        <p v-if="priorityDimensions.length" class="learning-path-note">AI 根据 {{ priorityDimensions.length }} 项低于 80 分的能力生成复训重点，建议先处理“{{ priorityDimensions[0].label }}”。</p>
        <ol><li v-for="(item, index) in report.learningPath" :key="item"><span>{{ index + 1 }}</span><strong>{{ item }}</strong><button type="button" title="按此主题复训" @click="router.push({ path: '/student/case/new', query: { case: retrainingCaseId, focus: item } })"><RotateCcw :size="15" />专项复训</button></li></ol>
        <button class="button-primary" type="button" @click="router.push({ path: '/student/case/new', query: { case: retrainingCaseId, focus: priorityDimensions[0]?.label || report.learningPath[0] } })"><RotateCcw :size="17" /> 使用本病例复训</button>
      </section>
    </div>
  </main>
</template>

<style scoped>
.report-step-nav {
  position: sticky;
  top: 0;
  z-index: 8;
  display: flex;
  align-items: center;
  gap: 0;
  margin: 14px 0 18px;
  padding: 8px 10px;
  overflow-x: auto;
  border: 1px solid var(--line, #dce8e7);
  border-radius: 8px;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 8px 22px rgba(20, 58, 67, .08);
  scrollbar-width: thin;
}
.report-step-nav button {
  display: inline-flex;
  flex: 1 0 auto;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 9px;
  border: 0;
  background: transparent;
  color: #6b8086;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}
.report-step-nav button span {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #edf3f2;
  color: #648078;
  font-size: 11px;
}
.report-step-nav button svg { flex: 0 0 auto; color: #b3c4c3; }
.report-step-nav button.active { color: #146b5b; }
.report-step-nav button.active span { background: #dff4ed; color: #08745f; box-shadow: 0 0 0 3px rgba(36, 155, 125, .1); }
.report-step-nav button:hover { color: #146b5b; }
.report-step-nav button:focus-visible { outline: 2px solid #5db9a4; outline-offset: 2px; border-radius: 5px; }
[id^='report-step-'] { scroll-margin-top: 74px; }
@media (max-width: 760px) {
  .report-step-nav { margin-right: -2px; margin-left: -2px; }
  .report-step-nav button { flex: 0 0 auto; }
}
</style>
