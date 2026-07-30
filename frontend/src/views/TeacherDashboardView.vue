<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { AlertTriangle, ArrowRight, BookOpenCheck, Clock3, FileCheck2, TrendingUp, Users } from '@lucide/vue';
import { getTeacherDashboard } from '../api';
import teacherDashboardImage from '../assets/medical/teacher-dashboard.png';
import type { TeacherDashboard } from '../types';

const router = useRouter();
const dashboard = ref<TeacherDashboard>({
  class_average: 82,
  completion_rate: 76,
  training_sessions: 248,
  teacher_time_saved: '41%',
  citation_accuracy: '88%',
  intervention_needed: 6,
  improvements: [{ label: '临床推理分提升', value: 24 }, { label: '关键问诊遗漏率下降', value: 32 }, { label: '指南引用准确率提升', value: 18 }],
  common_missing_points: ['尚未询问胸痛性质', '尚未排除主动脉夹层', '建议申请心电图和肌钙蛋白'],
  students: [],
  risk_rankings: [],
  teaching_suggestions: []
});
onMounted(async () => {
  try { dashboard.value = await getTeacherDashboard(); } catch { /* Keep teaching mock data available. */ }
});
const interventionStudents = computed(() => dashboard.value.students?.filter((item) => item.needs_intervention) ?? []);
</script>

<template>
  <div class="workspace-page teacher-page">
    <section class="teacher-dashboard-hero">
      <img :src="teacherDashboardImage" alt="" />
      <div><span class="section-kicker">诊断学课程 · 2023-2 班</span><h1>教学质量与班级临床思维概览</h1><p>聚合训练表现、共性遗漏和教师复核任务，用于下一轮教学干预。</p></div>
      <button class="button-primary" type="button" @click="router.push('/teacher/reports')">查看待复核报告 <ArrowRight :size="18" /></button>
    </section>

    <section class="metric-strip teacher-metrics">
      <article><Users :size="19" /><span><small>班级平均分</small><strong>{{ dashboard.class_average }}</strong></span><b>较上月 +4.8</b></article>
      <article><FileCheck2 :size="19" /><span><small>训练总次数</small><strong>{{ dashboard.training_sessions }}</strong></span><b>完成率 {{ dashboard.completion_rate }}%</b></article>
      <article><Clock3 :size="19" /><span><small>批改时间减少</small><strong>{{ dashboard.teacher_time_saved }}</strong></span><b>过程评分辅助</b></article>
      <article><BookOpenCheck :size="19" /><span><small>引用准确率</small><strong>{{ dashboard.citation_accuracy }}</strong></span><b>可追溯证据</b></article>
    </section>

    <div class="teacher-dashboard-grid">
      <section class="surface-panel class-trend">
        <div class="section-heading"><div><span class="section-kicker">近 8 周</span><h2>班级能力趋势</h2></div><TrendingUp :size="20" /></div>
        <svg viewBox="0 0 620 245" role="img" aria-label="班级能力趋势图">
          <line v-for="y in [50,100,150,200]" :key="y" x1="42" :y1="y" x2="594" :y2="y" />
          <polyline class="trend-main" points="42,178 120,165 198,157 276,142 354,130 432,112 510,93 594,78" />
          <polyline class="trend-secondary" points="42,190 120,183 198,170 276,176 354,154 432,147 510,126 594,113" />
        </svg>
        <div class="trend-legend"><span><i></i>临床推理</span><span><i class="secondary"></i>证据引用</span></div>
      </section>

      <section class="surface-panel weakness-panel">
        <div class="section-heading"><div><span class="section-kicker">共性问题</span><h2>班级薄弱项</h2></div><AlertTriangle :size="20" /></div>
        <article v-for="(item, index) in dashboard.common_missing_points.slice(0, 5)" :key="item">
          <span>{{ String(index + 1).padStart(2, '0') }}</span><div><strong>{{ item }}</strong><small>{{ 34 - index * 5 }} 名学生出现</small></div><b :style="{ width: `${88 - index * 12}%` }"></b>
        </article>
      </section>
    </div>

    <div class="teacher-dashboard-grid lower">
      <section class="surface-panel intervention-list">
        <div class="section-heading"><div><span class="section-kicker">需要关注</span><h2>教学干预名单</h2></div><button class="text-button" type="button" @click="router.push('/teacher/reports')">全部报告 <ArrowRight :size="15" /></button></div>
        <article v-for="student in interventionStudents" :key="student.name">
          <span>{{ student.name.slice(-1) }}</span><div><strong>{{ student.name }}</strong><small>{{ student.last_case }} · 薄弱项：{{ student.weakness }}</small></div><b>{{ student.average_score }}</b><button type="button" @click="router.push('/teacher/reports')">查看</button>
        </article>
        <p v-if="!interventionStudents.length" class="empty-copy">当前没有需要重点干预的学生。</p>
      </section>
      <section class="surface-panel teaching-advice">
        <div class="section-heading"><div><span class="section-kicker">智能教学建议</span><h2>下一节课重点</h2></div></div>
        <ol><li v-for="(item, index) in dashboard.teaching_suggestions" :key="item"><span>{{ index + 1 }}</span><p>{{ item }}</p></li></ol>
        <button class="button-secondary" type="button" @click="router.push('/teacher/cases')">从病例库布置训练 <ArrowRight :size="16" /></button>
      </section>
    </div>
  </div>
</template>
