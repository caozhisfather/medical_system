<script setup lang="ts">
import { computed } from 'vue';
import type { Component } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  BarChart3,
  Bell,
  BookOpen,
  ChartNetwork,
  ChevronDown,
  CircleHelp,
  FileChartColumn,
  History,
  LayoutDashboard,
  Library,
  LogOut,
  Mail,
  ScanLine,
  Search,
  Settings2,
  SlidersHorizontal,
  Users
} from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import BrandLogo from '../components/BrandLogo.vue';
import OnboardingTour from '../components/onboarding/OnboardingTour.vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore } from '../stores/training';
import { logout } from '../api';

const route = useRoute();
const router = useRouter();
const role = computed(() => trainingStore.state.profile.role);

type NavItem = {
  label: string;
  path: string;
  icon: Component;
  tour?: string;
  hash?: string;
};

const studentNav: NavItem[] = [
  { label: '学习总览', path: '/student/dashboard', icon: LayoutDashboard, tour: 'today-task' },
  { label: '虚拟解剖室', path: '/student/anatomy', icon: ScanLine, tour: 'anatomy-lab' },
  { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork, tour: 'knowledge-graph' },
  { label: '学习档案', path: '/student/archive', icon: History, tour: 'daily-review' }
];
const teacherNav: NavItem[] = [
  { label: '教学总览', path: '/teacher/dashboard', icon: BarChart3, tour: 'teacher-dashboard' },
  { label: '班级管理', path: '/teacher/classrooms', icon: Users },
  { label: '教学知识库', path: '/teacher/knowledge', icon: Library, tour: 'case-management' },
  { label: '题型与提示词', path: '/teacher/exam-settings', icon: SlidersHorizontal, tour: 'exam-settings' },
  { label: '知识图谱', path: '/knowledge-graph', icon: BookOpen, tour: 'teacher-graph' }
];
const adminNav: NavItem[] = [
  { label: '系统控制台', path: '/admin/dashboard', hash: '#admin-console', icon: Settings2, tour: 'admin-review-policy' },
  { label: 'Skill 管理', path: '/admin/skills', icon: SlidersHorizontal },
  { label: '教学知识库', path: '/admin/knowledge', icon: Library, tour: 'admin-knowledge-library' },
  { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork, tour: 'admin-graph' }
];
const nav = computed(() => role.value === 'teacher' ? teacherNav : role.value === 'admin' ? adminNav : studentNav);
const roleMeta = computed(() => {
  if (role.value === 'teacher') return { title: '教师工作台', subtitle: '复核与教学分析', space: '教师教学空间', progress: '6 份待复核', note: '预计节省 48 分钟' };
  if (role.value === 'admin') return { title: '超级管理员', subtitle: '策略与系统控制', space: '系统控制台', progress: '7 类数据源', note: 'Mock 索引可用' };
  return { title: '学生工作台', subtitle: '训练与能力提升', space: '学生训练空间', progress: '本周完成 3 次', note: '连续训练第 4 周' };
});
const currentNavLabel = computed(() => nav.value.find((item) => active(item))?.label ?? roleMeta.value.title);

function homePath() {
  if (role.value === 'teacher') return '/teacher/dashboard';
  if (role.value === 'admin') return '/admin/dashboard';
  return '/student/dashboard';
}

function active(item: NavItem) {
  if (route.path !== item.path) return false;
  if (item.hash) return route.hash === item.hash || (item.hash === '#admin-console' && !route.hash);
  return role.value !== 'admin' || item.path !== '/admin/dashboard' || !route.hash;
}

async function signOut() {
  try {
    await logout();
  } finally {
    trainingStore.signOut();
    await router.push('/landing');
  }
}
</script>

<template>
  <div class="product-shell" :class="`role-${role}`">
    <aside class="product-sidebar">
      <button class="sidebar-brand" type="button" @click="router.push(homePath())">
        <BrandLogo variant="compact" subtitle="虚拟解剖学习平台" />
      </button>
      <label class="sidebar-search">
        <Search :size="16" />
        <input type="search" placeholder="搜索知识、结构与任务" aria-label="全局搜索" />
      </label>
      <nav aria-label="主导航">
        <span class="nav-section-label">学习工具</span>
        <RouterLink v-for="item in nav" :key="`${item.path}-${item.label}`" :to="{ path: item.path, hash: item.hash }" :class="{ active: active(item) }" :data-tour="item.tour">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-progress">
        <FileChartColumn :size="18" />
        <span><strong>{{ roleMeta.progress }}</strong><small>{{ roleMeta.note }}</small></span>
      </div>
      <div class="sidebar-support">
        <button type="button" @click="router.push('/help')"><CircleHelp :size="16" />帮助中心</button>
        <SafetyNotice compact />
      </div>
      <div class="sidebar-user">
        <span class="user-avatar">{{ trainingStore.state.profile.name.slice(0, 1) }}</span>
        <span><strong>{{ trainingStore.state.profile.name }}</strong><small>{{ trainingStore.state.profile.grade || trainingStore.state.profile.className || roleMeta.title }}</small></span>
        <button type="button" title="退出登录" aria-label="退出登录" @click="signOut"><LogOut :size="17" /></button>
      </div>
    </aside>

    <header class="product-topbar">
      <div class="topbar-title">
        <strong>{{ currentNavLabel }}</strong>
        <small>{{ roleMeta.space }}</small>
      </div>
      <AgentCommand compact />
      <div class="topbar-actions">
        <button class="topbar-icon-button" type="button" title="消息" aria-label="消息"><Mail :size="17" /></button>
        <button class="topbar-icon-button" type="button" title="通知" aria-label="通知"><Bell :size="17" /></button>
        <button class="topbar-profile" type="button" @click="router.push('/help')">
          <span class="user-avatar">{{ trainingStore.state.profile.name.slice(0, 1) }}</span>
          <span><strong>{{ trainingStore.state.profile.name }}</strong><small>{{ roleMeta.title }}</small></span>
          <ChevronDown :size="15" />
        </button>
      </div>
    </header>

    <main class="product-content">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
    <OnboardingTour :role="role" />
  </div>
</template>
