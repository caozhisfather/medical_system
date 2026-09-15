<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { AlertTriangle, ArrowRight, BarChart3, ClipboardCheck, Lightbulb, Users } from '@lucide/vue';
import { getClassDailyReview } from '../api';
import { mockClassReview } from '../data/dailyReview';
import type { DailyReviewClassSummary } from '../types';
import TeacherReportsView from './TeacherReportsView.vue';

const classReview = ref<DailyReviewClassSummary>(mockClassReview);
const route = useRoute();
const activeTab = ref<'review' | 'reports'>(route.query.tab === 'reports' ? 'reports' : 'review');

onMounted(async () => {
  try {
    classReview.value = await getClassDailyReview();
  } catch {
    classReview.value = mockClassReview;
  }
});
</script>

<template>
  <div class="workspace-page class-review-page">
    <section class="page-title-row class-review-heading" data-tour="class-review">
      <div>
        <span class="section-kicker">教学复盘 · 班级复盘与报告复核</span>
        <h1>从个体复盘汇总到明日教学干预</h1>
        <p>{{ classReview.summary }}</p>
      </div>
      <nav class="review-page-tabs" aria-label="教学复盘视图">
        <button type="button" :class="{ active: activeTab === 'review' }" @click="activeTab = 'review'"><ClipboardCheck :size="17" />班级复盘</button>
        <button type="button" :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'"><Users :size="17" />报告复核</button>
      </nav>
    </section>

    <template v-if="activeTab === 'review'">
    <section class="metric-strip teacher-metrics">
      <article><Users :size="19" /><span><small>完成训练学生</small><strong>{{ classReview.trained_students }} 名</strong></span><b>今日</b></article>
      <article><ClipboardCheck :size="19" /><span><small>复盘完成率</small><strong>{{ classReview.review_completion_rate }}%</strong></span><b>自动生成</b></article>
      <article><BarChart3 :size="19" /><span><small>班级平均分</small><strong>{{ classReview.average_score }}</strong></span><b>较上周 +3.6</b></article>
      <article><AlertTriangle :size="19" /><span><small>高风险类型</small><strong>{{ classReview.high_risk_rankings.length }}</strong></span><b>需讲评</b></article>
    </section>

    <div class="teacher-dashboard-grid">
      <section class="surface-panel class-risk-board">
        <div class="section-heading"><div><span class="section-kicker">高风险遗漏排行榜</span><h2>需要课堂复盘的问题</h2></div></div>
        <article v-for="item in classReview.high_risk_rankings" :key="item.label" :class="item.level">
          <span>{{ item.count }}</span>
          <div><strong>{{ item.label }}</strong><small>{{ item.level === 'danger' ? '连续出现时建议教师干预' : '纳入明日课堂讲评' }}</small></div>
          <i :style="{ width: `${Math.min(94, item.count * 5)}%` }"></i>
        </article>
      </section>

      <section class="surface-panel class-common-panel">
        <div class="section-heading"><div><span class="section-kicker">班级共性薄弱点</span><h2>群体分析</h2></div></div>
        <button v-for="item in classReview.common_weak_points" :key="item" type="button">
          <Lightbulb :size="17" />
          <span>{{ item }}</span>
          <ArrowRight :size="16" />
        </button>
      </section>
    </div>

    <div class="teacher-dashboard-grid lower">
      <section class="surface-panel intervention-list">
        <div class="section-heading"><div><span class="section-kicker">学生预警</span><h2>需要教师关注</h2></div></div>
        <article v-for="student in classReview.attention_students" :key="student.student_id">
          <span>{{ student.name.slice(-1) }}</span>
          <div><strong>{{ student.name }}</strong><small>{{ student.reason }}</small></div>
          <b>{{ student.average_score }}</b>
          <button type="button">复核</button>
        </article>
      </section>
      <section class="surface-panel teaching-advice">
        <div class="section-heading"><div><span class="section-kicker">AI 生成明日教学建议</span><h2>讲评安排</h2></div></div>
        <ol><li v-for="(item, index) in classReview.teaching_suggestions" :key="item"><span>{{ index + 1 }}</span><p>{{ item }}</p></li></ol>
      </section>
    </div>
    </template>

    <TeacherReportsView v-else />
  </div>
</template>

<style scoped>
.review-page-tabs { display: flex; gap: 6px; padding: 4px; border-radius: 8px; background: #eef3f4; }
.review-page-tabs button { display: inline-flex; align-items: center; gap: 6px; padding: 7px 12px; border: 0; border-radius: 6px; background: transparent; color: #60757d; font-size: 13px; }
.review-page-tabs button.active { background: #fff; color: #186f5d; box-shadow: 0 1px 4px rgba(27, 58, 66, 0.1); }
</style>
