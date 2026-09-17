import { createRouter, createWebHistory } from 'vue-router';
import ProductShell from '../layouts/ProductShell.vue';
import { trainingStore } from '../stores/training';
import { getCurrentUser } from '../api';

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: () => trainingStore.state.authenticated ? (trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : trainingStore.state.profile.role === 'admin' ? '/admin/dashboard' : '/student/dashboard') : '/landing' },
    { path: '/landing', component: () => import('../views/LandingView.vue'), meta: { public: true } },
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
    { path: '/register', component: () => import('../views/AuthAccountView.vue'), meta: { public: true } },
    { path: '/forgot-password', component: () => import('../views/AuthAccountView.vue'), meta: { public: true } },
    { path: '/reset-password', component: () => import('../views/AuthAccountView.vue'), meta: { public: true } },
    { path: '/verify-email', component: () => import('../views/AuthAccountView.vue'), meta: { public: true } },
    { path: '/resend-verification', component: () => import('../views/AuthAccountView.vue'), meta: { public: true } },
    { path: '/onboarding', component: () => import('../views/OnboardingView.vue') },
    {
      path: '/',
      component: ProductShell,
      children: [
        { path: 'student/dashboard', component: () => import('../views/StudentDashboardViewV2.vue'), meta: { role: 'student' } },
        { path: 'student/anatomy', component: () => import('../views/AnatomyTrainingView.vue'), meta: { role: 'student' } },
        { path: 'student/archive', component: () => import('../views/StudentLearningArchiveView.vue'), meta: { role: 'student' } },
        { path: 'student/history', redirect: { path: '/student/archive', query: { tab: 'history' } }, meta: { role: 'student' } },
        { path: 'student/daily-review', redirect: { path: '/student/archive', query: { tab: 'review' } }, meta: { role: 'student' } },
        { path: 'teacher/dashboard', component: () => import('../views/TeacherDashboardView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/knowledge', component: () => import('../views/TeacherCaseLibraryView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/exam-settings', component: () => import('../views/TeacherExamSettingsView.vue'), meta: { role: 'teacher' } },
        { path: 'admin/dashboard', component: () => import('../views/AdminDashboardView.vue'), meta: { role: 'admin' } },
        { path: 'admin/skills', component: () => import('../views/AdminSkillsView.vue'), meta: { role: 'admin' } },
        { path: 'admin/knowledge', component: () => import('../views/TeacherCaseLibraryView.vue'), meta: { role: 'admin' } },
        { path: 'help', component: () => import('../views/HelpCenterView.vue') },
        { path: 'knowledge-graph', component: () => import('../views/KnowledgeGraphViewV2.vue') }
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
});

router.beforeEach(async (to) => {
  if (to.meta.public) return true;
  if (trainingStore.state.authenticated) {
    try {
      const user = await getCurrentUser();
      const role = user.role === 'super_admin' ? 'admin' : user.role as 'student' | 'teacher' | 'admin';
      trainingStore.saveProfile({ role, name: user.name });
    } catch {
      trainingStore.signOut();
    }
  }
  if (!trainingStore.state.authenticated) {
    const role = to.path.startsWith('/teacher/') ? 'teacher' : to.path.startsWith('/admin/') ? 'admin' : 'student';
    return { path: '/login', query: { role, redirect: to.fullPath } };
  }
  const requiredRole = to.meta.role as 'student' | 'teacher' | 'admin' | undefined;
  if (requiredRole && trainingStore.state.profile.role !== requiredRole) {
    return trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : trainingStore.state.profile.role === 'admin' ? '/admin/dashboard' : '/student/dashboard';
  }
  return true;
});

export default router;
