<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, CheckCircle2, GraduationCap, LoaderCircle, LockKeyhole, Mail, UserRound, Users } from '@lucide/vue';
import { forgotPassword, registerAccount, resendVerification, resetPassword, verifyEmail } from '../api';
import BrandLogo from '../components/BrandLogo.vue';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const resendLoading = ref(false);
const code = ref('');
const countdown = ref(0);
let sentAt = Number(sessionStorage.getItem('medical_verification_sent_at') || 0);
const countdownTimer = setInterval(()=>{countdown.value=Math.max(0,Math.ceil((sentAt+60000-Date.now())/1000));},500);
onBeforeUnmount(()=>clearInterval(countdownTimer));
const form = reactive({ nickname: '', name: '', email: '', password: '', confirmPassword: '', role: 'student' as 'student' | 'teacher' });
const mode = computed(() => route.path === '/register' ? 'register' : route.path === '/forgot-password' ? 'forgot' : route.path === '/reset-password' ? 'reset' : route.path === '/resend-verification' ? 'resend' : 'verify');
const title = computed(() => ({ register: '创建学习账号', forgot: '找回密码', reset: '设置新密码', verify: '验证邮箱', resend: '重发验证邮件' })[mode.value]);
const subtitle = computed(() => ({
  register: '填写真实姓名与昵称，验证邮箱后使用邮箱登录。',
  forgot: '输入注册邮箱，我们会发送一次性密码重置链接。',
  reset: '新密码至少8位，并同时包含字母和数字。',
  verify: '输入邮件中的六位验证码，10分钟内有效。',
  resend: '输入注册邮箱，重新获取六位验证码。'
})[mode.value]);

function rememberVerification(sent:boolean) {
 sessionStorage.setItem('medical_pending_verification',JSON.stringify({email:form.email.trim(),role:form.role}));
 if(sent){sentAt=Date.now();countdown.value=60;sessionStorage.setItem('medical_verification_sent_at',String(sentAt));}
}
function returnToLogin(){router.push({path:'/login',query:{role:form.role}});}
async function sendAgain(){
 if(resendLoading.value||countdown.value>0)return;
 errorMessage.value='';
 if(!form.email.trim()){errorMessage.value='请先填写注册邮箱。';return;}
 resendLoading.value=true;
 try{await resendVerification(form.email.trim());rememberVerification(true);code.value='';}
 catch(error){errorMessage.value=error instanceof Error?error.message:'发送失败，请稍后重试。';}
 finally{resendLoading.value=false;}
}
async function submit() {
  errorMessage.value = '';successMessage.value = '';
  if ((mode.value === 'register' || mode.value === 'reset') && form.password !== form.confirmPassword) {errorMessage.value = '两次输入的密码不一致。';return;}
  loading.value = true;
  try {
    if (mode.value === 'register') {
      rememberVerification(false);
      await registerAccount({ nickname: form.nickname.trim(), name: form.name.trim(), email: form.email.trim(), password: form.password, role: form.role });
      rememberVerification(true);await router.push('/verify-email');
    } else if (mode.value === 'verify') {
      const result=await verifyEmail(form.email.trim(),code.value.trim());successMessage.value=result.message;
      sessionStorage.removeItem('medical_pending_verification');sessionStorage.removeItem('medical_verification_sent_at');
    } else if (mode.value === 'forgot') {
      successMessage.value = (await forgotPassword(form.email.trim())).message;
    } else if (mode.value === 'resend') {
      await resendVerification(form.email.trim());rememberVerification(true);await router.push('/verify-email');
    } else if (mode.value === 'reset') {
      const token = typeof route.query.token === 'string' ? route.query.token : '';
      if (!token) throw new Error('重置链接缺少令牌，请重新申请。');
      successMessage.value = (await resetPassword(token, form.password)).message;
    }
  } catch (error) {errorMessage.value = error instanceof Error ? error.message : '操作失败，请稍后重试。';}
  finally {loading.value = false;}
}
watch(() => route.fullPath, () => {
  errorMessage.value = '';successMessage.value = '';form.password = '';form.confirmPassword = '';code.value='';
  try{const pending=JSON.parse(sessionStorage.getItem('medical_pending_verification')||'null');if(pending){form.email=pending.email||'';form.role=pending.role==='teacher'?'teacher':'student';}}catch{/* Ignore invalid browser draft. */}
  if(mode.value==='verify'&&route.query.token)errorMessage.value='验证方式已升级，请使用下方按钮重新获取六位验证码。';
}, { immediate: true });
</script>

<template>
  <main class="account-screen">
    <header>
      <button class="account-brand-lockup" type="button" @click="router.push('/landing')">
        <BrandLogo variant="compact" subtitle="AI 医学解剖与教学知识平台" />
      </button>
      <button class="account-back-button" type="button" @click="router.push('/login')"><ArrowLeft :size="17" /> 返回登录</button>
    </header>

    <section class="account-layout">
      <aside>
        <span class="aside-mark"><Mail :size="28" /></span>
        <h2>账号安全从邮箱验证开始</h2>
        <p>注册验证码为六位数字，10分钟内有效且只能使用一次。找回密码仍使用一次性重置链接。</p>
        <ul><li>密码加密保存</li><li>登录会话自动过期</li><li>重置密码后旧会话失效</li></ul>
      </aside>

      <section class="account-panel">
        <div class="account-heading"><h1>{{ title }}</h1><p>{{ subtitle }}</p></div>

        <div v-if="successMessage" class="status-panel success"><CheckCircle2 :size="34" /><strong>{{ successMessage }}</strong><button type="button" @click="returnToLogin">返回登录</button></div>
        <form v-else class="account-form" @submit.prevent="submit">
          <template v-if="mode === 'register'">
            <div class="role-switch" aria-label="注册身份">
              <button type="button" :class="{ active: form.role === 'student' }" @click="form.role = 'student'"><GraduationCap :size="18" /> 学生</button>
              <button type="button" :class="{ active: form.role === 'teacher' }" @click="form.role = 'teacher'"><Users :size="18" /> 教师</button>
            </div>
            <label><span>姓名</span><div class="field"><UserRound :size="18" /><input v-model="form.name" required minlength="2" maxlength="40" autocomplete="name" placeholder="请输入真实姓名，注册后不可自行修改" /></div><small class="identity-note">教师将通过真实姓名识别学生，请如实填写。</small></label>
            <label><span>昵称</span><div class="field"><UserRound :size="18" /><input v-model="form.nickname" required minlength="1" maxlength="40" autocomplete="nickname" placeholder="支持中文、字母、数字和表情，之后可修改" /></div></label>
          </template>
          <label v-if="mode === 'register' || mode === 'forgot' || mode === 'resend' || mode === 'verify'"><span>邮箱</span><div class="field"><Mail :size="18" /><input v-model="form.email" required type="email" autocomplete="email" placeholder="用于验证和找回密码" /></div></label>
          <template v-if="mode === 'verify'">
            <label><span>六位验证码</span><div class="field"><LockKeyhole :size="18"/><input v-model="code" required type="text" inputmode="numeric" pattern="[0-9]{6}" minlength="6" maxlength="6" autocomplete="one-time-code" placeholder="请输入六位验证码" class="verification-code"/></div></label>
            <div class="code-actions"><small>重发后旧验证码失效</small><button type="button" :disabled="loading||resendLoading||countdown>0" @click="sendAgain">{{resendLoading?'正在发送…':countdown>0?`${countdown}秒后可重发`:'重新获取验证码'}}</button></div>
          </template>
          <template v-if="mode === 'register' || mode === 'reset'">
            <label><span>密码</span><div class="field"><LockKeyhole :size="18" /><input v-model="form.password" required minlength="8" maxlength="120" type="password" :autocomplete="mode === 'reset' ? 'new-password' : 'new-password'" placeholder="至少8位，包含字母和数字" /></div></label>
            <label><span>确认密码</span><div class="field"><LockKeyhole :size="18" /><input v-model="form.confirmPassword" required type="password" autocomplete="new-password" placeholder="再次输入密码" /></div></label>
          </template>
          <p v-if="form.role === 'teacher' && mode === 'register'" class="teacher-note">教师邮箱验证后还需管理员审核才能登录。</p>
          <p v-if="errorMessage" class="error" role="alert">{{ errorMessage }}</p>
          <button class="primary" type="submit" :disabled="loading||resendLoading||(mode==='resend'&&countdown>0)"><LoaderCircle v-if="loading" class="spinner" :size="18" />{{ loading ? '正在提交...' : mode === 'verify' ? '验证邮箱' : mode === 'register' ? '创建账号并发送验证码' : mode === 'forgot' ? '发送重置邮件' : mode === 'resend' ? (countdown>0?`${countdown}秒后可重发`:'发送验证码') : '确认新密码' }}</button>
          <router-link v-if="mode === 'register' && errorMessage" to="/resend-verification">重新发送验证邮件</router-link>
        </form>

      </section>
    </section>
  </main>
</template>

<style scoped>
.identity-note{font-size:12px;color:#64748b;font-weight:400;line-height:1.5}.verification-code{letter-spacing:.25em;font-size:22px!important}.code-actions{display:flex;align-items:center;justify-content:space-between;gap:10px}.code-actions small{font-size:12px;color:#64748b}.code-actions button{border:0;background:transparent;color:#155eef;font-size:13px;cursor:pointer;padding:8px 0}.code-actions button:disabled{color:#94a3b8;cursor:not-allowed}
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
