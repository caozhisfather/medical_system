<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { Check, ListChecks, LoaderCircle, RotateCcw, Save, Sparkles, TextCursorInput, ToggleLeft, Zap } from '@lucide/vue';
import { getExamSettings, saveExamSettings } from '../api';
import type { ExamSettings } from '../types';

const OPTION_CHOICES = [2, 3, 4, 5];
const DIFFICULTIES: Array<{ id: ExamSettings['difficulty']; label: string; note: string }> = [
  { id: 'basic', label: '基础识记', note: '结构与名称，适合课后自测' },
  { id: 'exam', label: '考试标准', note: '位置、毗邻与功能，对标期末难度' },
  { id: 'clinical', label: '临床应用', note: '结合损伤与病变，适合提高训练' }
];

const GENERATION_MODES: Array<{ id: ExamSettings['generation_mode']; label: string; note: string }> = [
  { id: 'prebuild', label: '预生成题库', note: '提前批量出题，学生答题无需等待，题目可控可复核' },
  { id: 'realtime', label: '实时生成', note: '每个结构现场出题，内容更新鲜，学生需等待数秒' }
];

const settings = ref<ExamSettings | null>(null);
const loading = ref(true);
const saving = ref(false);
const message = ref('');
const error = ref('');

const weightTotal = computed(() => {
  const types = settings.value?.question_types;
  if (!types) return 0;
  return [types.single_choice, types.true_false, types.short_answer]
    .filter((item) => item.enabled)
    .reduce((total, item) => total + (item.weight || 0), 0);
});

const enabledCount = computed(() => {
  const types = settings.value?.question_types;
  if (!types) return 0;
  return [types.single_choice, types.true_false, types.short_answer].filter((item) => item.enabled).length;
});

const generationModeLabel = computed(
  () => GENERATION_MODES.find((item) => item.id === settings.value?.generation_mode)?.label ?? ''
);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    settings.value = await getExamSettings();
  } catch (fetchError) {
    error.value = fetchError instanceof Error ? fetchError.message : '题型配置读取失败';
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!settings.value || saving.value) return;
  saving.value = true;
  message.value = '';
  error.value = '';
  try {
    settings.value = await saveExamSettings(settings.value);
    message.value = '配置已保存，学生下一次测验将按新设置出题。';
  } catch (saveError) {
    error.value = saveError instanceof Error ? saveError.message : '保存失败';
  } finally {
    saving.value = false;
  }
}

function toggleOptionCount(count: number) {
  const single = settings.value?.question_types.single_choice;
  if (!single) return;
  const current = single.option_counts ?? [4];
  single.option_counts = current.includes(count)
    ? current.filter((item) => item !== count)
    : [...current, count].sort((a, b) => a - b);
}

function resetPrompt() {
  if (!settings.value) return;
  settings.value.system_prompt = '';
  message.value = '已清空提示词，保存后恢复系统默认提示词。';
}

onMounted(load);
</script>

<template>
  <div class="workspace-page exam-settings-page">
    <header class="page-title-row">
      <div>
        <span class="section-kicker">教师端 · 命题控制</span>
        <h1>题型与提示词</h1>
        <p>决定虚拟解剖室测验的出题方式。配置保存后即时对学生生效，无需改代码。</p>
      </div>
      <div class="exam-settings-actions">
        <button class="button-secondary" type="button" :disabled="loading || saving" @click="load"><RotateCcw :size="16" />重新读取</button>
        <button class="button-primary" type="button" :disabled="loading || saving || !settings" @click="save">
          <LoaderCircle v-if="saving" class="spin" :size="16" /><Save v-else :size="16" />{{ saving ? '保存中' : '保存配置' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="exam-settings-banner is-error">{{ error }}</p>
    <p v-else-if="message" class="exam-settings-banner is-ok"><Check :size="15" />{{ message }}</p>

    <div v-if="loading" class="exam-settings-loading"><LoaderCircle class="spin" :size="22" />正在读取配置</div>

    <template v-else-if="settings">
      <section class="exam-settings-grid" data-tour="exam-question-types">
        <article class="exam-card">
          <header><ListChecks :size="18" /><div><h2>选择题</h2><small>单选自 {{ settings.question_types.single_choice.option_counts.join(' / ') }} 选一</small></div>
            <label class="exam-switch"><input v-model="settings.question_types.single_choice.enabled" type="checkbox" /><span /></label>
          </header>
          <p>从同一系统或邻近结构中选择干扰项，考察位置与毗邻关系。</p>
          <div class="exam-option-row">
            <button v-for="count in OPTION_CHOICES" :key="count" type="button" :class="{ active: settings.question_types.single_choice.option_counts.includes(count) }" @click="toggleOptionCount(count)">{{ count }} 选 1</button>
          </div>
          <label class="exam-weight">占比 <input v-model.number="settings.question_types.single_choice.weight" type="number" min="0" max="100" /> %</label>
        </article>

        <article class="exam-card">
          <header><ToggleLeft :size="18" /><div><h2>判断题</h2><small>对结构描述作出真伪判断</small></div>
            <label class="exam-switch"><input v-model="settings.question_types.true_false.enabled" type="checkbox" /><span /></label>
          </header>
          <p>适合考察易混淆点，例如左右侧、瓣膜归属与毗邻关系。</p>
          <label class="exam-weight">占比 <input v-model.number="settings.question_types.true_false.weight" type="number" min="0" max="100" /> %</label>
        </article>

        <article class="exam-card">
          <header><TextCursorInput :size="18" /><div><h2>简答题</h2><small>这是什么、有什么功能、会发生什么病变</small></div>
            <label class="exam-switch"><input v-model="settings.question_types.short_answer.enabled" type="checkbox" /><span /></label>
          </header>
          <p>由模型按要点评分，考察结构识别、功能理解与临床联系。</p>
          <label class="exam-weight">占比 <input v-model.number="settings.question_types.short_answer.weight" type="number" min="0" max="100" /> %</label>
        </article>
      </section>

      <section class="exam-panel" data-tour="exam-prompt">
        <header>
          <div><Sparkles :size="18" /><h2>难度基线</h2></div>
          <small>当前启用 {{ enabledCount }} 种题型，权重合计 {{ weightTotal }}%</small>
        </header>
        <div class="exam-difficulty-row">
          <button v-for="item in DIFFICULTIES" :key="item.id" type="button" :class="{ active: settings.difficulty === item.id }" @click="settings.difficulty = item.id">
            <strong>{{ item.label }}</strong><small>{{ item.note }}</small>
          </button>
        </div>
        <p v-if="weightTotal !== 100" class="exam-weight-warning">权重合计为 {{ weightTotal }}%，建议调整为 100% 再保存。</p>
      </section>

      <section class="exam-panel">
        <header>
          <div><Zap :size="18" /><h2>出题方式</h2></div>
          <small>{{ generationModeLabel }}</small>
        </header>
        <div class="exam-difficulty-row">
          <button v-for="item in GENERATION_MODES" :key="item.id" type="button" :class="{ active: settings.generation_mode === item.id }" @click="settings.generation_mode = item.id">
            <strong>{{ item.label }}</strong><small>{{ item.note }}</small>
          </button>
        </div>
      </section>

      <section class="exam-panel">
        <header>
          <div><TextCursorInput :size="18" /><h2>系统提示词</h2></div>
          <div class="exam-prompt-actions">
            <button class="text-button" type="button" @click="resetPrompt">恢复默认</button>
          </div>
        </header>
        <p>这段提示词会作为出题模型的系统指令，决定命题范围、干扰项风格与解析要求。</p>
        <textarea v-model="settings.system_prompt" rows="12" spellcheck="false" placeholder="留空保存后将恢复系统默认提示词" />
        <small class="exam-prompt-meta">{{ settings.system_prompt.length }} / 4000 字符<template v-if="settings.updated_at"> · 上次更新 {{ settings.updated_at.slice(0, 19).replace('T', ' ') }}<template v-if="settings.updated_by"> by {{ settings.updated_by }}</template></template></small>
      </section>
    </template>
  </div>
</template>

<style scoped>
.exam-settings-page { display: grid; gap: 16px; align-content: start; }
.exam-settings-actions { display: flex; gap: 8px; }
.exam-settings-banner { display: flex; align-items: center; gap: 6px; margin: 0; padding: 10px 12px; border-radius: 7px; font-size: 13px; }
.exam-settings-banner.is-ok { background: #e6f4ef; color: #1c6b53; }
.exam-settings-banner.is-error { background: #fdecea; color: #a4342a; }
.exam-settings-loading { display: flex; align-items: center; gap: 8px; padding: 28px; color: #5d757a; }
.exam-settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
.exam-card { display: grid; gap: 8px; padding: 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #fff; }
.exam-card > header { display: grid; grid-template-columns: 22px minmax(0,1fr) auto; align-items: center; gap: 8px; }
.exam-card h2 { margin: 0; color: #214b51; font-size: 15px; }
.exam-card small { color: #7b8f93; font-size: 11px; }
.exam-card > p { margin: 0; color: #5d757a; font-size: 12px; line-height: 1.6; }
.exam-option-row { display: flex; flex-wrap: wrap; gap: 6px; }
.exam-option-row button { padding: 6px 10px; border: 1px solid var(--line, #e1e9ea); border-radius: 6px; background: #f7faf9; color: #4b6b70; font-size: 12px; cursor: pointer; }
.exam-option-row button.active { border-color: rgba(15,118,110,.45); background: #e4f1ee; color: var(--teal, #0f766e); font-weight: 700; }
.exam-weight { display: inline-flex; align-items: center; gap: 6px; color: #5d757a; font-size: 12px; }
.exam-weight input { width: 62px; padding: 5px 7px; border: 1px solid var(--line, #e1e9ea); border-radius: 6px; font-size: 12px; }
.exam-switch { position: relative; display: inline-flex; width: 42px; height: 24px; flex: 0 0 auto; }
.exam-switch input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.exam-switch span { width: 100%; border-radius: 999px; background: #d5e0e1; transition: background .15s ease; }
.exam-switch span::after { content: ''; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform .15s ease; }
.exam-switch input:checked + span { background: var(--teal, #0f766e); }
.exam-switch input:checked + span::after { transform: translateX(18px); }
.exam-panel { display: grid; gap: 10px; padding: 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #fff; }
.exam-panel > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.exam-panel > header > div { display: flex; align-items: center; gap: 8px; }
.exam-panel h2 { margin: 0; color: #214b51; font-size: 15px; }
.exam-panel > header small { color: #7b8f93; font-size: 11px; }
.exam-panel > p { margin: 0; color: #5d757a; font-size: 12px; line-height: 1.6; }
.exam-difficulty-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
.exam-difficulty-row button { display: grid; gap: 3px; padding: 10px 12px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #f7faf9; color: #466066; text-align: left; cursor: pointer; }
.exam-difficulty-row button strong { font-size: 13px; }
.exam-difficulty-row button small { color: #7b8f93; font-size: 11px; }
.exam-difficulty-row button.active { border-color: rgba(15,118,110,.45); background: #e4f1ee; }
.exam-difficulty-row button.active strong { color: var(--teal, #0f766e); }
.exam-weight-warning { margin: 0; color: #a4681c; font-size: 12px; }
.exam-panel textarea { width: 100%; padding: 12px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fbfdfd; color: #2f4f56; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; line-height: 1.65; resize: vertical; }
.exam-prompt-meta { color: #93a4a7; font-size: 11px; }
</style>
