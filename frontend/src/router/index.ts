import { createRouter, createWebHistory } from 'vue-router';
import ProductShell from '../layouts/ProductShell.vue';
import { trainingStore } from '../stores/training';

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: () => trainingStore.state.authenticated ? (trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : trainingStore.state.profile.role === 'admin' ? '/admin/dashboard' : '/student/dashboard') : '/landing' },
    { path: '/landing', component: () => import('../views/LandingView.vue'), meta: { public: true } },
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
    { path: '/onboarding', component: () => import('../views/OnboardingView.vue') },
    {
      path: '/',
      component: ProductShell,
      children: [
        { path: 'student/dashboard', component: () => import('../views/StudentDashboardView.vue'), meta: { role: 'student' } },
        { path: 'student/cases', component: () => import('../views/CaseLibraryView.vue'), meta: { role: 'student' } },
        { path: 'student/anatomy', component: () => import('../views/AnatomyTrainingView.vue'), meta: { role: 'student' } },
        { path: 'student/case/new', component: () => import('../views/CaseSetupView.vue'), meta: { role: 'student' } },
        { path: 'student/history', component: () => import('../views/HistoryView.vue'), meta: { role: 'student' } },
        { path: 'student/daily-review', component: () => import('../views/DailyReviewView.vue'), meta: { role: 'student' } },
        { path: 'teacher/dashboard', component: () => import('../views/TeacherDashboardView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/cases', component: () => import('../views/TeacherCasesView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/reports', component: () => import('../views/TeacherReportsView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/class-review', component: () => import('../views/TeacherClassReviewView.vue'), meta: { role: 'teacher' } },
        { path: 'admin/dashboard', component: () => import('../views/AdminDashboardView.vue'), meta: { role: 'admin' } },
        { path: 'help', component: () => import('../views/HelpCenterView.vue') },
        { path: 'knowledge-graph', component: () => import('../views/KnowledgeGraphView.vue') }
      ]
    },
    { path: '/patient-room/:caseId', component: () => import('../views/PatientRoomView.vue'), meta: { role: 'student', immersive: true } },
    { path: '/training-report/:sessionId', component: () => import('../views/TrainingReportView.vue'), meta: { immersive: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
});

router.beforeEach((to) => {
  const demoRole = import.meta.env.DEV ? (to.query.demo === 'teacher' ? 'teacher' : to.query.demo === 'admin' ? 'admin' : to.query.demo === 'student' ? 'student' : null) : null;
  if (demoRole) {
    trainingStore.signIn(demoRole);
    trainingStore.saveProfile({ role: demoRole, completed: true });
  }
  if (to.meta.public) return true;
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
