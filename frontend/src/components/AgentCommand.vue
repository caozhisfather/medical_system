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
  if (role === 'student' && /复盘|今天哪里|哪里做得不好|明日计划|今日总结/.test(message)) return { action: 'dailyReview', target: '', reply: '正在打开每日复盘，并生成今日总结、薄弱点和明日计划。' };
  if (role === 'teacher' && /班级复盘|复盘|教学建议|今日班级/.test(message)) return { action: 'classReview', target: '', reply: '正在打开班级复盘，查看共性薄弱点和教学建议。' };
  if (role === 'admin' && /复盘策略|复盘配置|教师预警|生成时间/.test(message)) return { action: 'adminReview', target: '', reply: '正在打开复盘策略配置。' };
  if (role === 'admin' && /数据源|ModelScope|知识库|后台|系统/.test(message)) return { action: 'admin', target: '', reply: '正在打开超级管理员控制台。' };
  if (message.includes('解剖') || message.includes('器官') || message.includes('定位')) return { action: 'anatomy', target: '', reply: '正在打开解剖定位训练。' };
  if (message.includes('随机') && (message.includes('呼吸') || message.includes('气促'))) {
    const candidates = trainingStore.state.cases.filter((item) => item.department.includes('呼吸') || item.symptom_tags?.includes('呼吸困难'));
    const selected = candidates[Math.floor(Math.random() * candidates.length)];
    if (selected) return { action: 'case', target: selected.id, reply: `已随机抽取${selected.title}病例。` };
  }
  const matchedCase = trainingStore.state.cases.find((item) => [item.title, item.chief_complaint, ...(item.symptom_tags ?? [])].some((keyword) => keyword && message.includes(keyword)));
  if (matchedCase) return { action: 'case', target: matchedCase.id, reply: `已定位${matchedCase.title}病例。` };
  if (message.includes('上次') && message.includes('报告')) return { action: 'report', target: trainingStore.lastReport.value.id, reply: '正在打开上次训练报告。' };
  if (message.includes('薄弱') || message.includes('班级')) return { action: 'teacher', target: '', reply: '正在打开班级薄弱项分析。' };
  if (message.includes('检索') || message.includes('问诊要点') || message.includes('指南')) return { action: 'knowledge', target: message.replace(/检索|问诊要点|指南/g, '').trim(), reply: '正在检索指南知识网络。' };
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
    if (result.target_module === 'daily_review') intent = { action: 'dailyReview', target: '', reply: result.reply };
    else if (result.target_module === 'class_review') intent = { action: 'classReview', target: '', reply: result.reply };
    else if (result.target_module === 'admin_review') intent = { action: 'adminReview', target: '', reply: result.reply };
    else if (result.target_module === 'admin') intent = { action: 'admin', target: '', reply: result.reply };
    else if (result.target_case_id) intent = { action: 'case', target: result.target_case_id, reply: result.reply };
    else if (result.target_module === 'anatomy') intent = { action: 'anatomy', target: result.target_exercise_id ?? '', reply: result.reply };
    else if (result.target_module === 'report') intent = { action: 'report', target: trainingStore.lastReport.value.id, reply: result.reply };
    else if (result.target_module === 'teacher') intent = { action: 'teacher', target: '', reply: result.reply };
    else if (result.target_module === 'graph' || result.intent.includes('retrieval')) intent = { action: 'knowledge', target: message, reply: result.reply };
  } catch {
    // Local intent keeps navigation available when the backend is offline.
  }
  feedback.value = intent.reply;
  if (intent.action === 'dailyReview') await router.push({ path: '/student/daily-review', query: { source: 'agent' } });
  else if (intent.action === 'classReview') await router.push('/teacher/class-review');
  else if (intent.action === 'adminReview' || intent.action === 'admin') await router.push('/admin/dashboard');
  else if (intent.action === 'case') await router.push({ path: '/student/case/new', query: { case: intent.target } });
  else if (intent.action === 'anatomy') await router.push({ path: '/student/anatomy', query: intent.target ? { exercise: intent.target } : {} });
  else if (intent.action === 'report') await router.push(`/training-report/${intent.target}`);
  else if (intent.action === 'teacher') await router.push('/teacher/reports');
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