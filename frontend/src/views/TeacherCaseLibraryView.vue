<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import {
  AlertTriangle,
  BookOpenCheck,
  CheckCircle2,
  ChevronRight,
  Database,
  Eye,
  FilePenLine,
  FolderTree,
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
  getDocumentProcessingStatus,
  startEmbeddingProcessing,
  getEmbeddingProcessingStatus,
  startDocumentProcessing,
  uploadTeachingKnowledge,
  updateTeachingKnowledge
} from '../api';
import MarkdownContent from '../components/MarkdownContent.vue';
import type { CaseLibraryDeidentifyResult, CaseLibraryEntry } from '../types';
import { trainingStore } from '../stores/training';

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
const knowledgeTypeFilter = ref<'all' | 'textbook' | 'evidence'>('all');
const filterKind = ref<'all' | 'anonymized' | 'risk'>('all');
const processingFilter = ref('');
const selectedId = ref('');
const editing = ref(false);
const saving = ref(false);
const showCreate = ref(false);
const previewing = ref(false);
const importing = ref(false);
const uploading = ref(false);
const processing = ref(false);
const processingCounts = ref<Record<string, number>>({});
const embeddingProcessing = ref(false);
const embeddingCounts = ref<Record<string, number>>({});
let processingTimer: ReturnType<typeof window.setInterval> | undefined;
let embeddingTimer: ReturnType<typeof window.setInterval> | undefined;
const uploadType = ref<'textbook' | 'evidence'>('textbook');
const selectedIds = ref<string[]>([]);
const createForm = ref<EntryForm>(emptyForm());
const editForm = ref<EntryForm>(emptyForm());
const preview = ref<CaseLibraryDeidentifyResult | null>(null);
const isAdmin = computed(() => trainingStore.state.profile.role === 'admin');

const selected = computed(() => entries.value.find((item) => item.id === selectedId.value) || null);

function documentTypeLabel(item: CaseLibraryEntry) {
  return item.document_type === 'evidence' ? '医学依据' : '教材';
}

function hasRisk(item: CaseLibraryEntry) {
  return (item.risk_flags || []).some((flag) => flag.startsWith('疑似'));
}

const filteredEntries = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  return entries.value.filter((item) => {
    if (categoryFilter.value && item.category !== categoryFilter.value) return false;
    if (filterKind.value === 'anonymized' && !item.anonymized) return false;
    if (filterKind.value === 'risk' && !hasRisk(item)) return false;
    if (processingFilter.value && (item.processing_status || '') !== processingFilter.value) return false;
    if (!keyword) return true;
    return [item.title, item.category, item.diagnosis, item.chief_complaint, item.present_illness].join(' ').toLowerCase().includes(keyword);
  });
});

const riskCount = computed(() => entries.value.filter(hasRisk).length);
const anonymizedCount = computed(() => entries.value.filter((item) => item.anonymized).length);
const ocrPendingCount = computed(() => entries.value.filter((item) => item.processing_status === 'OCR 待处理' || item.ocr_status === 'pending').length);
const embeddingPendingCount = computed(() => entries.value.filter((item) => item.embedding_status && item.embedding_status !== '已生成').length);
const documentCount = computed(() => entries.value.filter((item) => item.document_scope === 'whole_document').length);
const selectedOutline = computed(() => selected.value?.outline || []);
const selectedIsWholeDocument = computed(() => selected.value?.document_scope === 'whole_document');

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { hour12: false });
}

async function load() {
  loading.value = true;
  try {
    const scope = isAdmin.value ? 'admin' : 'teacher';
    const data = await getTeachingKnowledge({ document_type: knowledgeTypeFilter.value === 'all' ? '' : knowledgeTypeFilter.value }, scope);
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
    await updateTeachingKnowledge(selected.value.id, { ...editForm.value }, isAdmin.value ? 'admin' : 'teacher');
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
    await deleteTeachingKnowledge(selected.value.id, isAdmin.value ? 'admin' : 'teacher');
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
    await createTeachingKnowledge({ ...createForm.value, knowledge_type: knowledgeTypeFilter.value === 'evidence' ? 'evidence' : 'textbook' }, isAdmin.value ? 'admin' : 'teacher');
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

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file || !isAdmin.value) return;
  uploading.value = true;
  try {
    const result = await uploadTeachingKnowledge(file, uploadType.value);
    notice.value = `已接收“${result.filename}”，等待 OCR 处理。`;
    await load();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '资料上传失败，请重试。';
  } finally { uploading.value = false; }
}

async function refreshProcessingStatus() {
  if (!isAdmin.value) return;
  try {
    const status = await getDocumentProcessingStatus();
    processing.value = status.running;
    processingCounts.value = status.counts || {};
    if (!status.running && processingTimer) {
      window.clearInterval(processingTimer);
      processingTimer = undefined;
      await load();
    }
  } catch { /* 页面列表仍可正常使用，状态下次刷新重试 */ }
}

async function runProcessing() {
  if (processing.value) return;
  try {
    const result = await startDocumentProcessing();
    processing.value = result.status === 'started' || result.status === 'running';
    notice.value = result.status === 'running' ? '批量 OCR 正在处理中。' : '已启动批量 OCR，页面会自动刷新处理进度。';
    await refreshProcessingStatus();
    if (processing.value && !processingTimer) processingTimer = window.setInterval(refreshProcessingStatus, 2500);
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '批量 OCR 启动失败。';
  }
}

async function refreshEmbeddingStatus() {
  if (!isAdmin.value) return;
  try {
    const status = await getEmbeddingProcessingStatus();
    embeddingProcessing.value = status.running;
    embeddingCounts.value = status.counts || {};
    if (!status.running) {
      if (embeddingTimer) { window.clearInterval(embeddingTimer); embeddingTimer = undefined; }
      await load();
    }
  } catch { /* 后端不可用时不影响知识库浏览 */ }
}

async function runEmbeddingProcessing() {
  if (embeddingProcessing.value) return;
  try {
    const result = await startEmbeddingProcessing();
    embeddingProcessing.value = result.status === 'started' || result.status === 'running';
    notice.value = embeddingProcessing.value ? '已启动 Qwen 全量向量索引，处理完成后会更新状态。' : '向量索引任务已结束。';
    await refreshEmbeddingStatus();
    if (embeddingProcessing.value && !embeddingTimer) embeddingTimer = window.setInterval(refreshEmbeddingStatus, 3500);
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '向量索引启动失败。';
  }
}

onMounted(async () => { await load(); await refreshProcessingStatus(); await refreshEmbeddingStatus(); if (processing.value) processingTimer = window.setInterval(refreshProcessingStatus, 2500); if (embeddingProcessing.value) embeddingTimer = window.setInterval(refreshEmbeddingStatus, 3500); });
onUnmounted(() => { if (processingTimer) window.clearInterval(processingTimer); if (embeddingTimer) window.clearInterval(embeddingTimer); });
</script>

<template>
  <div class="case-library-panel">
    <header v-if="isAdmin" class="admin-library-heading">
      <div><span class="section-kicker">管理员资料中心</span><h1>教学知识库管理</h1><p>统一维护病例、教材和权威临床资料，导入前完成脱敏与来源审核。</p></div>
    </header>
    <div class="case-library-toolbar" data-tour="knowledge-library-toolbar">
      <div class="case-library-actions">
        <button class="button-secondary" type="button" :disabled="importing" @click="runImport">
          <LoaderCircle v-if="importing" class="spin" :size="17" /><Database v-else :size="17" />{{ importing ? '正在导入素材' : (isAdmin ? '导入教学资料' : '导入本地素材') }}
        </button>
        <div v-if="isAdmin" class="upload-group"><select v-model="uploadType" aria-label="资料类型"><option value="textbook">教材</option><option value="evidence">医学依据</option><option value="case">病例</option></select><label class="button-secondary upload-button"><input type="file" accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg" hidden @change="uploadFile" /><LoaderCircle v-if="uploading" class="spin" :size="17" /><Database v-else :size="17" />{{ uploading ? '正在上传' : '上传整本文档' }}</label></div>
        <button v-if="isAdmin" class="button-secondary" type="button" :disabled="processing" @click="runProcessing"><LoaderCircle v-if="processing" class="spin" :size="17" /><Sparkles v-else :size="17" />{{ processing ? 'OCR 处理中' : '启动批量 OCR' }}</button>
        <button v-if="isAdmin" class="button-secondary" type="button" :disabled="embeddingProcessing" @click="runEmbeddingProcessing"><LoaderCircle v-if="embeddingProcessing" class="spin" :size="17" /><Sparkles v-else :size="17" />{{ embeddingProcessing ? '向量生成中' : '生成 Qwen 向量' }}</button>
        <button class="button-primary" type="button" @click="openCreate"><Plus :size="17" />新增知识条目</button>
      </div>
    </div>

    <div v-if="isAdmin && processing" class="processing-progress"><LoaderCircle class="spin" :size="16" />正在处理文档，完成后会自动更新列表<span v-if="processingCounts['待脱敏']">已完成 {{ processingCounts['待脱敏'] }} 份</span></div>

    <div v-if="notice" class="teacher-case-notice"><CheckCircle2 :size="17" />{{ notice }}<button type="button" title="关闭" @click="notice = ''"><X :size="15" /></button></div>

    <section class="case-library-stats">
      <article><Library :size="18" /><span><strong>{{ entries.length }}</strong><small>教学知识条目</small></span></article>
      <article><ShieldCheck :size="18" /><span><strong>{{ anonymizedCount }}</strong><small>已完成脱敏</small></span></article>
      <article><Database :size="18" /><span><strong>{{ documentCount }}</strong><small>整本文档</small></span></article>
      <article :class="{ warning: riskCount > 0 }"><AlertTriangle :size="18" /><span><strong>{{ riskCount }}</strong><small>疑似残留风险</small></span></article>
      <article :class="{ warning: ocrPendingCount > 0 }"><Eye :size="18" /><span><strong>{{ ocrPendingCount }}</strong><small>待 OCR 文档</small></span></article>
      <article :class="{ warning: embeddingPendingCount > 0 }"><Sparkles :size="18" /><span><strong>{{ embeddingPendingCount }}</strong><small>待生成向量</small></span></article>
    </section>

    <div class="teacher-case-layout case-library-layout">
      <section class="case-management-list case-library-list">
        <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="搜索病例、教材或知识内容" /></label>
        <div class="knowledge-type-tabs">
          <button type="button" :class="{ active: knowledgeTypeFilter === 'all' }" @click="knowledgeTypeFilter = 'all'; load()">全部</button>
          <button type="button" :class="{ active: knowledgeTypeFilter === 'textbook' }" @click="knowledgeTypeFilter = 'textbook'; load()">教材</button>
          <button type="button" :class="{ active: knowledgeTypeFilter === 'evidence' }" @click="knowledgeTypeFilter = 'evidence'; load()">医学依据</button>
        </div>
        <label class="case-library-category">
          <span>分类</span>
          <select v-model="categoryFilter">
            <option value="">全部分类</option>
            <option v-for="(count, name) in categories" :key="name" :value="name">{{ name }}（{{ count }}）</option>
          </select>
        </label>
        <label class="case-library-category"><span>处理状态</span><select v-model="processingFilter"><option value="">全部状态</option><option value="OCR 待处理">OCR 待处理</option><option value="待脱敏">待脱敏</option><option value="OCR失败">OCR 失败</option><option value="已发布">已发布</option></select></label>
        <div class="case-list-tabs">
          <button type="button" :class="{ active: filterKind === 'all' }" @click="filterKind = 'all'">全部</button>
          <button type="button" :class="{ active: filterKind === 'anonymized' }" @click="filterKind = 'anonymized'">已脱敏</button>
          <button type="button" :class="{ active: filterKind === 'risk' }" @click="filterKind = 'risk'">需复核</button>
        </div>
        <div class="case-management-scroll">
          <div v-if="loading" class="case-library-empty"><LoaderCircle class="spin" :size="22" />正在加载知识库</div>
          <button v-for="item in filteredEntries" v-else :key="item.id" type="button" :class="{ active: selectedId === item.id, 'entry-selected': selectedIds.includes(item.id) }" @click="selectEntry(item.id)">
            <input class="entry-checkbox" type="checkbox" :disabled="item.knowledge_type === 'textbook'" :checked="selectedIds.includes(item.id)" :aria-label="`选择${item.title}`" @click.stop="toggleSelect(item.id)" />
            <span><strong>{{ item.title }}</strong><small>{{ documentTypeLabel(item) }} · {{ item.document_scope === 'whole_document' ? '整本文档 · 目录分层' : (item.knowledge_type === 'textbook' ? (item.chapter || item.category) : (item.category + ' · ' + (item.diagnosis || '待确认诊断'))) }}</small></span>
            <b :class="{ risk: hasRisk(item) }">{{ hasRisk(item) ? '需复核' : (item.processing_status || item.status) }}</b>
          </button>
          <div v-if="!loading && !filteredEntries.length" class="case-library-empty"><Library :size="22" />暂无匹配条目</div>
        </div>
      </section>

      <section v-if="selected" class="case-editor teacher-case-editor case-library-detail">
        <header>
      <div><span class="section-kicker">{{ documentTypeLabel(selected) }} · {{ selected.document_scope === 'whole_document' ? '整本文档' : '知识条目' }}</span><h2>{{ selected.title }}</h2><p>{{ selected.category }} · {{ selected.diagnosis || selected.source }}</p></div>
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
            <span v-if="selected.processing_status" class="processing-badge">处理：{{ selected.processing_status }}</span>
          </div>
          <div v-if="hasRisk(selected)" class="case-library-risk"><AlertTriangle :size="16" /><span>{{ selected.risk_flags.filter((flag) => flag.startsWith('疑似')).join('；') }}</span></div>
          <div class="editor-section">
            <h3><BookOpenCheck :size="17" />{{ selectedIsWholeDocument ? '资料概览' : (selected.knowledge_type === 'textbook' ? '教材摘要' : '病例摘要') }}</h3>
            <dl>
              <dt>主诉</dt><dd>{{ selected.chief_complaint || '未提取' }}</dd>
              <dt>现病史</dt><dd>{{ selected.present_illness || '未提取' }}</dd>
              <dt>来源</dt><dd>{{ selected.source }}</dd>
              <dt>文档范围</dt><dd>{{ selected.document_scope === 'whole_document' ? '整本文档，按目录层级浏览（页码仅供检索定位）' : '单条知识内容' }}</dd>
              <dt v-if="selected.page_count">页数</dt><dd v-if="selected.page_count">{{ selected.page_count }} 页</dd>
              <dt v-if="selected.ocr_text_path">OCR 文本</dt><dd v-if="selected.ocr_text_path">{{ selected.ocr_text_path }}</dd>
              <dt v-if="selected.source_path">原始文件</dt><dd v-if="selected.source_path">{{ selected.source_path }}</dd>
              <dt>更新时间</dt><dd>{{ formatTime(selected.updated_at) }}</dd>
            </dl>
          </div>
          <div v-if="selectedIsWholeDocument" class="editor-section document-outline-section">
            <h3><FolderTree :size="17" />本书目录与章节定位</h3>
            <MarkdownContent class="document-summary" :content="selected.content_summary || '正在生成本书摘要与目录结构。'" />
            <ol v-if="selectedOutline.length" class="document-outline-list">
              <li v-for="section in selectedOutline" :key="`${section.start_page}-${section.title}`">
                <ChevronRight :size="15" /><span>{{ section.title }}</span><small>第 {{ section.start_page }}{{ section.end_page !== section.start_page ? `-${section.end_page}` : '' }} 页</small>
              </li>
            </ol>
            <p v-else class="outline-empty">目录正在整理中；资料仍将作为整本来源参与检索。</p>
          </div>
          <div v-else class="editor-section">
            <h3>脱敏全文</h3>
            <MarkdownContent v-if="selected.content" class="case-library-content" :content="selected.content" />
            <div v-else class="case-library-content">暂无全文内容</div>
          </div>
        </template>
      </section>

      <section v-else class="case-editor teacher-case-editor case-library-detail case-library-empty-detail">
        <Library :size="26" /><p>选择一个条目查看脱敏后的病例内容</p>
      </section>
    </div>

    <div v-if="showCreate" class="case-library-modal" role="dialog" aria-modal="true" :aria-label="knowledgeTypeFilter === 'evidence' ? '新增医学依据' : '新增教材知识'">
      <div class="case-library-modal-card">
        <header>
          <div><span><ShieldCheck :size="19" /></span><div><strong>{{ knowledgeTypeFilter === 'evidence' ? '新增医学依据' : '新增教材知识条目' }}</strong><small>补充内容会作为讲解与命题的依据，保存后需要重建 embedding</small></div></div>
          <button class="icon-button" type="button" title="关闭" @click="showCreate = false"><X :size="18" /></button>
        </header>
        <form @submit.prevent="saveCreate">
          <div>
            <label>条目标题<input v-model="createForm.title" placeholder="例如：心脏四腔结构" /></label>
            <label>分类<input v-model="createForm.category" list="category-options" placeholder="例如：循环系统" /></label>
          </div>
          <div>
            <label>来源<input v-model="createForm.source" placeholder="例如：《系统解剖学》第10版" /></label>
          </div>
          <label>正文<textarea v-model="createForm.content" rows="8" placeholder="粘贴教材摘要或教师补充内容" /></label>
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
.case-library-panel { font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", sans-serif; color: #18363d; }
.case-library-panel button, .case-library-panel input, .case-library-panel textarea, .case-library-panel select { font-size: 15px; }
.case-library-panel .case-management-scroll small, .case-library-panel .case-library-category, .case-library-panel .compile-publish-toggle { font-size: 14px; }
.upload-button { cursor: pointer; }
.upload-group { display: inline-flex; align-items: center; gap: 8px; }
.upload-group select { height: 40px; padding: 0 10px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fff; color: #24515a; }
.admin-library-heading { margin: 0 0 18px; }
.admin-library-heading h1 { margin: 0 0 6px; font-size: clamp(1.7rem, 2.8vw, 2.35rem); }
.admin-library-heading p { margin: 0; max-width: 68ch; }
.case-library-compile { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.compile-publish-toggle { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted, #64748b); font-size: 13px; cursor: pointer; }
.compile-publish-toggle input { width: 15px; height: 15px; accent-color: #2f7d6c; }
.button-primary.ai-compile { background: #2f7d6c; }
.button-primary.ai-compile:disabled { opacity: .45; cursor: not-allowed; }
.entry-checkbox { flex: 0 0 auto; width: 15px; height: 15px; accent-color: #2f7d6c; cursor: pointer; }
.case-management-scroll > button.entry-selected { border-color: rgba(47, 125, 108, .3); background: #edf7f4; }
.case-library-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.case-library-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 0 0 16px; }
.case-library-stats article { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #fff; color: var(--text-muted, #64748b); }
.case-library-stats article strong { display: block; font-size: 22px; line-height: 1.15; color: var(--text-primary, #16313a); }
.case-library-stats article small { font-size: 12px; }
.case-library-stats article.warning { color: #b45309; border-color: #fde6c8; background: #fffbeb; }
.case-library-stats article.warning strong { color: #92400e; }
.case-library-detail dd { overflow-wrap: anywhere; }
.case-library-category { display: flex; align-items: center; gap: 8px; margin: 10px 0; color: var(--text-muted, #64748b); font-size: 13px; }
.case-library-category select { flex: 1; min-width: 0; height: 34px; padding: 0 8px; border: 1px solid var(--line, #e1e9ea); border-radius: 6px; background: #fff; color: var(--text-primary, #16313a); }
.knowledge-type-tabs { display: flex; gap: 4px; margin: 10px 0 2px; padding: 3px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #f6fafb; }
.knowledge-type-tabs button { flex: 1; padding: 6px 8px; border: 0; border-radius: 5px; background: transparent; color: var(--text-muted, #64748b); font-size: 13px; cursor: pointer; }
.knowledge-type-tabs button.active { background: #fff; color: #176b5d; box-shadow: 0 1px 3px rgba(20, 50, 58, .1); font-weight: 600; }
.processing-badge { display: inline-flex; align-items: center; padding: 3px 8px; border-radius: 999px; background: #eef5ff; color: #315b92; font-size: 12px; }
.processing-progress { display: flex; align-items: center; gap: 8px; margin: 0 0 14px; padding: 10px 14px; border: 1px solid #cfe2f4; border-radius: 8px; background: #f4f9ff; color: #315b92; font-size: 13px; }
.processing-progress span { margin-left: auto; color: #52718e; }
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
.case-library-content { max-height: 420px; overflow: auto; padding: 14px 16px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #f8fafb; color: #33454f; font-size: 15px; line-height: 1.8; word-break: break-word; }
.case-library-content :deep(h1),
.case-library-content :deep(h2),
.case-library-content :deep(h3),
.case-library-content :deep(h4) { margin: 14px 0 7px; font-size: 17px; }
.case-library-content :deep(p) { margin: 7px 0; font-size: inherit; }
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
