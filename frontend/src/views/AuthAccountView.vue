<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, CheckCircle2, GraduationCap, LoaderCircle, LockKeyhole, Mail, UserRound, Users } from '@lucide/vue';
import { forgotPassword, registerAccount, resendVerification, resetPassword, verifyEmail } from '../api';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const form = reactive({ account: '', name: '', email: '', password: '', confirmPassword: '', role: 'student' as 'student' | 'teacher' });
const mode = computed(() => route.path === '/register' ? 'register' : route.path === '/forgot-password' ? 'forgot' : route.path === '/reset-password' ? 'reset' : route.path === '/resend-verification' ? 'resend' : 'verify');
const title = computed(() => ({ register: '创建学习账号', forgot: '找回密码', reset: '设置新密码', verify: '验证邮箱', resend: '重发验证邮件' })[mode.value]);
const subtitle = computed(() => ({
  register: '填写账号信息，我们会向你的邮箱发送验证链接。',
  forgot: '输入注册邮箱，我们会发送一次性密码重置链接。',
  reset: '新密码至少8位，并同时包含字母和数字。',
  verify: '正在确认验证链接，请稍候。',
  resend: '输入注册邮箱，重新获取验证链接。'
})[mode.value]);

async function submit() {
  errorMessage.value = '';
  successMessage.value = '';
  if ((mode.value === 'register' || mode.value === 'reset') && form.password !== form.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致。';
    return;
  }
  loading.value = true;
  try {
    if (mode.value === 'register') {
      const result = await registerAccount({ account: form.account.trim(), name: form.name.trim(), email: form.email.trim(), password: form.password, role: form.role });
      successMessage.value = result.message;
    } else if (mode.value === 'forgot') {
      const result = await forgotPassword(form.email.trim());
      successMessage.value = result.message;
    } else if (mode.value === 'resend') {
      const result = await resendVerification(form.email.trim());
      successMessage.value = result.message;
    } else if (mode.value === 'reset') {
      const token = typeof route.query.token === 'string' ? route.query.token : '';
      if (!token) throw new Error('重置链接缺少令牌，请重新申请。');
      const result = await resetPassword(token, form.password);
      successMessage.value = result.message;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

watch(() => route.fullPath, async () => {
  errorMessage.value = '';
  successMessage.value = '';
  form.password = '';
  form.confirmPassword = '';
  if (mode.value !== 'verify') return;
  const token = typeof route.query.token === 'string' ? route.query.token : '';
  if (!token) {
    errorMessage.value = '验证链接缺少令牌。';
    return;
  }
  loading.value = true;
  try {
    const result = await verifyEmail(token);
    successMessage.value = result.message;
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '邮箱验证失败。';
  } finally {
    loading.value = false;
  }
}, { immediate: true });
</script>

<template>
  <main class="account-screen">
    <header>
      <button class="account-brand-lockup" type="button" @click="router.push('/landing')">
        <span class="brand-mark">临</span><span><strong>临思智训</strong><small>AI 医学解剖与教学知识平台</small></span>
      </button>
      <button class="account-back-button" type="button" @click="router.push('/login')"><ArrowLeft :size="17" /> 返回登录</button>
    </header>

    <section class="account-layout">
      <aside>
        <span class="aside-mark"><Mail :size="28" /></span>
        <h2>账号安全从邮箱验证开始</h2>
        <p>验证链接和密码重置链接均为一次性链接，并会自动过期。</p>
        <ul><li>密码加密保存</li><li>登录会话自动过期</li><li>重置密码后旧会话失效</li></ul>
      </aside>

      <section class="account-panel">
        <div class="account-heading"><h1>{{ title }}</h1><p>{{ subtitle }}</p></div>

        <div v-if="loading && mode === 'verify'" class="status-panel"><LoaderCircle class="spinner" :size="32" /><strong>正在验证邮箱...</strong></div>
        <div v-else-if="successMessage" class="status-panel success"><CheckCircle2 :size="34" /><strong>{{ successMessage }}</strong><button type="button" @click="router.push('/login')">返回登录</button></div>
        <form v-else-if="mode !== 'verify'" class="account-form" @submit.prevent="submit">
          <template v-if="mode === 'register'">
            <div class="role-switch" aria-label="注册身份">
              <button type="button" :class="{ active: form.role === 'student' }" @click="form.role = 'student'"><GraduationCap :size="18" /> 学生</button>
              <button type="button" :class="{ active: form.role === 'teacher' }" @click="form.role = 'teacher'"><Users :size="18" /> 教师</button>
            </div>
            <label><span>姓名</span><div class="field"><UserRound :size="18" /><input v-model="form.name" required minlength="2" maxlength="40" autocomplete="name" placeholder="请输入姓名" /></div></label>
            <label><span>用户名</span><div class="field"><UserRound :size="18" /><input v-model="form.account" required minlength="3" maxlength="40" pattern="[A-Za-z0-9_]+" autocomplete="username" placeholder="字母、数字或下划线" /></div></label>
          </template>
          <label v-if="mode === 'register' || mode === 'forgot' || mode === 'resend'"><span>邮箱</span><div class="field"><Mail :size="18" /><input v-model="form.email" required type="email" autocomplete="email" placeholder="用于验证和找回密码" /></div></label>
          <template v-if="mode === 'register' || mode === 'reset'">
            <label><span>密码</span><div class="field"><LockKeyhole :size="18" /><input v-model="form.password" required minlength="8" maxlength="120" type="password" :autocomplete="mode === 'reset' ? 'new-password' : 'new-password'" placeholder="至少8位，包含字母和数字" /></div></label>
            <label><span>确认密码</span><div class="field"><LockKeyhole :size="18" /><input v-model="form.confirmPassword" required type="password" autocomplete="new-password" placeholder="再次输入密码" /></div></label>
          </template>
          <p v-if="form.role === 'teacher' && mode === 'register'" class="teacher-note">教师邮箱验证后还需管理员审核才能登录。</p>
          <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
          <button class="primary" type="submit" :disabled="loading"><LoaderCircle v-if="loading" class="spinner" :size="18" />{{ loading ? '正在提交...' : mode === 'register' ? '创建账号并发送验证邮件' : mode === 'forgot' ? '发送重置邮件' : mode === 'resend' ? '重发验证邮件' : '确认新密码' }}</button>
          <router-link v-if="mode === 'register' && errorMessage" to="/resend-verification">重新发送验证邮件</router-link>
        </form>
        <div v-else class="status-panel error-status"><strong>{{ errorMessage || '无法验证邮箱。' }}</strong><button type="button" @click="router.push('/resend-verification')">重发验证邮件</button></div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.account-layout aside h2 { color: #fff; }
.account-screen { min-height: 100dvh; padding: 0 28px 32px; color: #173b3f; background: #edf3f2; }
header { display: flex; align-items: center; justify-content: space-between; width: min(1060px, 100%); min-height: 78px; margin: 0 auto; border-bottom: 1px solid rgba(26,70,72,.12); }
.account-brand-lockup { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 6px 8px; border: 0; color: #173b3f; background: transparent; text-align: left; }
.account-brand-lockup > span:last-child { display: grid; min-width: 0; }
.account-brand-lockup strong { color: #11343b; font-size: 14px; white-space: nowrap; }
.account-brand-lockup small { margin-top: 2px; color: #71868a; font-size: 13px; font-weight: 700; }
.brand-mark { display: grid; width: 38px; height: 38px; place-items: center; flex: 0 0 38px; border-radius: 8px; color: #fff; background: #0f766e; font-weight: 900; }
.account-back-button { position: static; display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 42px; padding: 0 14px; border: 1px solid #cbdada; border-radius: 8px; color: #45666a; background: #fff; white-space: nowrap; }
.account-layout { display: grid; grid-template-columns: 350px minmax(0, 1fr); width: min(1060px, 100%); min-height: 650px; margin: 32px auto 0; overflow: hidden; border-radius: 8px; background: #fff; box-shadow: 0 24px 70px rgba(24,67,69,.13); }
aside { padding: 62px 42px; color: #fff; background: #164e4a; } .aside-mark { display: grid; width: 54px; height: 54px; place-items: center; border: 1px solid rgba(255,255,255,.25); border-radius: 8px; color: #8ce5ce; }
aside h2 { margin: 30px 0 16px; font-size: 30px; line-height: 1.3; letter-spacing: 0; } aside p { color: #c6d9d5; line-height: 1.75; } aside ul { display: grid; gap: 14px; margin: 36px 0 0; padding-left: 20px; color: #d8e7e4; }
.account-panel { display: flex; flex-direction: column; justify-content: center; padding: 54px clamp(32px,7vw,86px); }.account-heading h1 { margin: 0; font-size: 36px; letter-spacing: 0; }.account-heading p { margin: 12px 0 0; color: #71888b; line-height: 1.6; }
.account-form { display: grid; gap: 17px; margin-top: 28px; }.account-form label { display: grid; gap: 7px; font-size: 14px; font-weight: 800; }.field { display: flex; align-items: center; gap: 10px; min-height: 50px; padding: 0 14px; border: 1px solid #cbdada; border-radius: 8px; color: #789093; background: #fbfdfd; }.field:focus-within { border-color: #19877d; box-shadow: 0 0 0 3px rgba(25,135,125,.12); }.field input { min-width: 0; flex: 1; border: 0; outline: 0; color: #173b3f; background: transparent; font: inherit; }
.role-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 5px; border-radius: 8px; background: #edf4f3; }.role-switch button { display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 44px; border: 0; border-radius: 6px; color: #678084; background: transparent; font-weight: 800; }.role-switch button.active { color: #075f58; background: #fff; box-shadow: 0 5px 15px rgba(28,75,74,.08); }
.primary, .status-panel button { min-height: 50px; border: 0; border-radius: 8px; color: #fff; background: #0f766e; font-weight: 900; }.primary { display: flex; align-items: center; justify-content: center; gap: 8px; }.primary:disabled { opacity: .65; }.teacher-note, .error { margin: 0; padding: 11px 13px; border-radius: 6px; font-size: 13px; line-height: 1.5; }.teacher-note { color: #765313; background: #fff8df; }.error { color: #9b3418; background: #fff1e9; }
.status-panel { display: grid; justify-items: center; gap: 18px; margin-top: 40px; padding: 38px; color: #537174; text-align: center; background: #f4f9f8; }.status-panel.success { color: #0f766e; }.status-panel button { padding: 0 22px; }.error-status { color: #9b3418; }.spinner { animation: spin .8s linear infinite; } @keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 760px) { .account-screen { padding: 0 14px 20px; } header { min-height: 68px; } .account-brand-lockup small { display: none; } .account-layout { grid-template-columns: 1fr; margin-top: 20px; }.account-layout aside { display: none; }.account-panel { padding: 36px 20px; }.account-heading h1 { font-size: 30px; } }
</style>
