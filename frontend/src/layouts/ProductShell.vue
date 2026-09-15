<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  BarChart3,
  BookOpen,
  ChartNetwork,
  ClipboardCheck,
  FileChartColumn,
  History,
  LayoutDashboard,
  Library,
  LogOut,
  ScanLine,
  Stethoscope,
  Users
} from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore } from '../stores/training';

const route = useRoute();
const router = useRouter();
const role = computed(() => trainingStore.state.profile.role);
const displayIdentity = computed(() => role.value === 'teacher'
  ? { name: '王老师', subtitle: '临床诊断学教研室' }
  : { name: trainingStore.state.profile.name, subtitle: trainingStore.state.profile.grade || trainingStore.state.profile.className });

const studentNav = [
  { label: '学习总览', path: '/student/dashboard', icon: LayoutDashboard },
  { label: '病例训练', path: '/student/cases', icon: Stethoscope },
  { label: '解剖训练', path: '/student/anatomy', icon: ScanLine },
  { label: '训练记录', path: '/student/history', icon: History },
  { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork }
];
const teacherNav = [
  { label: '教学总览', path: '/teacher/dashboard', icon: BarChart3 },
  { label: '病例库管理', path: '/teacher/cases', icon: Library },
  { label: '报告复核', path: '/teacher/reports', icon: ClipboardCheck },
  { label: '知识图谱', path: '/knowledge-graph', icon: BookOpen }
];
const nav = computed(() => role.value === 'teacher' ? teacherNav : studentNav);

function active(path: string) {
  return route.path === path || (path === '/student/cases' && route.path.startsWith('/student/case'));
}

async function signOut() {
  trainingStore.signOut();
  await router.push('/landing');
}
</script>

<template>
  <div class="product-shell" :class="`role-${role}`">
    <header class="product-topbar">
      <button class="brand-lockup" type="button" @click="router.push(role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard')">
        <span class="brand-mark">临</span>
        <span><strong>AI标准化病人临床思维训练平台</strong><small>{{ role === 'teacher' ? '教师教学空间' : '学生训练空间' }}</small></span>
      </button>
      <AgentCommand compact />
      <div class="topbar-user">
        <span>{{ displayIdentity.name }}</span>
        <small>{{ displayIdentity.subtitle }}</small>
        <button type="button" title="退出登录" @click="signOut"><LogOut :size="17" /></button>
      </div>
    </header>

    <aside class="product-sidebar">
      <div class="role-sign">
        <Users :size="18" />
        <span><strong>{{ role === 'teacher' ? '教师工作台' : '学生工作台' }}</strong><small>{{ role === 'teacher' ? '复核与教学分析' : '训练与能力提升' }}</small></span>
      </div>
      <nav aria-label="主导航">
        <RouterLink v-for="item in nav" :key="item.path" :to="item.path" :class="{ active: active(item.path) }">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-progress">
        <FileChartColumn :size="18" />
        <span><strong>{{ role === 'teacher' ? '6 份待复核' : '本周完成 3 次' }}</strong><small>{{ role === 'teacher' ? '预计节省 48 分钟' : '连续训练第 4 周' }}</small></span>
      </div>
      <SafetyNotice compact />
    </aside>

    <main class="product-content">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
