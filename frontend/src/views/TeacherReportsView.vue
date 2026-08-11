<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, CheckCircle2, Filter, Search, Users } from '@lucide/vue';
import { trainingStore } from '../stores/training';

const router = useRouter();
const tab = ref('待复核');
const query = ref('');
const allReports = computed(() => [
  ...trainingStore.state.history,
  { ...trainingStore.state.history[0], id: 'TR-CLASS-01', caseTitle: '发热待查', score: 69, status: '待教师复核' as const, completedAt: '2026-07-28 16:50' },
  { ...trainingStore.state.history[1], id: 'TR-CLASS-02', caseTitle: '急性腹痛', score: 78, status: '待教师复核' as const, completedAt: '2026-07-28 15:18' }
]);
const filtered = computed(() => allReports.value.filter((item) =>
  (!query.value || item.caseTitle.includes(query.value)) &&
  (tab.value === '全部' || (tab.value === '待复核' ? item.status === '待教师复核' : item.status === '教师已复核'))
));
</script>

<template>
  <div class="workspace-page">
    <section class="page-title-row"><div><span class="section-kicker">人工监督与教学闭环</span><h1>学生报告复核</h1><p>复核 AI 过程评分、风险遗漏和证据引用，并形成班级教学分析。</p></div></section>
    <section class="review-summary">
      <article><span>待复核</span><strong>6</strong><small>预计 48 分钟</small></article>
      <article><span>今日已复核</span><strong>12</strong><small>较昨日 +3</small></article>
      <article><span>需教学干预</span><strong>4</strong><small>涉及 3 个薄弱项</small></article>
      <article><span>教师一致率</span><strong>91%</strong><small>AI 评分参考</small></article>
    </section>
    <div class="review-tabs">
      <button v-for="item in ['待复核', '已复核', '全部']" :key="item" type="button" :class="{ active: tab === item }" @click="tab = item">{{ item }}</button>
      <label class="search-control"><Search :size="16" /><input v-model="query" placeholder="搜索病例或学生" /></label>
      <button class="icon-button" type="button" title="筛选"><Filter :size="17" /></button>
    </div>
    <section class="report-review-table">
      <header><span>学生与病例</span><span>完成时间</span><span>综合分</span><span>主要薄弱项</span><span>状态</span><span></span></header>
      <article v-for="(item, index) in filtered" :key="item.id">
        <div class="student-cell"><span>{{ ['陈', '林', '周', '许'][index % 4] }}</span><div><strong>{{ ['陈同学', '林同学', '周同学', '许同学'][index % 4] }}</strong><small>{{ item.caseTitle }}</small></div></div>
        <span>{{ item.completedAt }}</span>
        <strong :class="{ low: item.score < 75 }">{{ item.score }}</strong>
        <span>{{ item.improvements[0] ?? '证据引用需要完善' }}</span>
        <b :class="{ reviewed: item.status === '教师已复核' }">{{ item.status === '教师已复核' ? '已复核' : '待复核' }}</b>
        <button type="button" title="打开报告" @click="router.push(`/training-report/${item.id}`)"><ArrowRight :size="18" /></button>
      </article>
    </section>
    <section class="class-analysis-band">
      <div><Users :size="22" /><span><strong>班级薄弱项聚合</strong><small>基于最近 248 次训练记录</small></span></div>
      <p><b>34%</b> 未完成致命性胸痛鉴别</p><p><b>29%</b> 检查优先级不合理</p><p><b>18%</b> 指南引用与结论不匹配</p>
      <button class="button-secondary" type="button" @click="router.push('/teacher/dashboard')">查看教学趋势 <CheckCircle2 :size="16" /></button>
    </section>
  </div>
</template>
