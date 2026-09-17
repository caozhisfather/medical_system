<script setup lang="ts">
import { BookOpenCheck, GitBranch, LocateFixed } from '@lucide/vue';
import type { AgentAction, AgentResponse } from '../../types';
defineProps<{ response: AgentResponse }>();
const emit = defineEmits<{ action: [value: AgentAction] }>();
const statuses: Record<string, string> = { success: '成功', empty: '无匹配', disabled: '未启用', forbidden: '无权限', rate_limited: '额度耗尽', error: '失败' };
</script>
<template>
  <div class="agent-evidence">
    <div v-if="response.actions?.length" class="evidence-actions"><button v-for="action in response.actions" :key="`${action.type}-${action.target}`" type="button" @click="emit('action', action)"><LocateFixed v-if="action.type === 'highlight_structure'" :size="15" /><GitBranch v-else-if="action.type === 'open_graph'" :size="15" /><BookOpenCheck v-else :size="15" />{{ action.type === 'highlight_structure' ? `定位 ${action.label}` : action.label }}</button></div>
    <ul v-if="response.citations?.length" class="evidence-citations"><li v-for="citation in response.citations" :key="citation.reference">{{ citation.reference }}</li></ul>
    <details v-if="response.skill_results?.length"><summary>调用记录 · {{ response.skill_results.length }}</summary><ul class="evidence-trace"><li v-for="result in response.skill_results" :key="result.call_id"><strong>{{ result.skill_id }}</strong><span>{{ statuses[result.status] }} · {{ result.duration_ms }} ms</span><small>{{ result.message }}</small></li></ul></details>
  </div>
</template>
<style scoped>
.agent-evidence { margin-top: 12px; min-width: 0; font-size: 12px; }
.evidence-actions { display: flex; flex-wrap: wrap; gap: 6px; }
.evidence-actions button { display: inline-flex; align-items: center; gap: 5px; max-width: 100%; min-height: 32px; padding: 6px 8px; border: 1px solid #bcd9d4; border-radius: 4px; background: #fff; color: #16685c; font-size: 12px; text-align: left; overflow-wrap: anywhere; }
.evidence-citations, .evidence-trace { display: grid; gap: 8px; padding: 0; list-style: none; color: #57757c; overflow-wrap: anywhere; }
.evidence-trace li { display: grid; gap: 4px; padding: 8px 0; border-bottom: 1px solid #d9e6e4; }
.evidence-trace strong { font-size: 12px; }.evidence-trace small { font-size: 12px; }
summary { cursor: pointer; color: #315b65; }
</style>
