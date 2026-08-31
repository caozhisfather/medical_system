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
        <div class="demo-flow-hint"><span>完整演示链路</span><b>病例问诊</b><i>→</i><b>检查决策</b><i>→</i><b>解剖/图谱</b><i>→</i><b>六维复盘</b></div>
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

    <section class="dashboard-card-grid dashboard-loop-cards" aria-label="学习闭环">
      <details class="dashboard-fold-card" open><summary><span class="fold-icon"><Target :size="17" /></span><span><small>学习任务</small><strong>推荐胸痛与腹痛复训</strong></span><i>展开</i></summary><p>从今日薄弱项进入针对性病例训练，优先处理高风险鉴别。</p><button class="text-button" type="button" @click="router.push('/student/cases')">进入病例库 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card"><summary><span class="fold-icon"><Stethoscope :size="17" /></span><span><small>AI 训练</small><strong>标准化病人问诊与检查选择</strong></span><i>展开</i></summary><p>在虚拟病例中完成问诊、鉴别诊断、检查和教学用药决策。</p><button class="text-button" type="button" @click="router.push({ path: '/student/case/new', query: { case: 'emergency_chest_pain' } })">开始训练 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card" data-tour="daily-review"><summary><span class="fold-icon"><CalendarCheck2 :size="17" /></span><span><small>反馈复盘</small><strong>今日均分 {{ mockDailyReview.average_score }} · {{ mockDailyReview.status }}</strong></span><i>展开</i></summary><p>{{ mockDailyReview.summary }}</p><button class="text-button" type="button" @click="router.push('/student/daily-review')">查看每日复盘 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card"><summary><span class="fold-icon"><Route :size="17" /></span><span><small>明日计划</small><strong>{{ mockDailyReview.recommended_graph_path.slice(0, 2).join(' / ') }}</strong></span><i>展开</i></summary><p>系统会根据病例表现、解剖训练和证据引用结果持续调整学习路径。</p><button class="text-button" type="button" @click="router.push('/student/daily-review')">查看计划 <ArrowRight :size="15" /></button></details>
    </section>

    <div class="dashboard-card-grid dashboard-content-cards">
      <details class="dashboard-fold-card dashboard-wide-card" data-tour="case-training" open>
        <summary><span class="fold-icon"><BookOpenCheck :size="17" /></span><span><small>个性化推荐</small><strong>下一组病例</strong></span><i>展开</i></summary>
        <div class="fold-card-actions"><button class="text-button" type="button" @click="router.push('/student/cases')">查看病例库 <ArrowRight :size="16" /></button></div>
        <div class="recommended-cases">
          <button v-for="(item, index) in recommended" :key="item.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: item.id } })">
            <span class="case-index">0{{ index + 1 }}</span><span class="case-accent" :class="`accent-${index + 1}`"></span><span class="case-copy"><small>{{ item.department }} · {{ item.difficulty }}</small><strong>{{ item.title }}</strong><p>{{ item.chief_complaint }}</p></span><ArrowRight :size="18" />
          </button>
        </div>
      </details>

      <details class="dashboard-fold-card">
        <summary><span class="fold-icon"><CalendarClock :size="17" /></span><span><small>最近活动</small><strong>训练记录</strong></span><i>展开</i></summary>
        <div class="activity-list">
          <button v-for="item in history" :key="item.id" type="button" @click="router.push(`/training-report/${item.id}`)"><span class="score-orbit">{{ item.score }}</span><span><strong>{{ item.caseTitle }}</strong><small>{{ item.completedAt }} · {{ item.duration }}</small></span><b :class="{ pending: item.status === '待教师复核' }">{{ item.status }}</b></button>
        </div>
      </details>

      <details class="dashboard-fold-card">
        <summary><span class="fold-icon"><Route :size="17" /></span><span><small>推荐路径</small><strong>从薄弱点到复训</strong></span><i>展开</i></summary>
        <ol class="learning-route-list"><li v-for="(item, index) in mockDailyReview.recommended_graph_path.slice(0, 4)" :key="item"><span>{{ String(index + 1).padStart(2, '0') }}</span><div><strong>{{ item }}</strong><small>{{ index === 0 ? '从今日薄弱点进入' : '与病例训练联动' }}</small></div></li></ol>
      </details>

      <details class="dashboard-fold-card dashboard-wide-card">
        <summary><span class="fold-icon"><Stethoscope :size="17" /></span><span><small>数字人导师</small><strong>智能临床导师复盘</strong></span><i>展开</i></summary>
        <DigitalHumanWorkspace compact data-tour="digital-human" name="智能临床导师" description="陪你规划下一次病例训练与报告复盘" :subtitle="mockDailyReview.summary" state="reviewing" />
      </details>
    </div>
  </div>
</template>
