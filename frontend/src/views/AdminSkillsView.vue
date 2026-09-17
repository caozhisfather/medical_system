<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { FlaskConical, LoaderCircle, RefreshCw, Save, ShieldCheck, X } from '@lucide/vue';
import { getAdminSkills, getSkillCalls, testSkill, updateSkill } from '../api';
import type { SkillCall, SkillDefinition, SkillPolicy, SkillResult, SkillRole } from '../types';

const skills = ref<SkillDefinition[]>([]);
const calls = ref<SkillCall[]>([]);
const drafts = reactive<Record<string, SkillPolicy>>({});
const roles: { id: SkillRole; name: string }[] = [{ id: 'student', name: '学生' }, { id: 'teacher', name: '教师' }, { id: 'admin', name: '管理员' }];
const statuses: Record<string, string> = { success: '成功', empty: '无匹配', disabled: '未启用', forbidden: '无权限', rate_limited: '额度耗尽', error: '失败', running: '执行中' };
const loading = ref(false);
const saving = ref('');
const testing = ref(false);
const selectedId = ref('');
const query = ref('心脏');
const testResult = ref<SkillResult | null>(null);
const error = ref('');
const notice = ref('');

function draft(skill: SkillDefinition): SkillPolicy { return { enabled: skill.enabled, allowed_roles: [...skill.allowed_roles], hourly_limit: skill.hourly_limit }; }
function dirty(skill: SkillDefinition) {
  const value = drafts[skill.id];
  return value && (value.enabled !== skill.enabled || value.hourly_limit !== skill.hourly_limit || [...value.allowed_roles].sort().join() !== [...skill.allowed_roles].sort().join());
}
async function load() {
  loading.value = true;
  error.value = '';
  try {
    const result = await getAdminSkills();
    skills.value = result;
    result.forEach(skill => { drafts[skill.id] = draft(skill); });
    calls.value = (await getSkillCalls()).items;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'Skill 管理暂时不可用'; }
  finally { loading.value = false; }
}
async function save(skill: SkillDefinition) {
  if (saving.value) return;
  saving.value = skill.id;
  error.value = ''; notice.value = '';
  try {
    const updated = await updateSkill(skill.id, drafts[skill.id]);
    skills.value = skills.value.map(item => item.id === skill.id ? updated : item);
    drafts[skill.id] = draft(updated);
    notice.value = `${skill.name}已保存`;
    testResult.value = null;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '保存失败'; }
  finally { saving.value = ''; }
}
function selectTest(id: string) { selectedId.value = id; testResult.value = null; }
async function runTest() {
  if (testing.value || !query.value.trim()) return;
  testing.value = true; error.value = ''; testResult.value = null;
  try {
    testResult.value = await testSkill(selectedId.value, { query: query.value.trim() });
    calls.value = (await getSkillCalls()).items;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : '测试失败'; }
  finally { testing.value = false; }
}
onMounted(load);
</script>

<template>
  <div class="workspace-page skill-admin">
    <header class="skill-page-heading">
      <div><span class="section-kicker">管理员控制台</span><h1>Skill 管理</h1></div>
      <button class="skill-icon" type="button" title="刷新" aria-label="刷新 Skill 列表" :disabled="loading || !!saving || testing" @click="load"><LoaderCircle v-if="loading" class="skill-spin" :size="18" /><RefreshCw v-else :size="18" /></button>
    </header>
    <p v-if="error" class="skill-message error" role="alert">{{ error }}</p>
    <p v-if="notice" class="skill-message" role="status">{{ notice }}</p>
    <div class="skill-section-heading"><h2>预置能力</h2><span><ShieldCheck :size="16" />只读 · {{ skills.filter(skill => skill.enabled).length }}/{{ skills.length }} 已启用</span></div>
    <div v-if="loading && !skills.length" class="skill-empty" role="status">正在加载...</div>
    <div v-else-if="!skills.length" class="skill-empty">暂无可用 Skill</div>
    <div v-else class="skill-table-scroll">
      <table class="skill-table">
        <thead><tr><th>能力 / 数据源</th><th>启用</th><th>允许角色</th><th>每账号额度 / 小时</th><th>更新记录</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="skill in skills" :key="skill.id">
            <td><strong>{{ skill.name }}</strong><code>{{ skill.id }} · v{{ skill.version }}</code><small>{{ skill.source }}</small></td>
            <td><input v-model="drafts[skill.id].enabled" type="checkbox" role="switch" :aria-label="`${skill.name}启用`" :disabled="loading || !!saving || testing" /></td>
            <td><div class="skill-role-options"><label v-for="role in roles" :key="role.id"><input v-model="drafts[skill.id].allowed_roles" type="checkbox" :value="role.id" :aria-label="`${skill.name}允许${role.name}`" :disabled="loading || !!saving || testing" />{{ role.name }}</label></div></td>
            <td><input v-model.number="drafts[skill.id].hourly_limit" class="skill-limit" type="number" min="1" max="1000" step="1" :aria-label="`${skill.name}小时额度`" :disabled="loading || !!saving || testing" /></td>
            <td><small>{{ skill.updated_by || '尚未配置' }}</small><small v-if="skill.updated_at">{{ new Date(skill.updated_at).toLocaleString('zh-CN', { hour12: false }) }}</small></td>
            <td><div class="skill-row-actions"><button class="skill-icon" type="button" :title="`保存${skill.name}`" :aria-label="`保存${skill.name}`" :disabled="loading || !!saving || testing || !dirty(skill)" @click="save(skill)"><LoaderCircle v-if="saving === skill.id" class="skill-spin" :size="17" /><Save v-else :size="17" /></button><button class="skill-icon" type="button" :title="`测试${skill.name}`" :aria-label="`测试${skill.name}`" :disabled="loading || !!saving || testing || dirty(skill)" @click="selectTest(skill.id)"><FlaskConical :size="17" /></button></div></td>
          </tr>
        </tbody>
      </table>
    </div>
    <section v-if="selectedId" class="skill-test-section">
      <div class="skill-section-heading"><h2>{{ skills.find(skill => skill.id === selectedId)?.name }} · 测试</h2><button class="skill-icon" title="关闭测试" aria-label="关闭测试" :disabled="testing" @click="selectedId = ''"><X :size="17" /></button></div>
      <form class="skill-test-form" @submit.prevent="runTest"><label>检索词<input v-model="query" required maxlength="200" :disabled="testing" /></label><button class="button-primary" type="submit" :disabled="testing || !!saving || loading || !query.trim()"><LoaderCircle v-if="testing" class="skill-spin" :size="17" /><FlaskConical v-else :size="17" />运行测试</button></form>
      <div v-if="testResult" class="skill-test-result" role="status"><strong>{{ statuses[testResult.status] }} · {{ testResult.duration_ms }} ms</strong><p>{{ testResult.message }}</p><p v-for="citation in testResult.citations" :key="citation.reference">{{ citation.reference }}</p><details v-if="Object.keys(testResult.data).length"><summary>检索结果</summary><pre>{{ JSON.stringify(testResult.data, null, 2) }}</pre></details></div>
    </section>
    <section class="skill-call-section">
      <div class="skill-section-heading"><h2>最近调用</h2><button class="skill-icon" title="刷新调用记录" aria-label="刷新调用记录" :disabled="loading || !!saving || testing" @click="load"><RefreshCw :size="17" /></button></div>
      <p v-if="!calls.length" class="skill-empty">暂无调用记录</p>
      <div v-else class="skill-table-scroll"><table class="skill-table call-table"><thead><tr><th>时间</th><th>账号 / 角色</th><th>Skill</th><th>状态</th><th>耗时</th><th>结果</th></tr></thead><tbody><tr v-for="call in calls" :key="call.id"><td>{{ new Date(call.created_at).toLocaleString('zh-CN', { hour12: false }) }}</td><td>{{ call.account }}<small>{{ roles.find(role => role.id === call.role)?.name || call.role }}</small></td><td><code>{{ call.skill_id }}</code></td><td><span :class="['skill-call-status', call.status]">{{ statuses[call.status] || call.status }}</span></td><td>{{ call.duration_ms }} ms</td><td>{{ call.message }}</td></tr></tbody></table></div>
    </section>
  </div>
</template>

<style scoped>
.skill-admin { min-width: 0; color: #173b3f; }
.skill-page-heading, .skill-section-heading { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.skill-page-heading { padding-bottom: 24px; border-bottom: 1px solid #dbe3e5; }
.skill-page-heading h1 { margin: 6px 0 0; font-size: 28px; letter-spacing: 0; }
.skill-section-heading { margin: 24px 0 14px; }
.skill-section-heading h2 { margin: 0; font-size: 18px; }
.skill-section-heading > span { display: inline-flex; align-items: center; gap: 6px; color: #526a71; font-size: 13px; }
.skill-icon { display: grid; place-items: center; flex: 0 0 36px; width: 36px; height: 36px; padding: 0; border: 1px solid #cdd9dd; border-radius: 6px; background: #fff; color: #2c6666; }
.skill-icon:disabled { opacity: .45; cursor: default; }
.skill-icon:focus-visible { outline: 3px solid #76b7b7; outline-offset: 2px; }
.skill-table-scroll { max-width: 100%; overflow: auto; }
.skill-table { width: 100%; min-width: 900px; border-collapse: collapse; background: #fff; text-align: left; font-size: 13px; }
.skill-table th { padding: 12px; background: #f0f5f7; color: #576e76; font-size: 12px; white-space: nowrap; }
.skill-table td { padding: 16px 12px; border-bottom: 1px solid #e0e7e9; vertical-align: middle; }
.skill-table strong, .skill-table small, .skill-table td > code { display: block; }
.skill-table small { margin-top: 6px; color: #60787d; }
.skill-table code { margin-top: 6px; font-size: 12px; color: #596b78; overflow-wrap: anywhere; }
.skill-role-options { display: flex; gap: 12px; white-space: nowrap; }
.skill-role-options label { display: flex; align-items: center; gap: 5px; }
.skill-table input[type=checkbox] { width: 17px; height: 17px; accent-color: #117e72; }
.skill-limit { width: 84px; height: 36px; padding: 0 8px; border: 1px solid #cdd9dd; border-radius: 4px; }
.skill-row-actions { display: flex; gap: 6px; }
.skill-message { padding: 12px; border-left: 3px solid #17856f; background: #eef8f3; font-size: 14px; }
.skill-message.error { border-color: #b84b39; background: #fff3ee; color: #963e2b; }
.skill-empty { padding: 24px 0; color: #6c8087; }
.skill-test-section, .skill-call-section { border-top: 1px solid #dbe3e5; margin-top: 28px; }
.skill-test-form { display: flex; align-items: end; flex-wrap: wrap; gap: 14px; }
.skill-test-form label { display: grid; gap: 7px; flex: 1 1 240px; max-width: 440px; font-size: 13px; }
.skill-test-form input { min-width: 0; height: 40px; padding: 8px 12px; border: 1px solid #cdd9dd; border-radius: 4px; }
.skill-test-result { margin-top: 18px; font-size: 14px; }
.skill-test-result pre { max-height: 320px; overflow: auto; padding: 14px; background: #f1f5f7; font-size: 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
.skill-call-status { color: #61737b; white-space: nowrap; }
.skill-call-status.success { color: #087459; }.skill-call-status.error, .skill-call-status.forbidden { color: #a84632; }.skill-call-status.rate_limited { color: #936500; }
.skill-spin { animation: skill-spin 1s linear infinite; } @keyframes skill-spin { to { transform: rotate(360deg); } }
@media (max-width: 760px) { .skill-page-heading h1 { font-size: 24px; }.skill-section-heading { flex-wrap: wrap; } }
@media (prefers-reduced-motion: reduce) { .skill-spin { animation: none; } }
</style>
