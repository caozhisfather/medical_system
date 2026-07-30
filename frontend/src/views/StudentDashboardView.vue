<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, CalendarClock, FileChartColumn, Stethoscope, Target } from '@lucide/vue';
import mainWorkbenchImage from '../assets/medical/main-workbench.png';
import DigitalHumanWorkspace from '../components/DigitalHumanWorkspace.vue';
import { trainingStore } from '../stores/training';

const router = useRouter();
onMounted(() => trainingStore.loadCases());
const recommended = computed(() => trainingStore.state.cases.slice(0, 3));
const history = computed(() => trainingStore.state.history.slice(0, 3));
</script>

<template>
  <div class="workspace-page">
    <section class="dashboard-hero">
      <img :src="mainWorkbenchImage" alt="" />
      <div class="dashboard-hero-copy">
        <span class="section-kicker">今日学习任务</span>
        <h1>{{ trainingStore.state.profile.name }}，继续完善你的临床思维链</h1>
        <p>根据最近训练，建议优先强化高危鉴别和指南证据引用。</p>
        <button class="button-primary" type="button" @click="router.push({ path: '/student/case/new', query: { case: 'emergency_chest_pain' } })">
          开始急诊胸痛训练 <ArrowRight :size="18" />
        </button>
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
        <div class="section-heading"><div><span class="section-kicker">本周学习路径</span><h2>从薄弱点到复训</h2></div></div>
        <ol>
          <li><span>01</span><div><strong>致命性胸痛鉴别</strong><small>完成问诊要点微课</small></div></li>
          <li><span>02</span><div><strong>急诊胸痛复训</strong><small>重点覆盖夹层与肺栓塞</small></div></li>
          <li><span>03</span><div><strong>教师反馈复盘</strong><small>整理检查选择证据链</small></div></li>
        </ol>
      </section>
      <DigitalHumanWorkspace
        compact
        name="智能临床导师"
        description="陪你规划下一次病例训练与报告复盘"
        subtitle="今天建议先复训急诊胸痛，重点提前排除主动脉夹层和肺栓塞。"
        state="idle"
      />
    </div>
  </div>
</template>
