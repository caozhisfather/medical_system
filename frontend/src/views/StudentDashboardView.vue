<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, CalendarClock, CheckCircle2, Clock3, FileChartColumn, Flame, RotateCcw, Stethoscope, Target, TrendingUp } from '@lucide/vue';
import { trainingStore } from '../stores/training';

const router = useRouter();
onMounted(() => trainingStore.loadCases());
const recommended = computed(() => trainingStore.state.cases.slice(0, 3));
const history = computed(() => trainingStore.state.history.slice(0, 3));
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
        <h2>急诊胸痛 · 高危鉴别复训</h2>
        <p>最近一次训练中，主动脉夹层与肺栓塞排查顺序仍需加强。本次训练将重点检查致命性胸痛优先级。</p>
        <div class="today-task-tags"><span>高危鉴别</span><span>检查优先级</span><span>证据引用</span></div>
        <footer><button type="button" @click="router.push({ path: '/student/case/new', query: { case: 'emergency_chest_pain' } })">开始今日训练 <ArrowRight :size="18" /></button><small><Clock3 :size="15" />预计 20 分钟</small></footer>
      </article>
      <aside class="weekly-progress-card">
        <header><div><span class="section-kicker">本周进度</span><h2>还差 1 次完成目标</h2></div><strong>3<small>/4</small></strong></header>
        <div class="weekly-progress-track"><i style="width:75%"></i></div>
        <div class="weekly-progress-row"><span><CheckCircle2 :size="16" />已完成 3 次训练</span><b>75%</b></div>
        <section><span><RotateCcw :size="17" /></span><div><small>当前薄弱项</small><strong>致命性疾病鉴别</strong><p>完成今日任务后将重新计算能力画像。</p></div></section>
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

      <section class="surface-panel trend-panel">
        <div class="section-heading"><div><span class="section-kicker">近 6 次训练</span><h2>能力趋势</h2></div><b>+24%</b></div>
        <svg viewBox="0 0 520 190" role="img" aria-label="临床推理能力趋势图">
          <line v-for="y in [40, 80, 120, 160]" :key="y" x1="35" :y1="y" x2="500" :y2="y" />
          <polyline points="35,145 125,132 215,118 305,126 395,88 500,62" />
          <circle v-for="(point, index) in [[35,145],[125,132],[215,118],[305,126],[395,88],[500,62]]" :key="index" :cx="point[0]" :cy="point[1]" r="5" />
        </svg>
        <div class="trend-legend"><span><i></i>综合临床推理</span><small>问诊完整性与检查决策提升明显</small></div>
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
          <li><span>01</span><div><strong>致命性胸痛鉴别</strong><small>完成问诊要点微课</small></div></li>
          <li><span>02</span><div><strong>急诊胸痛复训</strong><small>重点覆盖夹层与肺栓塞</small></div></li>
          <li><span>03</span><div><strong>教师反馈复盘</strong><small>整理检查选择证据链</small></div></li>
        </ol>
        <button class="button-secondary learning-route-action" type="button" @click="router.push('/student/history')">查看完整学习档案 <ArrowRight :size="16" /></button>
      </section>
    </div>
  </div>
</template>
