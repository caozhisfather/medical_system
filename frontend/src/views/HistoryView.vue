<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, CalendarDays, Eye, RotateCcw, Search } from '@lucide/vue';
import { trainingStore } from '../stores/training';

const router = useRouter();
const query = ref('');
const status = ref('全部状态');
const records = computed(() => trainingStore.state.history.filter((item) =>
  (!query.value || item.caseTitle.includes(query.value)) &&
  (status.value === '全部状态' || item.status === status.value)
));

function scoreTone(score: number) {
  return score >= 80 ? 'score-good' : score >= 60 ? 'score-warning' : 'score-danger';
}
</script>

<template>
  <div class="workspace-page">
    <section class="page-title-row"><div><span class="section-kicker">学习档案</span><h1>历史训练记录</h1><p>回顾每次问诊路径、评分变化和教师反馈。</p></div></section>
    <section class="filter-bar">
      <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="搜索病例名称" /></label>
      <label><CalendarDays :size="16" /><select v-model="status"><option>全部状态</option><option>待教师复核</option><option>教师已复核</option></select></label>
      <span>共 {{ records.length }} 次训练</span>
    </section>
    <section class="history-timeline">
      <article v-for="item in records" :key="item.id">
        <div class="timeline-date"><strong>{{ item.completedAt.slice(5, 10) }}</strong><small>{{ item.completedAt.slice(11) }}</small></div>
        <div class="timeline-point"></div>
        <div class="history-record">
          <div class="history-main"><span>{{ item.status }}</span><h2>{{ item.caseTitle }}</h2><p>{{ item.diagnosisPath.slice(0, 3).join(' → ') }}</p></div>
          <div class="history-score" :class="scoreTone(item.score)"><strong>{{ item.score }}</strong><small>综合评分</small></div>
          <div class="history-meta"><span>{{ item.duration }}</span><span>{{ item.improvements.length }} 项改进建议</span></div>
          <div class="history-actions"><button type="button" title="查看训练报告" @click="router.push(`/training-report/${item.id}`)"><Eye :size="16" />查看报告</button><button type="button" title="再次训练" @click="router.push({ path: '/student/case/new', query: { case: item.caseId } })"><RotateCcw :size="16" />再次训练</button></div>
        </div>
      </article>
    </section>
  </div>
</template>
