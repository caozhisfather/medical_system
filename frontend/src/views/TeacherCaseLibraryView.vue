<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  AlertTriangle,
  BookOpenCheck,
  CheckCircle2,
  Database,
  Eye,
  FilePenLine,
  Library,
  LoaderCircle,
  Plus,
  Save,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  X
} from '@lucide/vue';
import {
  createCaseLibraryEntry,
  createTeachingKnowledge,
  deidentifyCaseText,
  deleteTeachingKnowledge,
  getTeachingKnowledge,
  importCaseLibrary,
  updateTeachingKnowledge
} from '../api';
import type { CaseLibraryDeidentifyResult, CaseLibraryEntry } from '../types';

const emit = defineEmits<{ compile: [payload: { entry_ids: string[]; publish_immediately: boolean }] }>();

interface EntryForm {
  title: string;
  category: string;
  diagnosis: string;
  chief_complaint: string;
  present_illness: string;
  content: string;
  source: string;
}

function emptyForm(): EntryForm {
  return { title: '', category: '', diagnosis: '', chief_complaint: '', present_illness: '', content: '', source: '教师手工录入' };
}

const entries = ref<CaseLibraryEntry[]>([]);
const categories = ref<Record<string, number>>({});
const loading = ref(false);
const notice = ref('');
const query = ref('');
const categoryFilter = ref('');
const knowledgeTypeFilter = ref<'all' | 'case' | 'textbook'>('all');
const filterKind = ref<'all' | 'anonymized' | 'risk'>('all');
const selectedId = ref('');
const editing = ref(false);
const saving = ref(false);
const showCreate = ref(false);
const previewing = ref(false);
const importing = ref(false);
const selectedIds = ref<string[]>([]);
const compilePublish = ref(false);
const createForm = ref<EntryForm>(emptyForm());
const editForm = ref<EntryForm>(emptyForm());
const preview = ref<CaseLibraryDeidentifyResult | null>(null);

const selected = computed(() => entries.value.find((item) => item.id === selectedId.value) || null);

function hasRisk(item: CaseLibraryEntry) {
  return (item.risk_flags || []).some((flag) => flag.startsWith('疑似'));
}

const filteredEntries = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  return entries.value.filter((item) => {
    if (categoryFilter.value && item.category !== categoryFilter.value) return false;
    if (filterKind.value === 'anonymized' && !item.anonymized) return false;
    if (filterKind.value === 'risk' && !hasRisk(item)) return false;
    if (!keyword) return true;
    return [item.title, item.category, item.diagnosis, item.chief_complaint, item.present_illness].join(' ').toLowerCase().includes(keyword);
  });
});

const riskCount = computed(() => entries.value.filter(hasRisk).length);
const anonymizedCount = computed(() => entries.value.filter((item) => item.anonymized).length);

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false });
}

async function load() {
  loading.value = true;
  try {
    const data = await getTeachingKnowledge({ knowledge_type: knowledgeTypeFilter.value === 'all' ? '' : knowledgeTypeFilter.value });
    entries.value = data.items;
    categories.value = data.categories;
    if (!selectedId.value || !entries.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = entries.value[0]?.id || '';
    }
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '病例知识库加载失败，请检查后端服务。';
  } finally {
    loading.value = false;
  }
}

function selectEntry(entryId: string) {
  selectedId.value = entryId;
  editing.value = false;
}

function toggleSelect(entryId: string) {
  const entry = entries.value.find((item) => item.id === entryId);
  if (entry?.knowledge_type === 'textbook') return;
  const index = selectedIds.value.indexOf(entryId);
  if (index >= 0) selectedIds.value.splice(index, 1);
  else selectedIds.value.push(entryId);
}

function compileSelected() {
  if (!selectedIds.value.length) return;
  emit('compile', { entry_ids: [...selectedIds.value], publish_immediately: compilePublish.value });
}

function beginEdit() {
  if (!selected.value) return;
  editForm.value = {
    title: selected.value.title,
    category: selected.value.category,
    diagnosis: selected.value.diagnosis,
    chief_complaint: selected.value.chief_complaint,
    present_illness: selected.value.present_illness,
    content: selected.value.content,
    source: selected.value.source
  };
  editing.value = true;
}

async function saveEdit() {
  if (!selected.value) return;
  saving.value = true;
  try {
    await updateTeachingKnowledge(selected.value.id, { ...editForm.value });
    editing.value = false;
    notice.value = '病例知识库条目已更新，敏感字段已重新脱敏。';
    await load();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '保存失败，请重试。';
  } finally {
    saving.value = false;
  }
}

async function removeEntry() {
  if (!selected.value) return;
  if (!window.confirm(`确定删除「${selected.value.title}」吗？此操作会同时写入审计日志。`)) return;
  try {
    await deleteTeachingKnowledge(selected.value.id);
    selectedId.value = '';
    notice.value = '病例知识库条目已删除。';
    await load();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '删除失败，请重试。';
  }
}

function openCreate() {
  createForm.value = emptyForm();
  preview.value = null;
  showCreate.value = true;
}

async function runPreview() {
  previewing.value = true;
  try {
    const text = [createForm.value.chief_complaint, createForm.value.present_illness, createForm.value.content].filter(Boolean).join('\n');
    preview.value = await deidentifyCaseText(text);
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '脱敏预览失败。';
  } finally {
    previewing.value = false;
  }
}

async function saveCreate() {
  if (!createForm.value.title.trim() || !createForm.value.category.trim()) {
    notice.value = '请至少填写病例名称和分类。';
    return;
  }
  saving.value = true;
  try {
    await createTeachingKnowledge({ ...createForm.value, knowledge_type: knowledgeTypeFilter.value === 'textbook' ? 'textbook' : 'case' });
    showCreate.value = false;
    notice.value = '新病例已脱敏并写入知识库。';
    await load();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '新增失败，请重试。';
  } finally {
    saving.value = false;
  }
}

async function runImport() {
  importing.value = true;
  notice.value = '';
  try {
    const report = await importCaseLibrary();
    notice.value = `素材导入完成：新增 ${report.imported} 条，扫描 ${report.scanned_files} 个文件，跳过 ${report.skipped} 条。`;
    await load();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '素材导入失败。';
  } finally {
    importing.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="case-library-panel">
    <div class="case-library-toolbar">
      <div class="case-library-actions">
        <button class="button-secondary" type="button" :disabled="importing" @click="runImport">
          <LoaderCircle v-if="importing" class="spin" :size="17" /><Database v-else :size="17" />{{ importing ? '正在导入素材' : '导入本地素材' }}
        </button>
        <button class="button-primary" type="button" @click="openCreate"><Plus :size="17" />新增知识条目</button>
      </div>
      <div class="case-library-compile">
        <label class="compile-publish-toggle"><input v-model="compilePublish" type="checkbox" />整合后直接发布</label>
        <button class="button-primary ai-compile" type="button" :disabled="!selectedIds.length" @click="compileSelected"><Sparkles :size="16" />AI 整合为训练病例（{{ selectedIds.length }}）</button>
      </div>
    </div>

    <div v-if="notice" class="teacher-case-notice"><CheckCircle2 :size="17" />{{ notice }}<button type="button" title="关闭" @click="notice = ''"><X :size="15" /></button></div>

    <section class="case-library-stats">
      <article><Library :size="18" /><span><strong>{{ entries.length }}</strong><small>教学知识条目</small></span></article>
      <article><ShieldCheck :size="18" /><span><strong>{{ anonymizedCount }}</strong><small>已完成脱敏</small></span></article>
      <article><Database :size="18" /><span><strong>{{ Object.keys(categories).length }}</strong><small>疾病分类</small></span></article>
      <article :class="{ warning: riskCount > 0 }"><AlertTriangle :size="18" /><span><strong>{{ riskCount }}</strong><small>疑似残留风险</small></span></article>
    </section>

    <div class="teacher-case-layout case-library-layout">
      <section class="case-management-list case-library-list">
        <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="搜索病例、教材或知识内容" /></label>
        <div class="knowledge-type-tabs">
          <button type="button" :class="{ active: knowledgeTypeFilter === 'all' }" @click="knowledgeTypeFilter = 'all'; load()">全部</button>
          <button type="button" :class="{ active: knowledgeTypeFilter === 'case' }" @click="knowledgeTypeFilter = 'case'; load()">病例</button>
          <button type="button" :class="{ active: knowledgeTypeFilter === 'textbook' }" @click="knowledgeTypeFilter = 'textbook'; load()">教材</button>
        </div>
        <label class="case-library-category">
          <span>分类</span>
          <select v-model="categoryFilter">
            <option value="">全部分类</option>
            <option v-for="(count, name) in categories" :key="name" :value="name">{{ name }}（{{ count }}）</option>
          </select>
        </label>
        <div class="case-list-tabs">
          <button type="button" :class="{ active: filterKind === 'all' }" @click="filterKind = 'all'">全部</button>
          <button type="button" :class="{ active: filterKind === 'anonymized' }" @click="filterKind = 'anonymized'">已脱敏</button>
          <button type="button" :class="{ active: filterKind === 'risk' }" @click="filterKind = 'risk'">需复核</button>
        </div>
        <div class="case-management-scroll">
          <div v-if="loading" class="case-library-empty"><LoaderCircle class="spin" :size="22" />正在加载知识库</div>
          <button v-for="item in filteredEntries" v-else :key="item.id" type="button" :class="{ active: selectedId === item.id, 'entry-selected': selectedIds.includes(item.id) }" @click="selectEntry(item.id)">
            <input class="entry-checkbox" type="checkbox" :disabled="item.knowledge_type === 'textbook'" :checked="selectedIds.includes(item.id)" :aria-label="`选择${item.title}`" @click.stop="toggleSelect(item.id)" />
            <span><strong>{{ item.title }}</strong><small>{{ item.knowledge_type === 'textbook' ? '教材 · ' + (item.chapter || item.category) : item.category + ' · ' + (item.diagnosis || '待确认诊断') }}</small></span>
            <b :class="{ risk: hasRisk(item) }">{{ hasRisk(item) ? '需复核' : item.status }}</b>
          </button>
          <div v-if="!loading && !filteredEntries.length" class="case-library-empty"><Library :size="22" />暂无匹配条目</div>
        </div>
      </section>

      <section v-if="selected" class="case-editor teacher-case-editor case-library-detail">
        <header>
          <div><span class="section-kicker">{{ selected.knowledge_type === 'textbook' ? '教材知识条目' : '去标识化教学病例' }}</span><h2>{{ selected.title }}</h2><p>{{ selected.category }} · {{ selected.diagnosis || selected.source }}</p></div>
          <div v-if="!editing">
            <button class="button-primary" type="button" @click="beginEdit"><FilePenLine :size="16" />编辑</button>
            <button class="button-secondary danger" type="button" @click="removeEntry"><Trash2 :size="16" />删除</button>
          </div>
        </header>

        <form v-if="editing" class="teacher-case-edit-form case-library-edit-form" @submit.prevent="saveEdit">
          <div>
            <label>病例名称<input v-model="editForm.title" /></label>
            <label>疾病分类<input v-model="editForm.category" list="category-options" /><datalist id="category-options"><option v-for="name in Object.keys(categories)" :key="name" :value="name" /></datalist></label>
          </div>
          <div>
            <label>主要诊断<input v-model="editForm.diagnosis" /></label>
            <label>来源<input v-model="editForm.source" /></label>
          </div>
          <label>主诉<input v-model="editForm.chief_complaint" /></label>
          <label>现病史<textarea v-model="editForm.present_illness" rows="3" /></label>
          <label>病例全文<textarea v-model="editForm.content" rows="8" /></label>
          <footer><button class="button-secondary" type="button" @click="editing = false"><X :size="16" />取消</button><button class="button-primary" type="submit" :disabled="saving"><LoaderCircle v-if="saving" class="spin" :size="16" /><Save v-else :size="16" />保存修改</button></footer>
        </form>

        <template v-else>
          <div class="case-library-badges">
            <span class="privacy-ok"><ShieldCheck :size="15" />已脱敏</span>
            <span v-for="kind in selected.pii_removed" :key="kind" class="pii-kind">{{ kind }}</span>
            <span v-if="selected.imported" class="imported-kind">素材导入</span>
            <span v-if="selected.knowledge_type === 'textbook'" :class="['embedding-badge', selected.embedding_status === '已生成' ? 'ready' : 'pending']">{{ selected.embedding_status || '待生成' }}</span>
          </div>
          <div v-if="hasRisk(selected)" class="case-library-risk"><AlertTriangle :size="16" /><span>{{ selected.risk_flags.filter((flag) => flag.startsWith('疑似')).join('；') }}</span></div>
          <div class="editor-section">
            <h3><BookOpenCheck :size="17" />{{ selected.knowledge_type === 'textbook' ? '教材摘要' : '病例摘要' }}</h3>
            <dl>
              <dt>主诉</dt><dd>{{ selected.chief_complaint || '未提取' }}</dd>
              <dt>现病史</dt><dd>{{ selected.present_illness || '未提取' }}</dd>
              <dt>来源</dt><dd>{{ selected.source }}</dd>
              <dt>更新时间</dt><dd>{{ formatTime(selected.updated_at) }}</dd>
            </dl>
          </div>
          <div class="editor-section">
            <h3>脱敏全文</h3>
            <div class="case-library-content">{{ selected.content || '暂无全文内容' }}</div>
          </div>
        </template>
      </section>

      <section v-else class="case-editor teacher-case-editor case-library-detail case-library-empty-detail">
        <Library :size="26" /><p>选择一个条目查看脱敏后的病例内容</p>
      </section>
    </div>

    <div v-if="showCreate" class="case-library-modal" role="dialog" aria-modal="true" :aria-label="knowledgeTypeFilter === 'textbook' ? '新增教材知识' : '新增病例知识'">
      <div class="case-library-modal-card">
        <header>
          <div><span><ShieldCheck :size="19" /></span><div><strong>{{ knowledgeTypeFilter === 'textbook' ? '新增教材知识条目' : '新增去标识化病例' }}</strong><small>{{ knowledgeTypeFilter === 'textbook' ? '补充内容将进入教材知识库，保存后需要重建 embedding' : '保存时后端会自动脱敏全部文本字段' }}</small></div></div>
          <button class="icon-button" type="button" title="关闭" @click="showCreate = false"><X :size="18" /></button>
        </header>
        <form @submit.prevent="saveCreate">
          <div>
            <label>{{ knowledgeTypeFilter === 'textbook' ? '条目标题' : '病例名称' }}<input v-model="createForm.title" :placeholder="knowledgeTypeFilter === 'textbook' ? '例如：心脏四腔结构' : '例如：急性心肌梗死'" /></label>
            <label>{{ knowledgeTypeFilter === 'textbook' ? '教材分类' : '疾病分类' }}<input v-model="createForm.category" list="category-options" :placeholder="knowledgeTypeFilter === 'textbook' ? '例如：循环系统' : '例如：心血管疾病'" /></label>
          </div>
          <div>
            <label>主要诊断<input v-model="createForm.diagnosis" /></label>
            <label>来源<input v-model="createForm.source" /></label>
          </div>
          <label>主诉<input v-model="createForm.chief_complaint" placeholder="例如：突发胸痛 3 小时" /></label>
          <label>现病史<textarea v-model="createForm.present_illness" rows="3" /></label>
          <label>{{ knowledgeTypeFilter === 'textbook' ? '教材正文' : '病例全文' }}<textarea v-model="createForm.content" rows="8" :placeholder="knowledgeTypeFilter === 'textbook' ? '粘贴教材摘要或教师补充内容' : '可粘贴原始病历，保存前先脱敏预览'" /></label>
          <div class="case-library-preview-actions">
            <button class="button-secondary" type="button" :disabled="previewing" @click="runPreview"><LoaderCircle v-if="previewing" class="spin" :size="16" /><Eye v-else :size="16" />脱敏预览</button>
          </div>
          <div v-if="preview" class="case-library-preview">
            <div><strong>检测到敏感字段</strong><span v-for="kind in preview.pii_types" :key="kind" class="pii-kind">{{ kind }} {{ preview.counts[kind] }}</span><span v-if="!preview.pii_types.length" class="pii-kind none">未检测到</span></div>
            <p v-if="preview.risk_flags.length" class="risk-text">{{ preview.risk_flags.join('；') }}</p>
            <textarea :value="preview.masked_text" rows="6" readonly />
          </div>
          <footer><button class="button-secondary" type="button" @click="showCreate = false"><X :size="16" />取消</button><button class="button-primary" type="submit" :disabled="saving"><LoaderCircle v-if="saving" class="spin" :size="16" /><Save v-else :size="16" />保存并入库</button></footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.case-library-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0 0 14px; }
.case-library-compile { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.compile-publish-toggle { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted, #64748b); font-size: 13px; cursor: pointer; }
.compile-publish-toggle input { width: 15px; height: 15px; accent-color: #2f7d6c; }
.button-primary.ai-compile { background: #2f7d6c; }
.button-primary.ai-compile:disabled { opacity: .45; cursor: not-allowed; }
.entry-checkbox { flex: 0 0 auto; width: 15px; height: 15px; accent-color: #2f7d6c; cursor: pointer; }
.case-management-scroll > button.entry-selected { border-color: rgba(47, 125, 108, .3); background: #edf7f4; }
.case-library-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.case-library-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 0 0 16px; }
.case-library-stats article { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #fff; color: var(--text-muted, #64748b); }
.case-library-stats article strong { display: block; font-size: 22px; line-height: 1.15; color: var(--text-primary, #16313a); }
.case-library-stats article small { font-size: 12px; }
.case-library-stats article.warning { color: #b45309; border-color: #fde6c8; background: #fffbeb; }
.case-library-stats article.warning strong { color: #92400e; }
.case-library-category { display: flex; align-items: center; gap: 8px; margin: 10px 0; color: var(--text-muted, #64748b); font-size: 13px; }
.case-library-category select { flex: 1; min-width: 0; height: 34px; padding: 0 8px; border: 1px solid var(--line, #e1e9ea); border-radius: 6px; background: #fff; color: var(--text-primary, #16313a); }
.knowledge-type-tabs { display: flex; gap: 4px; margin: 10px 0 2px; padding: 3px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #f6fafb; }
.knowledge-type-tabs button { flex: 1; padding: 6px 8px; border: 0; border-radius: 5px; background: transparent; color: var(--text-muted, #64748b); font-size: 13px; cursor: pointer; }
.knowledge-type-tabs button.active { background: #fff; color: #176b5d; box-shadow: 0 1px 3px rgba(20, 50, 58, .1); font-weight: 600; }
.case-library-list button b { font-size: 11px; padding: 2px 7px; border-radius: 999px; background: #e8f7f2; color: #0f766e; white-space: nowrap; }
.case-library-list button b.risk { background: #fffbeb; color: #b45309; }
.case-library-empty { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 120px; color: var(--text-muted, #64748b); font-size: 13px; }
.case-library-detail header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.case-library-detail header > div:last-child { display: flex; gap: 8px; flex-wrap: wrap; }
.case-library-badges { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
.case-library-badges span { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; font-size: 12px; }
.privacy-ok { background: #e8f7f2; color: #0f766e; }
.pii-kind { background: #eef4f6; color: #48606b; }
.pii-kind.none { color: #94a3b8; }
.imported-kind { background: #eef2ff; color: #4338ca; }
.embedding-badge { background: #fff7ed; color: #b45309; }
.embedding-badge.ready { background: #ecfdf5; color: #047857; }
.case-library-risk { display: flex; gap: 8px; align-items: flex-start; margin: 0 0 14px; padding: 10px 12px; border: 1px solid #fde6c8; border-radius: 8px; background: #fffbeb; color: #92400e; font-size: 13px; }
.case-library-content { max-height: 420px; overflow: auto; padding: 14px 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #f8fafb; color: #33454f; font-size: 14px; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }
.case-library-empty-detail { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: var(--text-muted, #64748b); font-size: 14px; }
.case-library-modal { position: fixed; inset: 0; z-index: 80; display: flex; align-items: center; justify-content: center; padding: 20px; background: rgba(12, 30, 36, 0.48); }
.case-library-modal-card { width: min(720px, 100%); max-height: calc(100vh - 40px); overflow: auto; border-radius: 10px; background: #fff; box-shadow: 0 18px 50px rgba(12, 30, 36, 0.28); }
.case-library-modal-card header { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; padding: 16px 18px; border-bottom: 1px solid var(--line, #e1e9ea); }
.case-library-modal-card header > div:first-child { display: flex; gap: 10px; }
.case-library-modal-card header strong { display: block; color: var(--text-primary, #16313a); }
.case-library-modal-card header small { color: var(--text-muted, #64748b); font-size: 12px; }
.case-library-modal-card form { display: flex; flex-direction: column; gap: 12px; padding: 18px; }
.case-library-modal-card form > div { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.case-library-modal-card label { display: flex; flex-direction: column; gap: 5px; color: var(--text-muted, #64748b); font-size: 13px; }
.case-library-modal-card input, .case-library-modal-card textarea { width: 100%; padding: 9px 11px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fff; color: var(--text-primary, #16313a); font-size: 14px; }
.case-library-modal-card textarea { resize: vertical; }
.case-library-preview-actions { display: flex; justify-content: flex-start; }
.case-library-preview { display: flex; flex-direction: column; gap: 8px; padding: 12px; border: 1px solid #d8e6e5; border-radius: 8px; background: #f4faf9; }
.case-library-preview > div { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; font-size: 13px; }
.case-library-preview .risk-text { margin: 0; color: #b45309; font-size: 12px; }
.case-library-preview textarea { background: #fff; }
.case-library-edit-form footer, .case-library-modal-card form footer { display: flex; justify-content: flex-end; gap: 8px; }
.button-secondary.danger { border-color: #fecaca; color: #b91c1c; background: #fff; }
.button-secondary.danger:hover { background: #fef2f2; }

/* Keep the teaching knowledge list independently scrollable on desktop. */
.case-library-list {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: calc(100vh - 110px);
  max-height: calc(100vh - 110px);
}
.case-library-list .case-management-scroll {
  flex: 1 1 auto;
  min-height: 0;
  max-height: none;
  overflow-y: scroll;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: #9fb8b6 #edf4f3;
}
.case-library-list .case-management-scroll::-webkit-scrollbar { width: 9px; }
.case-library-list .case-management-scroll::-webkit-scrollbar-thumb {
  border-radius: 8px;
  background: #9fb8b6;
}
.case-library-list .case-management-scroll::-webkit-scrollbar-track {
  border-radius: 8px;
  background: #edf4f3;
}
@media (max-width: 900px) {
  .case-library-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .case-library-modal-card form > div { grid-template-columns: 1fr; }
  .case-library-list { position: static; height: auto; max-height: none; }
  .case-library-list .case-management-scroll { max-height: 420px; }
}
@media (max-width: 560px) {
  .case-library-stats { grid-template-columns: 1fr 1fr; }
  .case-library-modal-card form { padding: 14px; }
}
</style>
