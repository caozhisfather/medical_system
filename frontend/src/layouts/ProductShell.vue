<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { Component } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  BarChart3, ChartNetwork, ChevronDown, CircleHelp, History, LayoutDashboard, Library, LogOut, ScanLine,
  Settings2, SlidersHorizontal, Users
} from '@lucide/vue';
import AgentCommand from '../components/AgentCommand.vue';
import BrandLogo from '../components/BrandLogo.vue';
import OnboardingTour from '../components/onboarding/OnboardingTour.vue';
import SafetyNotice from '../components/SafetyNotice.vue';
import { trainingStore, type WorkspaceRole } from '../stores/training';
import { logout } from '../api';

const route = useRoute();
const router = useRouter();
const role = computed(() => trainingStore.state.profile.role);
const isStudentOverview = computed(() => route.path === '/student/dashboard');
const profileMenu = ref<HTMLDetailsElement>();

type NavItem = { label: string; path: string; icon: Component };

const workspaces: Record<WorkspaceRole, { title: string; links: NavItem[] }> = {
  student: {
    title: '学生工作台',
    links: [
      { label: '学习总览', path: '/student/dashboard', icon: LayoutDashboard },
      { label: '虚拟解剖室', path: '/student/anatomy', icon: ScanLine },
      { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork },
        { label: '学习档案', path: '/student/archive', icon: History },
        { label: '我的班级', path: '/student/classrooms', icon: Users }
    ]
  },
  teacher: {
    title: '教师工作台',
    links: [
      { label: '教学总览', path: '/teacher/dashboard', icon: BarChart3 },
      { label: '班级管理', path: '/teacher/classrooms', icon: Users },
      { label: '教学知识库', path: '/teacher/knowledge', icon: Library },
      { label: '题型与提示词', path: '/teacher/exam-settings', icon: SlidersHorizontal },
      { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork }
    ]
  },
  admin: {
    title: '管理员工作台',
    links: [
      { label: '系统控制台', path: '/admin/dashboard', icon: Settings2 },
      { label: '班级管理', path: '/admin/classrooms', icon: Users },
      { label: 'Skill 管理', path: '/admin/skills', icon: SlidersHorizontal },
      { label: '教学知识库', path: '/admin/knowledge', icon: Library },
      { label: '知识图谱', path: '/knowledge-graph', icon: ChartNetwork }
    ]
  }
};

const workspace = computed(() => workspaces[role.value]);
const currentPage = computed(() => route.path === '/help'
  ? '帮助中心'
  : workspace.value.links.find(item => item.path === route.path)?.label ?? workspace.value.title);

function closeProfileMenu() {
  if (profileMenu.value) profileMenu.value.open = false;
}

watch(() => route.fullPath, closeProfileMenu);

async function signOut() {
  closeProfileMenu();
  try {
    await logout();
  } finally {
    trainingStore.signOut();
    await router.push('/landing');
  }
}
</script>

<template>
  <div class="product-shell" :class="['role-' + role, { 'student-dashboard-shell': isStudentOverview }]">
    <aside class="product-sidebar">
      <RouterLink class="sidebar-brand" :to="workspace.links[0].path">
        <BrandLogo variant="compact" subtitle="智能学习平台" />
      </RouterLink>
      <nav aria-label="主导航">
        <RouterLink v-for="item in workspace.links" :key="item.path" :to="item.path" exact-active-class="active"
          :data-tour="item.path === '/student/dashboard' ? 'today-task' : undefined">
          <component :is="item.icon" :size="19" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-support">
        <RouterLink class="sidebar-help" to="/help" exact-active-class="active"><CircleHelp :size="17" />帮助中心</RouterLink>
        <SafetyNotice compact />
      </div>
    </aside>

    <header class="product-topbar">
      <div class="topbar-title">
        <RouterLink class="mobile-brand" :to="workspace.links[0].path" aria-label="芯聆知医工作台">
          <BrandLogo alt="" />
        </RouterLink>
        <strong>{{ currentPage }}</strong>
      </div>
      <AgentCommand compact search-icon />
      <details ref="profileMenu" class="workspace-profile-menu" @keydown.esc="closeProfileMenu">
        <summary class="topbar-profile" aria-label="账户菜单">
          <span class="user-avatar">{{ trainingStore.state.profile.name.slice(0, 1) }}</span>
          <span><strong>{{ trainingStore.state.profile.name }}</strong><small>{{ workspace.title }}</small></span>
          <ChevronDown :size="15" />
        </summary>
        <div class="workspace-profile-links">
          <RouterLink class="profile-help" to="/help" @click="closeProfileMenu"><CircleHelp :size="16" />帮助中心</RouterLink>
          <button type="button" @click="signOut"><LogOut :size="16" />退出登录</button>
        </div>
      </details>
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

<style scoped>
.product-shell {
  grid-template-columns: clamp(180px, 14vw, 238px) minmax(0, 1fr);
  grid-template-rows: 70px minmax(calc(100vh - 70px), auto);
  background: var(--ui-canvas);
}

.product-shell .product-sidebar {
  padding: 16px 14px 14px;
  overflow-y: auto;
  border-right: 0;
  border-radius: 0 0 var(--ui-radius) 0;
  background:
    linear-gradient(180deg, #edf5ff33, #edf5ff0d 55%, #edf5ff33),
    #dbe8fc url('../assets/brand/sidebar-medical.webp') 8% center / cover no-repeat;
}

.sidebar-brand { min-height: 55px; margin-bottom: 28px; border-radius: 10px; }
.product-shell .product-sidebar nav { gap: 7px; }
.product-shell .product-sidebar nav a, .sidebar-help {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 45px;
  padding-inline: clamp(10px, 1.45vw, 22px);
  border: 1px solid transparent;
  border-radius: 11px;
  color: #1b3968;
  font-size: 14px;
  font-weight: 750;
}
.product-shell .product-sidebar nav a svg, .sidebar-help svg { flex: none; }
.product-shell .product-sidebar nav a:hover, .sidebar-help:hover { background: rgba(255, 255, 255, .55); color: #124cca; }
.product-shell .product-sidebar nav a.active, .sidebar-help.active {
  border-color: rgba(144, 193, 255, .48);
  background: var(--ui-primary);
  color: #fff;
  box-shadow: inset 0 -4px 12px rgba(134, 183, 255, .24), 0 5px 15px rgba(8, 21, 66, .27);
}

.sidebar-support { display: grid; gap: 5px; margin-top: auto; }
.sidebar-help { padding-inline: 10px; }
.product-sidebar :is(a, button):focus-visible { outline-color: #1d5cf1; }

.product-shell .product-topbar {
  grid-template-columns: minmax(108px, .36fr) minmax(0, 1fr) auto;
  min-height: 70px;
  gap: clamp(10px, 1.4vw, 22px);
  padding: 8px clamp(12px, 1.6vw, 28px);
  border: 0;
  background: rgba(232, 239, 253, .96) !important;
  box-shadow: none !important;
}
.student-dashboard-shell .product-topbar { grid-template-columns: minmax(0, 1fr) auto; }
.student-dashboard-shell .topbar-title { display: none; }
.mobile-brand { display: none; }
.topbar-title strong { color: var(--ink); font-size: 16px; }
.product-topbar :deep(.agent-command) {
  justify-self: center;
  width: min(100%, 720px);
  min-height: 42px;
  grid-template-columns: 20px minmax(0, 1fr) 53px;
  border-color: #d4e2ff;
  border-radius: 999px;
  background: #f9fbff;
  box-shadow: 0 3px 8px rgba(47, 98, 216, .14);
}
.product-topbar :deep(.agent-command input) { height: 32px; font-size: 14px; }
.product-topbar :deep(.agent-command button) {
  width: 53px;
  height: 31px;
  border-radius: 999px;
  background: var(--ui-primary);
}
.product-shell .product-content { background: var(--ui-canvas); }

.workspace-profile-menu { position: relative; min-width: 0; }
.product-shell .topbar-profile { display: grid; border: 0; background: transparent; cursor: pointer; list-style: none; }
.topbar-profile::-webkit-details-marker { display: none; }
.topbar-profile strong { overflow: hidden; max-width: 11em; text-overflow: ellipsis; white-space: nowrap; }
.workspace-profile-links {
  position: absolute;
  z-index: 1;
  top: calc(100% + 5px);
  right: 0;
  display: grid;
  min-width: 145px;
  gap: 2px;
  padding: 5px;
  border: 1px solid var(--line);
  border-radius: 11px;
  background: var(--paper);
  box-shadow: var(--shadow);
}
.workspace-profile-links :is(a, button) { display: flex; align-items: center; gap: 7px; padding: 7px 8px; border: 0; border-radius: 6px; background: transparent; color: var(--ink); font-size: 13px; text-align: left; }
.workspace-profile-links :is(a, button):hover { background: var(--soft); }
.workspace-profile-links .profile-help { display: none; }

@media (max-width: 760px) {
  .product-shell .product-topbar { grid-template-columns: minmax(0, 1fr) auto; gap: 5px 12px; }
  .product-shell .topbar-title { display: flex; align-items: center; gap: 8px; }
  .mobile-brand { display: inline-flex; flex: none; }
  .mobile-brand :deep(.brand-logo) { --brand-mark-size: 30px; --brand-mark-padding: 2px; }
  .topbar-title strong { font-size: 15px; }
  .product-shell .topbar-profile { grid-template-columns: 30px 14px; gap: 3px; min-height: 34px; }
  .topbar-profile > span:not(.user-avatar) { display: none; }
  .workspace-profile-links .profile-help { display: flex; }
  .product-shell .product-sidebar { overflow: hidden; padding: 8px 10px 2px; border-radius: 0; background-position: center 56%; }
  .sidebar-brand, .sidebar-support { display: none; }
  .product-shell .product-sidebar nav { gap: 5px; }
  .product-shell .product-sidebar nav a { min-width: 0; min-height: 35px; padding-inline: 10px; gap: 5px; font-size: 12px; }
  .product-shell .product-sidebar nav a svg { width: 15px; height: 15px; }
}
</style>
