<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, Eye, EyeOff, GraduationCap, LoaderCircle, LockKeyhole, ShieldCheck, UserRound, Users } from '@lucide/vue';
import teacherMentorImage from '../assets/medical/teacher-mentor-hero.png';
import { trainingStore, type WorkspaceRole } from '../stores/training';

const route = useRoute();
const router = useRouter();
const showPassword = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const form = reactive({ account: '', password: '', remember: true });

const role = computed<WorkspaceRole>(() => route.query.role === 'teacher' ? 'teacher' : route.query.role === 'admin' ? 'admin' : 'student');
const roleOptions = [
  { value: 'student' as const, label: '医学生', icon: GraduationCap },
  { value: 'teacher' as const, label: '医学教师', icon: Users },
  { value: 'admin' as const, label: '管理员', icon: ShieldCheck }
];

const roleMeta = computed(() => {
  if (role.value === 'teacher') return {
    title: '登录教师工作台',
    description: '复核学生训练报告，查看班级薄弱项并形成教学行动。',
    accountHint: 'teacher01',
    destination: '/teacher/dashboard'
  };
  if (role.value === 'admin') return {
    title: '登录系统控制台',
    description: '管理平台数据源、知识图谱与 Agent 策略边界。',
    accountHint: 'admin',
    destination: '/admin/dashboard'
  };
  return {
    title: '登录学生训练空间',
    description: '进入虚拟解剖室、空间定位测验与知识图谱。',
    accountHint: 'student01',
    destination: '/student/dashboard'
  };
});

function selectRole(nextRole: WorkspaceRole) {
  errorMessage.value = '';
  router.replace({ path: '/login', query: { ...route.query, role: nextRole } });
}

function fillDemoAccount() {
  form.account = roleMeta.value.accountHint;
  form.password = '';
  errorMessage.value = '';
}

function safeDestination() {
  const requested = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : '';
  if (role.value === 'student' && requested.startsWith('/student/')) return requested;
  if (role.value === 'teacher' && requested.startsWith('/teacher/')) return requested;
  if (role.value === 'admin' && requested.startsWith('/admin/')) return requested;
  return roleMeta.value.destination;
}

async function submit() {
  errorMessage.value = '';
  loading.value = true;
  try {
    await trainingStore.authenticate(form.account.trim(), form.password, role.value, form.remember);
    await router.push(safeDestination());
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败，请检查账号和密码后重试。';
  } finally {
    loading.value = false;
  }
}

watch(role, () => {
  form.account = localStorage.getItem(`medical_login_account_${role.value}`) ?? '';
  form.password = '';
  errorMessage.value = '';
}, { immediate: true });
</script>

<template>
  <main class="login-screen">
    <header class="login-header">
      <button class="brand-lockup" type="button" @click="router.push('/landing')">
        <span class="brand-mark">临</span>
        <span><strong>临思智训</strong><small>AI标准化病人临床思维训练平台</small></span>
      </button>
      <button class="login-back" type="button" @click="router.push('/landing')"><ArrowLeft :size="17" /> 返回首页</button>
    </header>

    <section class="login-stage">
      <figure class="login-context">
        <img :src="teacherMentorImage" alt="AI医学教学导师与临床训练工作台" />
        <figcaption>
          <strong>身份清晰，权限才可信。</strong>
          <p>{{ roleMeta.description }}</p>
          <span><ShieldCheck :size="16" /> 虚拟教学病例，不用于真实临床诊断</span>
        </figcaption>
      </figure>

      <section class="login-panel">
        <div class="login-heading">
          <h1>{{ roleMeta.title }}</h1>
          <p>请选择身份并输入对应账号密码。</p>
        </div>

        <div class="login-role-tabs" aria-label="选择登录身份">
          <button v-for="item in roleOptions" :key="item.value" type="button" :class="{ active: role === item.value }" :aria-pressed="role === item.value" @click="selectRole(item.value)">
            <component :is="item.icon" :size="18" /> {{ item.label }}
          </button>
        </div>

        <form class="login-form" @submit.prevent="submit">
          <label>
            <span>账号</span>
            <div class="login-input"><UserRound :size="18" /><input v-model="form.account" name="username" autocomplete="username" autofocus required placeholder="请输入账号" /></div>
          </label>
          <label>
            <span>密码</span>
            <div class="login-input"><LockKeyhole :size="18" /><input v-model="form.password" name="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" required placeholder="请输入密码" /><button type="button" :title="showPassword ? '隐藏密码' : '显示密码'" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword"><EyeOff v-if="showPassword" :size="18" /><Eye v-else :size="18" /></button></div>
          </label>

          <label class="remember-account"><input v-model="form.remember" type="checkbox" /> <span>记住账号</span></label>
          <p v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</p>

          <button class="login-submit" type="submit" :disabled="loading">
            <LoaderCircle v-if="loading" class="login-spinner" :size="18" />
            <span>{{ loading ? '正在验证...' : '登录并进入工作台' }}</span>
            <ArrowRight v-if="!loading" :size="18" />
          </button>
        </form>

        <div class="demo-account">
          <span><strong>教学演示账号</strong><small>{{ roleMeta.accountHint }} · 密码由管理员分配</small></span>
          <button type="button" @click="fillDemoAccount">填入账号</button>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.login-screen { min-height: 100dvh; padding: 0 32px 32px; color: #143438; background: #edf3f2; }
.login-header { display: flex; align-items: center; justify-content: space-between; width: min(1240px, 100%); min-height: 78px; margin: 0 auto; border-bottom: 1px solid rgba(26, 70, 72, .12); }
.login-header .brand-lockup { border: 0; background: transparent; text-align: left; }
.login-header .brand-mark { color: #fff; background: #0f766e; }
.login-back { display: inline-flex; align-items: center; gap: 7px; min-height: 42px; padding: 0 14px; border: 1px solid rgba(26, 70, 72, .16); border-radius: 10px; color: #45666a; background: rgba(255, 255, 255, .52); }
.login-stage { display: grid; grid-template-columns: minmax(0, 1.12fr) minmax(400px, .88fr); width: min(1240px, 100%); min-height: min(700px, calc(100dvh - 110px)); margin: 32px auto 0; overflow: hidden; border-radius: 16px; background: #fff; box-shadow: 0 28px 80px rgba(24, 67, 69, .14); }
.login-context { position: relative; min-height: 620px; margin: 0; overflow: hidden; background: #12342f; }
.login-context::after { content: ""; position: absolute; inset: 35% 0 0; background: linear-gradient(180deg, transparent, rgba(4, 24, 21, .92)); }
.login-context img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: 58% center; filter: saturate(.76) contrast(1.04); }
.login-context figcaption { position: absolute; z-index: 1; right: clamp(28px, 5vw, 62px); bottom: clamp(30px, 5vw, 58px); left: clamp(28px, 5vw, 62px); display: grid; gap: 13px; color: #fff; }
.login-context figcaption strong { max-width: 10em; font-size: clamp(2rem, 3.6vw, 3.6rem); line-height: 1.08; letter-spacing: -.035em; }
.login-context figcaption p { max-width: 34em; margin: 0; color: #c5d8d3; line-height: 1.7; }
.login-context figcaption span { display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; color: #83e2c7; font-size: 13px; font-weight: 800; }
.login-panel { display: flex; flex-direction: column; justify-content: center; padding: clamp(42px, 6vw, 76px); }
.login-heading h1 { margin: 0; color: #102f33; font-size: clamp(2rem, 3.2vw, 3rem); line-height: 1.12; letter-spacing: -.035em; }
.login-heading p { margin: 14px 0 0; color: #71888b; }
.login-role-tabs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 5px; margin-top: 34px; padding: 5px; border-radius: 12px; background: #edf4f3; }
.login-role-tabs button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 46px; padding: 0 10px; border: 0; border-radius: 9px; color: #678084; background: transparent; font-size: 13px; font-weight: 800; }
.login-role-tabs button.active { color: #075f58; background: #fff; box-shadow: 0 7px 20px rgba(28, 75, 74, .09); }
.login-form { display: grid; gap: 18px; margin-top: 30px; }
.login-form > label:not(.remember-account) { display: grid; gap: 8px; color: #36575b; font-size: 14px; font-weight: 800; }
.login-input { display: flex; align-items: center; gap: 10px; min-height: 50px; padding: 0 14px; border: 1px solid #cbdada; border-radius: 10px; color: #789093; background: #fbfdfd; transition: border-color .2s ease, box-shadow .2s ease, background-color .2s ease; }
.login-input:focus-within { border-color: #19877d; background: #fff; box-shadow: 0 0 0 3px rgba(25, 135, 125, .12); }
.login-input input { min-width: 0; flex: 1; border: 0; outline: 0; color: #173b3f; background: transparent; font: inherit; }
.login-input button { display: grid; width: 36px; height: 36px; place-items: center; border: 0; border-radius: 8px; color: #6d8588; background: transparent; }
.remember-account { display: inline-flex; align-items: center; gap: 8px; width: max-content; color: #5f777a; font-size: 13px; }
.remember-account input { width: 16px; height: 16px; accent-color: #0f766e; }
.login-error { margin: -4px 0 0; padding: 11px 13px; border-radius: 9px; color: #9b3418; background: #fff1e9; font-size: 13px; line-height: 1.55; }
.login-submit { display: inline-flex; align-items: center; justify-content: center; gap: 9px; min-height: 52px; border: 0; border-radius: 10px; color: #fff; background: #0f766e; font-weight: 900; box-shadow: 0 16px 32px rgba(15, 118, 110, .18); }
.login-submit:hover:not(:disabled) { background: #0a6861; transform: translateY(-1px); }
.login-submit:disabled { cursor: wait; opacity: .68; }
.login-spinner { animation: login-spin .8s linear infinite; }
.demo-account { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e1eaea; }
.demo-account span { display: grid; gap: 3px; }
.demo-account strong { color: #37585c; font-size: 13px; }
.demo-account small { color: #809396; font-size: 12px; }
.demo-account button { min-height: 38px; padding: 0 13px; border: 1px solid #cadbd9; border-radius: 9px; color: #0f6f68; background: #f4faf8; font-weight: 800; white-space: nowrap; }
.login-screen button:focus-visible, .login-screen input:focus-visible { outline: 3px solid rgba(15, 118, 110, .26); outline-offset: 2px; }
@keyframes login-spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) {
  .login-screen { padding: 0 18px 24px; }
  .login-stage { grid-template-columns: 1fr; margin-top: 22px; }
  .login-context { min-height: 260px; }
  .login-context figcaption strong { font-size: 2.3rem; }
  .login-context figcaption p { display: none; }
  .login-panel { padding: 40px; }
}
@media (max-width: 560px) {
  .login-screen { padding: 0 14px 18px; }
  .login-header { min-height: 68px; }
  .login-header .brand-lockup small { display: none; }
  .login-back { width: 42px; padding: 0; justify-content: center; font-size: 0; }
  .login-stage { border-radius: 14px; }
  .login-context { min-height: 200px; }
  .login-context figcaption { right: 22px; bottom: 22px; left: 22px; }
  .login-context figcaption strong { font-size: 1.8rem; }
  .login-context figcaption span { margin-top: 0; }
  .login-panel { padding: 32px 20px 24px; }
  .login-role-tabs button { gap: 5px; font-size: 12px; }
  .demo-account { align-items: flex-start; }
}
@media (prefers-reduced-motion: reduce) { .login-submit, .login-spinner { animation: none; transition: none; } }
</style>
