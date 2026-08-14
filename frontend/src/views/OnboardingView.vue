<script setup lang="ts">
import { computed, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, Check, GraduationCap, ShieldCheck, Users } from '@lucide/vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore, type WorkspaceRole } from '../stores/training';

const router = useRouter();
const role = computed<WorkspaceRole>(() => trainingStore.state.profile.role);
const form = reactive({
  name: '陈同学',
  school: '东部医科大学',
  grade: '临床医学四年级',
  specialty: '临床医学',
  className: '临床医学 2023-2 班',
  direction: '急诊与内科临床思维'
});
const roleCopy = computed(() => {
  if (role.value === 'teacher') return { title: '配置教师工作台', desc: '用于组织班级、病例、班级复盘和报告复核，不涉及真实诊疗。', label: '医学教师', grade: '教研室/科室', specialty: '课程方向', className: '主要班级', direction: '教学重点', icon: Users };
  if (role.value === 'admin') return { title: '配置超级管理员控制台', desc: '用于管理数据源、知识图谱、Agent 状态和每日复盘策略。', label: '超级管理员', grade: '管理部门', specialty: '系统职责', className: '管理范围', direction: '控制重点', icon: ShieldCheck };
  return { title: '配置学生训练路径', desc: '用于推荐适合你的病例难度、每日复盘和复训路径。', label: '医学生', grade: '年级', specialty: '专业', className: '所在班级', direction: '训练方向', icon: GraduationCap };
});

watch(role, (next) => {
  if (next === 'teacher') Object.assign(form, { name: '张老师', grade: '诊断学教研室', specialty: '诊断学与临床技能', className: '临床医学 2023-2 班', direction: '诊断学与临床技能' });
  else if (next === 'admin') Object.assign(form, { name: '超级管理员', grade: '系统管理中心', specialty: '平台运维与知识工程', className: '全校医学教学空间', direction: '数据源与复盘策略' });
  else Object.assign(form, { name: '陈同学', grade: '临床医学四年级', specialty: '临床医学', className: '临床医学 2023-2 班', direction: '急诊与内科临床思维' });
}, { immediate: true });

async function finish() {
  trainingStore.saveProfile({ ...form, role: role.value });
  await router.push(role.value === 'teacher' ? '/teacher/dashboard' : role.value === 'admin' ? '/admin/dashboard' : '/student/dashboard');
}
</script>

<template>
  <main class="onboarding-screen">
    <section class="onboarding-card">
      <button class="icon-button back-button" type="button" title="返回" @click="router.push('/landing')"><ArrowLeft :size="19" /></button>
      <div class="onboarding-intro">
        <span class="brand-mark">临</span>
        <span class="section-kicker">建立专属教学空间</span>
        <h1>{{ roleCopy.title }}</h1>
        <p>{{ roleCopy.desc }}</p>
        <div class="onboarding-steps">
          <span class="done"><Check :size="15" /> 身份确认</span>
          <span class="active">2 基础信息</span>
          <span>3 进入工作台</span>
        </div>
      </div>
      <form class="onboarding-form" @submit.prevent="finish">
        <div class="onboarding-role">
          <component :is="roleCopy.icon" :size="20" />
          <span><strong>{{ roleCopy.label }}</strong><small>身份可在登录页重新选择</small></span>
        </div>
        <label>姓名或演示称呼<input v-model="form.name" required /></label>
        <label>学校/机构<input v-model="form.school" required /></label>
        <div class="form-split">
          <label>{{ roleCopy.grade }}<input v-model="form.grade" required /></label>
          <label>{{ roleCopy.specialty }}<input v-model="form.specialty" required /></label>
        </div>
        <label>{{ roleCopy.className }}<input v-model="form.className" required /></label>
        <label>{{ roleCopy.direction }}
          <select v-model="form.direction">
            <option>急诊与内科临床思维</option>
            <option>诊断学与临床技能</option>
            <option>数据源与复盘策略</option>
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