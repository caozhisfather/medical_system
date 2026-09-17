<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, LoaderCircle, Sparkles } from '@lucide/vue';
import { sendAgentMessage } from '../api';
import { trainingStore } from '../stores/training';

const props = defineProps<{ compact?: boolean }>();
const router = useRouter();
const command = ref('');
const loading = ref(false);
const feedback = ref('');

type LocalIntent = { action: string; target: string; reply: string };

function localIntent(message: string): LocalIntent {
  const role = trainingStore.state.profile.role;
  if (role === 'admin' && /skill|技能|能力管理/i.test(message)) return { action: 'skills', target: '', reply: '正在打开 Skill 管理。' };
  if (role === 'teacher' && /题型|命题|提示词|出题/.test(message)) return { action: 'examSettings', target: '', reply: '正在打开题型与提示词配置。' };
  if (role === 'teacher' && /知识库|教材|资料|依据/.test(message)) return { action: 'knowledgeBase', target: '', reply: '正在打开教学知识库。' };
  if (role === 'admin' && /数据源|ModelScope|知识库|后台|系统/.test(message)) return { action: 'admin', target: '', reply: '正在打开超级管理员控制台。' };
  if (message.includes('解剖') || message.includes('器官') || message.includes('三维') || message.includes('定位') || message.includes('测验')) return { action: 'anatomy', target: '', reply: '正在打开虚拟解剖室。' };
  if (message.includes('检索') || message.includes('指南') || message.includes('关系')) return { action: 'knowledge', target: message.replace(/检索|指南|关系/g, '').trim(), reply: '正在检索知识图谱。' };
  return { action: 'dashboard', target: '', reply: '已返回当前工作台。' };
}

async function execute() {
  const message = command.value.trim();
  if (!message || loading.value) return;
  loading.value = true;
  feedback.value = '';
  let intent = localIntent(message);
  try {
    const result = await sendAgentMessage(message, trainingStore.state.profile.role, 'router');
    if (result.target_module === 'admin') intent = { action: 'admin', target: '', reply: result.reply };
    else if (result.target_module === 'anatomy') intent = { action: 'anatomy', target: result.target_exercise_id ?? '', reply: result.reply };
    else if (result.target_module === 'graph' || result.intent.includes('retrieval')) intent = { action: 'knowledge', target: message, reply: result.reply };
  } catch {
    // Local intent keeps navigation available when the backend is offline.
  }
  feedback.value = intent.reply;
  if (intent.action === 'skills') await router.push('/admin/skills');
  else if (intent.action === 'admin') await router.push('/admin/dashboard');
  else if (intent.action === 'examSettings') await router.push('/teacher/exam-settings');
  else if (intent.action === 'knowledgeBase') await router.push('/teacher/knowledge');
  else if (intent.action === 'anatomy') await router.push({ path: '/student/anatomy', query: intent.target ? { exercise: intent.target } : {} });
  else if (intent.action === 'knowledge') await router.push({ path: '/knowledge-graph', query: { q: intent.target } });
  else await router.push(trainingStore.state.profile.role === 'teacher' ? '/teacher/dashboard' : trainingStore.state.profile.role === 'admin' ? '/admin/dashboard' : '/student/dashboard');
  command.value = '';
  loading.value = false;
}
</script>

<template>
  <div class="agent-command" :class="{ compact }">
    <Sparkles :size="17" aria-hidden="true" />
    <input
      v-model="command"
      aria-label="智能导航指令"
      placeholder="告诉智能体你想训练、复盘或查看什么"
      @keydown.enter.prevent="execute"
    />
    <button type="button" :disabled="loading || !command.trim()" title="执行指令" @click="execute">
      <LoaderCircle v-if="loading" class="spin" :size="17" />
      <ArrowRight v-else :size="17" />
    </button>
    <span v-if="feedback" class="agent-feedback">{{ feedback }}</span>
  </div>
</template>
