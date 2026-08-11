<script setup lang="ts">
import { computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, Check, GraduationCap, Users } from '@lucide/vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore, type WorkspaceRole } from '../stores/training';

const route = useRoute();
const router = useRouter();
const role = computed<WorkspaceRole>(() => route.query.role === 'teacher' ? 'teacher' : 'student');
const form = reactive({
  name: role.value === 'teacher' ? '张老师' : '陈同学',
  school: '东部医科大学',
  grade: role.value === 'teacher' ? '诊断学教研室' : '临床医学四年级',
  specialty: '临床医学',
  className: '临床医学 2023-2 班',
  direction: role.value === 'teacher' ? '诊断学与临床技能' : '急诊与内科临床思维'
});

async function finish() {
  trainingStore.signIn(role.value);
  trainingStore.saveProfile({ ...form, role: role.value });
  await router.push(role.value === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
}
</script>

<template>
  <main class="onboarding-screen">
    <section class="onboarding-card">
      <button class="icon-button back-button" type="button" title="返回" @click="router.push('/landing')"><ArrowLeft :size="19" /></button>
      <div class="onboarding-intro">
        <span class="brand-mark">临</span>
        <span class="section-kicker">建立专属教学空间</span>
        <h1>{{ role === 'teacher' ? '配置教师工作台' : '配置学生训练路径' }}</h1>
        <p>{{ role === 'teacher' ? '用于组织班级、病例和报告复核，不涉及真实诊疗。' : '用于推荐适合你的病例难度和复训路径。' }}</p>
        <div class="onboarding-steps">
          <span class="done"><Check :size="15" /> 身份确认</span>
          <span class="active">2 基础信息</span>
          <span>3 进入工作台</span>
        </div>
      </div>
      <form class="onboarding-form" @submit.prevent="finish">
        <div class="onboarding-role">
          <component :is="role === 'teacher' ? Users : GraduationCap" :size="20" />
          <span><strong>{{ role === 'teacher' ? '医学教师' : '医学生' }}</strong><small>身份可在登录页重新选择</small></span>
        </div>
        <label>姓名或演示称呼<input v-model="form.name" required /></label>
        <label>学校/机构<input v-model="form.school" required /></label>
        <div class="form-split">
          <label>{{ role === 'teacher' ? '教研室/科室' : '年级' }}<input v-model="form.grade" required /></label>
          <label>{{ role === 'teacher' ? '课程方向' : '专业' }}<input v-model="form.specialty" required /></label>
        </div>
        <label>{{ role === 'teacher' ? '主要班级' : '所在班级' }}<input v-model="form.className" required /></label>
        <label>{{ role === 'teacher' ? '教学重点' : '训练方向' }}
          <select v-model="form.direction">
            <option>急诊与内科临床思维</option>
            <option>诊断学与临床技能</option>
            <option>外科急腹症</option>
            <option>呼吸系统疾病</option>
          </select>
        </label>
        <SafetyNotice compact />
        <button class="button-primary" type="submit">完成并进入工作台 <ArrowRight :size="18" /></button>
      </form>
    </section>
  </main>
</template>
