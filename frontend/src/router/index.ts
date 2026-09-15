import { createRouter, createWebHistory } from 'vue-router';
import ProductShell from '../layouts/ProductShell.vue';
import { trainingStore } from '../stores/training';

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: () => trainingStore.state.authenticated ? (trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard') : '/landing' },
    { path: '/landing', component: () => import('../views/LandingView.vue'), meta: { public: true } },
    { path: '/onboarding', component: () => import('../views/OnboardingView.vue'), meta: { public: true } },
    {
      path: '/',
      component: ProductShell,
      children: [
        { path: 'student/dashboard', component: () => import('../views/StudentDashboardView.vue'), meta: { role: 'student' } },
        { path: 'student/cases', component: () => import('../views/CaseLibraryView.vue'), meta: { role: 'student' } },
        { path: 'student/anatomy', component: () => import('../views/AnatomyTrainingView.vue'), meta: { role: 'student' } },
        { path: 'student/case/new', component: () => import('../views/CaseSetupView.vue'), meta: { role: 'student' } },
        { path: 'student/history', component: () => import('../views/HistoryView.vue'), meta: { role: 'student' } },
        { path: 'teacher/dashboard', component: () => import('../views/TeacherDashboardView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/cases', component: () => import('../views/TeacherCasesView.vue'), meta: { role: 'teacher' } },
        { path: 'teacher/reports', component: () => import('../views/TeacherReportsView.vue'), meta: { role: 'teacher' } },
        { path: 'knowledge-graph', component: () => import('../views/KnowledgeGraphView.vue') }
      ]
    },
    { path: '/patient-room/:caseId', component: () => import('../views/PatientRoomView.vue'), meta: { role: 'student', immersive: true } },
    { path: '/training-report/:sessionId', component: () => import('../views/TrainingReportView.vue'), meta: { immersive: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
});

router.beforeEach((to) => {
  const demoRole = to.query.demo === 'teacher' ? 'teacher' : to.query.demo === 'student' ? 'student' : null;
  if (demoRole) {
    trainingStore.signIn(demoRole);
    trainingStore.saveProfile({ role: demoRole, completed: true });
  }
  if (to.meta.public) return true;
  if (!trainingStore.state.authenticated) return { path: '/landing', query: { redirect: to.fullPath } };
  const requiredRole = to.meta.role as 'student' | 'teacher' | undefined;
  if (requiredRole && trainingStore.state.profile.role !== requiredRole) {
    return trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard';
  }
  return true;
});

export default router;
