<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, GraduationCap, ShieldCheck, Stethoscope, Users } from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import landingImage from '../assets/medical/login-background.png';
import { trainingStore, type WorkspaceRole } from '../stores/training';

const router = useRouter();
const selectedRole = ref<WorkspaceRole>('student');

async function enter() {
  trainingStore.signIn(selectedRole.value);
  const profile = trainingStore.state.profile;
  if (!profile.completed || profile.role !== selectedRole.value) {
    await router.push({ path: '/onboarding', query: { role: selectedRole.value } });
    return;
  }
  await router.push(selectedRole.value === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
}
</script>

<template>
  <main class="landing-screen">
    <section class="landing-workspace">
      <header class="landing-header">
        <div class="brand-lockup">
          <span class="brand-mark">临</span>
          <span><strong>AI标准化病人临床思维训练平台</strong><small>虚拟病例 · 过程评分 · 教师复核</small></span>
        </div>
        <div class="landing-proof"><ShieldCheck :size="17" /> 医学教育专用</div>
      </header>

      <div class="landing-grid">
        <div class="landing-visual">
          <img :src="landingImage" alt="医学教育训练工作台示意图" />
          <div class="landing-overlay">
            <span>当前推荐训练</span>
            <h1>从一次真实感问诊，建立完整临床思维链</h1>
            <p>选择虚拟病例，完成问诊、鉴别诊断、检查决策与证据引用，再由教师复核。</p>
            <div class="training-path">
              <b>选择病例</b><i></i><b>标准化病人</b><i></i><b>训练报告</b><i></i><b>教师反馈</b>
            </div>
          </div>
        </div>

        <aside class="entry-panel">
          <span class="section-kicker">进入教学空间</span>
          <h2>选择你的身份</h2>
          <p>系统会为学生与教师提供不同的任务、数据和工作流。</p>
          <div class="role-choice">
            <button type="button" :class="{ active: selectedRole === 'student' }" @click="selectedRole = 'student'">
              <GraduationCap :size="22" />
              <span><strong>医学生</strong><small>病例训练、能力趋势、学习路径</small></span>
            </button>
            <button type="button" :class="{ active: selectedRole === 'teacher' }" @click="selectedRole = 'teacher'">
              <Users :size="22" />
              <span><strong>医学教师</strong><small>病例发布、报告复核、班级分析</small></span>
            </button>
          </div>
          <button class="button-primary entry-button" type="button" @click="enter">
            进入{{ selectedRole === 'teacher' ? '教师' : '学生' }}工作台
            <ArrowRight :size="18" />
          </button>
          <div class="entry-features">
            <span><Stethoscope :size="15" /> 脚本约束病人</span>
            <span><BookOpenCheck :size="15" /> 指南证据可追溯</span>
          </div>
        </aside>
      </div>

      <div class="landing-command">
        <span><strong>也可以直接告诉智能体</strong><small>例如：“带我去胸痛病例训练”</small></span>
        <AgentCommand />
      </div>
    </section>
  </main>
</template>
