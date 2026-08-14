<script setup lang="ts">
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, CircleHelp, GraduationCap, Network, ScanLine, ShieldCheck, Stethoscope, Users } from '@lucide/vue';
import { resetOnboarding } from '../services/onboarding';
import { trainingStore } from '../stores/training';

const router = useRouter();

function replayTour() {
  resetOnboarding(trainingStore.state.profile.role);
  window.dispatchEvent(new CustomEvent('medical-tour-reset'));
}
</script>

<template>
  <div class="workspace-page help-page">
    <section class="page-title-row">
      <div>
        <span class="section-kicker">帮助中心</span>
        <h1>用最短路径完成一次医学教育训练闭环</h1>
        <p>平台用于虚拟病例教学训练，帮助学生完成问诊、推理、证据引用、解剖定位和每日复盘，教师与管理员负责监督和配置。</p>
      </div>
      <button class="button-primary" type="button" @click="replayTour"><CircleHelp :size="18" /> 重新打开新手引导</button>
    </section>

    <section class="help-grid">
      <article><Stethoscope :size="20" /><strong>学生怎么完成一次病例训练</strong><p>进入病例训练库，选择病例与变体，与 AI 标准化病人问诊，提交鉴别诊断、检查选择和处理原则。</p><button type="button" @click="router.push('/student/cases')">打开病例训练 <ArrowRight :size="15" /></button></article>
      <article><BookOpenCheck :size="20" /><strong>如何查看每日复盘</strong><p>训练结束后进入每日复盘，查看今日表现、薄弱点、明日计划、推荐病例和知识图谱路径。</p><button type="button" @click="router.push('/student/daily-review')">打开每日复盘 <ArrowRight :size="15" /></button></article>
      <article><Network :size="20" /><strong>如何使用知识图谱</strong><p>检索症状、疾病、检查或教材主题，沿关系展开病例、指南、解剖结构和学习目标。</p><button type="button" @click="router.push('/knowledge-graph')">打开知识图谱 <ArrowRight :size="15" /></button></article>
      <article><ScanLine :size="20" /><strong>如何进行解剖定位训练</strong><p>选择器官或结构，在图像上完成定位，系统给出定位准确性、名称掌握和临床关联反馈。</p><button type="button" @click="router.push('/student/anatomy')">打开解剖训练 <ArrowRight :size="15" /></button></article>
      <article><Users :size="20" /><strong>教师如何查看班级分析</strong><p>教师端查看班级看板、学生预警、共性薄弱点、班级复盘和 AI 生成的教学建议。</p><button type="button" @click="router.push('/teacher/class-review')">打开班级复盘 <ArrowRight :size="15" /></button></article>
      <article><GraduationCap :size="20" /><strong>管理员如何管理数据源</strong><p>超级管理员端查看 ModelScope、知识库、图谱、Agent 状态，并配置每日复盘生成策略。</p><button type="button" @click="router.push('/admin/dashboard')">打开管理控制台 <ArrowRight :size="15" /></button></article>
    </section>

    <section class="surface-panel help-safety">
      <ShieldCheck :size="22" />
      <div>
        <strong>医学安全声明</strong>
        <p>本平台仅用于医学教学训练，所有病例均为虚拟或脱敏教学数据，不用于真实临床诊断、治疗决策或急救处置。</p>
      </div>
    </section>
  </div>
</template>
