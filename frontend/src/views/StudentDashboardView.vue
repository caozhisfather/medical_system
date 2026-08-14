<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, ArrowRight, BookOpenCheck, CalendarCheck2, CalendarClock, FileChartColumn, Route, Stethoscope, Target } from '@lucide/vue';
import mainWorkbenchImage from '../assets/medical/main-workbench.png';
import DigitalHumanWorkspace from '../components/DigitalHumanWorkspace.vue';
import { mockDailyReview } from '../data/dailyReview';
import { trainingStore } from '../stores/training';

const router = useRouter();
onMounted(() => trainingStore.loadCases());
const recommended = computed(() => trainingStore.state.cases.slice(0, 3));
const history = computed(() => trainingStore.state.history.slice(0, 3));
</script>

<template>
  <div class="workspace-page student-home-page">
    <section class="dashboard-hero" data-tour="today-task">
      <img :src="mainWorkbenchImage" alt="" />
      <div class="dashboard-hero-copy">
        <span class="section-kicker">今日学习任务</span>
        <h1>{{ trainingStore.state.profile.name }}，继续完善你的临床思维链</h1>
        <p>今天的主线是：完成推荐病例，补齐高风险鉴别，查看 AI 复盘，再进入明日计划。</p>
        <div class="hero-action-row">
          <button class="button-primary" type="button" @click="router.push({ path: '/student/case/new', query: { case: 'emergency_chest_pain' } })">
            开始急诊胸痛训练 <ArrowRight :size="18" />
          </button>
          <button class="button-secondary" type="button" @click="router.push('/student/daily-review')"><CalendarCheck2 :size="17" /> 查看每日复盘</button>
        </div>
      </div>
      <div class="hero-progress">
        <strong>4</strong><span>连续训练周</span>
        <div><i style="width: 72%"></i></div>
        <small>本周目标 3 / 4 次</small>
      </div>
    </section>

    <section class="metric-strip">
      <article><Stethoscope :size="19" /><span><small>累计训练</small><strong>18 次</strong></span><b>本月 +5</b></article>
      <article><FileChartColumn :size="19" /><span><small>平均得分</small><strong>82.6</strong></span><b>提升 6.4</b></article>
      <article><Target :size="19" /><span><small>当前薄弱项</small><strong>高危鉴别</strong></span><b>需复训</b></article>
      <article data-tour="evidence"><BookOpenCheck :size="19" /><span><small>证据引用率</small><strong>84%</strong></span><b>提升 9%</b></article>
    </section>

    <section class="learning-loop-band">
      <article><span>学习任务</span><strong>推荐胸痛与腹痛复训</strong></article>
      <i></i>
      <article><span>AI 训练</span><strong>标准化病人问诊与检查选择</strong></article>
      <i></i>
      <article><span>反馈复盘</span><strong>今日均分 {{ mockDailyReview.average_score }} · {{ mockDailyReview.status }}</strong></article>
      <i></i>
      <article><span>明日计划</span><strong>{{ mockDailyReview.recommended_graph_path.slice(0, 2).join(' / ') }}</strong></article>
    </section>

    <div class="dashboard-main-grid">
      <section class="surface-section" data-tour="case-training">
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
        <button class="button-secondary" type="button" @click="router.push('/student/daily-review')">查看明日计划 <ArrowRight :size="16" /></button>
      </section>
    </div>

    <div class="dashboard-lower-grid">
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
        <div class="section-heading"><div><span class="section-kicker">推荐路径</span><h2>从薄弱点到复训</h2></div><Route :size="20" /></div>
        <ol>
          <li v-for="(item, index) in mockDailyReview.recommended_graph_path.slice(0, 4)" :key="item"><span>{{ String(index + 1).padStart(2, '0') }}</span><div><strong>{{ item }}</strong><small>{{ index === 0 ? '从今日薄弱点进入' : '与病例训练联动' }}</small></div></li>
        </ol>
      </section>
      <DigitalHumanWorkspace
        compact
        data-tour="digital-human"
        name="智能临床导师"
        description="陪你规划下一次病例训练与报告复盘"
        :subtitle="mockDailyReview.summary"
        state="reviewing"
      />
    </div>
  </div>
</template>