<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, ArrowRight, Box, Layers3, Network, Monitor, Mail, Eye, EyeOff, GraduationCap, LoaderCircle, LockKeyhole, ShieldCheck, UserRound, Users } from '@lucide/vue';
import loginLab from '../assets/medical/login-lab-reference.webp';
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
  <main class="login-screen login-reference">
    <section class="login-stage">
      <figure class="login-context">
        <img :src="loginLab" alt="医学实验室中的解剖模型、教材与三维教学电脑" />
        <figcaption>
          <strong>身份清晰 · 权限可控</strong><i class="login-caption-rule" aria-hidden="true"></i>
          <p>进入虚拟解剖实验室，开展三维结构探索、空间定位测验与知识图谱学习。</p>
          <div class="login-context-features"><span><Box :size="31"/>三维结构交互</span><span><Layers3 :size="31"/>实验测验训练</span><span><Network :size="31"/>教学数据管理</span></div>
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
            <div class="login-input"><UserRound :size="18" /><input v-model="form.account" name="username" autocomplete="username" autofocus required placeholder="请输入邮箱 / 原有账号" /></div>
          </label>
          <label>
            <span>密码</span>
            <div class="login-input"><LockKeyhole :size="18" /><input v-model="form.password" name="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" required placeholder="请输入密码" /><button type="button" :title="showPassword ? '隐藏密码' : '显示密码'" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword"><EyeOff v-if="showPassword" :size="18" /><Eye v-else :size="18" /></button></div>
          </label>

          <div class="login-options">
            <label class="remember-account"><input v-model="form.remember" type="checkbox" /> <span>记住账号</span></label>
            <router-link to="/forgot-password">忘记密码？</router-link>
          </div>
          <p v-if="errorMessage" class="login-error" role="alert">{{ errorMessage }}</p>

          <button class="login-submit" type="submit" :disabled="loading">
            <LoaderCircle v-if="loading" class="login-spinner" :size="18" />
            <span>{{ loading ? '正在验证...' : '登录并进入工作台' }}</span>
            <ArrowRight v-if="!loading" :size="18" />
          </button>
        </form>

        <p class="register-entry">还没有账号？ <router-link to="/register">通过邮箱注册</router-link></p>
        <p class="register-entry verification-entry"><router-link to="/resend-verification"><Mail :size="22"/>重新发送验证邮件</router-link></p>

        <div class="demo-account">
          <Monitor class="demo-monitor" :size="32"/><span><strong>教学演示账号</strong><small>{{ roleMeta.accountHint }} · {{ roleOptions.find(item=>item.value===role)?.label }}（演示数据）</small></span>
          <button type="button" @click="fillDemoAccount">填入账号</button>
        </div>
        <router-link class="login-home" to="/landing"><ArrowLeft :size="15"/>返回首页</router-link>
      </section>
    </section>
  </main>
</template>

<style scoped src="./login-reference.css"></style>
