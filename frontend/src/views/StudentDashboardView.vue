<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, ArrowRight, BookOpenCheck, CalendarCheck2, CalendarClock, CheckCircle2, Clock3, FileChartColumn, Flame, RotateCcw, Stethoscope, Target, TrendingUp } from '@lucide/vue';
import { mockDailyReview } from '../data/dailyReview';
import { trainingStore } from '../stores/training';

const router = useRouter();
onMounted(() => trainingStore.loadCases());
const recommended = computed(() => trainingStore.state.cases.slice(0, 3));
const history = computed(() => trainingStore.state.history.slice(0, 3));
const latestReport = computed(() => trainingStore.lastReport.value);
const weakestDimension = computed(() => latestReport.value?.dimensions?.length ? [...latestReport.value.dimensions].sort((a, b) => a.score - b.score)[0] : null);
const focusText = computed(() => weakestDimension.value?.label || latestReport.value?.learningPath?.[0] || '致命性疾病鉴别');
const focusDescription = computed(() => weakestDimension.value ? `${weakestDimension.value.feedback} 建议通过专项病例复训巩固。` : '完成今日任务后将重新计算能力画像。');
const previousSameCase = computed(() => latestReport.value ? trainingStore.state.history.slice(1).find((item) => item.caseId === latestReport.value.caseId) ?? null : null);
const latestScoreDelta = computed(() => previousSameCase.value && latestReport.value ? latestReport.value.score - previousSameCase.value.score : null);
</script>

<template>
  <div class="workspace-page student-dashboard-page">
    <header class="student-dashboard-heading">
      <div><span class="section-kicker">学习总览</span><h1>{{ trainingStore.state.profile.name }}，今天继续完成临床训练</h1><p>系统已根据最近训练表现，整理出今天最值得优先完成的任务。</p></div>
      <span class="dashboard-streak"><Flame :size="18" /><b>连续第 4 周</b><small>保持稳定训练节奏</small></span>
    </header>

    <section class="dashboard-focus-grid">
      <article class="today-training-card">
        <div class="today-task-head"><span><Target :size="17" />今日优先任务</span><small>AI 学情推荐</small></div>
        <h2>{{ latestReport?.caseTitle || '急诊胸痛' }} · {{ focusText }}复训</h2>
        <p>{{ focusDescription }}</p>
        <div class="today-task-tags"><span>高危鉴别</span><span>检查优先级</span><span>证据引用</span></div>
        <footer><button type="button" @click="router.push({ path: '/student/case/new', query: { case: latestReport?.caseId || 'emergency_chest_pain', focus: focusText } })">开始今日训练 <ArrowRight :size="18" /></button><small><Clock3 :size="15" />预计 20 分钟</small></footer>
      </article>
      <aside class="weekly-progress-card">
        <header><div><span class="section-kicker">本周进度</span><h2>还差 1 次完成目标</h2></div><strong>3<small>/4</small></strong></header>
        <div class="weekly-progress-track"><i style="width:75%"></i></div>
        <div class="weekly-progress-row"><span><CheckCircle2 :size="16" />已完成 3 次训练</span><b>75%</b></div>
        <section><span><RotateCcw :size="17" /></span><div><small>{{ previousSameCase ? '最近复训成效' : '当前薄弱项' }}</small><strong>{{ previousSameCase ? `${latestScoreDelta! >= 0 ? '+' : ''}${latestScoreDelta} 分` : focusText }}</strong><p>{{ previousSameCase ? `同病例较上次${latestScoreDelta! >= 0 ? '提升' : '下降'}，下一步继续巩固“${focusText}”。` : focusDescription }}</p></div></section>
        <button v-if="history[0]" type="button" @click="router.push(`/training-report/${history[0].id}`)">查看上次训练反馈 <ArrowRight :size="16" /></button>
      </aside>
    </section>

    <section class="metric-strip">
      <article><Stethoscope :size="19" /><span><small>累计训练</small><strong>18 次</strong></span><b>本月 +5</b></article>
      <article><FileChartColumn :size="19" /><span><small>平均得分</small><strong>82.6</strong></span><b>提升 6.4</b></article>
      <article><TrendingUp :size="19" /><span><small>近月提升</small><strong>+6.4 分</strong></span><b>趋势稳定</b></article>
      <article><BookOpenCheck :size="19" /><span><small>证据引用率</small><strong>84%</strong></span><b>提升 9%</b></article>
    </section>

    <div class="dashboard-main-grid">
      <section class="surface-section">
        <div class="section-heading">
          <div><span class="section-kicker">个性化推荐</span><h2>下一组病例</h2></div>
          <button class="text-button" type="button" @click="router.push('/student/cases')">查看病例库 <ArrowRight :size="16" /></button>
        </div>
        <div class="recommended-cases">
          <button v-for="(item, index) in recommended" :key="item.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: item.id } })">
            <span class="case-index">0{{ index + 1 }}</span>
            <span class="case-accent" :class="`accent-${index + 1}`"></span>
            <span class="case-copy"><small>{{ item.department }} · {{ item.difficulty }}</small><strong>{{ item.title }}</strong><p>{{ item.chief_complaint }}</p></span>
            <ArrowRight :size="18" />
          </button>
        </div>
      </section>

      <section class="surface-panel daily-review-snapshot" data-tour="daily-review">
        <div class="section-heading"><div><span class="section-kicker">今日复盘</span><h2>AI 导师总结</h2></div><CalendarCheck2 :size="20" /></div>
        <p>{{ mockDailyReview.summary }}</p>
        <div class="weak-chip-row">
          <span v-for="item in mockDailyReview.weak_points" :key="item"><AlertTriangle :size="14" />{{ item }}</span>
        </div>
        <button class="button-secondary" type="button" @click="router.push('/student/daily-review')">查看完整复盘与明日计划 <ArrowRight :size="16" /></button>
      </section>
    </div>

    <div class="dashboard-lower-grid dashboard-review-grid">
      <section class="surface-panel">
        <div class="section-heading"><div><span class="section-kicker">最近活动</span><h2>训练记录</h2></div><CalendarClock :size="20" /></div>
        <div class="activity-list">
          <button v-for="item in history" :key="item.id" type="button" @click="router.push(`/training-report/${item.id}`)">
            <span class="score-orbit">{{ item.score }}</span>
            <span><strong>{{ item.caseTitle }}</strong><small>{{ item.completedAt }} · {{ item.duration }}</small></span>
            <b :class="{ pending: item.status === '待教师复核' }">{{ item.status }}</b>
          </button>
        </div>
      </section>
      <section class="surface-panel learning-route">
        <div class="section-heading"><div><span class="section-kicker">本周学习路径</span><h2>从薄弱点到复训</h2></div></div>
        <ol>
          <li><span>01</span><div><strong>{{ focusText }}</strong><small>完成针对性复训</small></div></li>
          <li><span>02</span><div><strong>{{ latestReport?.caseTitle || '急诊胸痛' }}复训</strong><small>重点覆盖最近一次报告的薄弱项</small></div></li>
          <li><span>03</span><div><strong>教师反馈复盘</strong><small>整理检查选择证据链</small></div></li>
        </ol>
        <button class="button-secondary learning-route-action" type="button" @click="router.push('/student/history')">查看完整学习档案 <ArrowRight :size="16" /></button>
      </section>
    </div>
  </div>
</template>
