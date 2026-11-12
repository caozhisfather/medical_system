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
import { ArrowRight, ChevronLeft, MonitorPlay, Image as ImageIcon, BriefcaseMedical, ListChecks, Layers, Star, SlidersHorizontal } from '@lucide/vue';
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
import knowledgeBanner from '../assets/medical/teaching-library-banner.webp';

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
const createType = ref<'case' | 'textbook'>('textbook');
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
const searchInput = ref<HTMLInputElement | null>(null);
const resourceKind = ref('all');
const sourceFilter = ref('');
const recentDays = ref('');
const resourcePage = ref(1);
const detailOpen = ref(false);
const recommendationPage = ref(0);
const resourceKinds = [
  { id: 'case', label: '病例库（核心）', short: '病例', icon: BriefcaseMedical },
  { id: 'textbook', label: '教材与参考', short: '教材', icon: BookOpenCheck },
  { id: 'slides', label: '课件与讲义', short: '课件', icon: MonitorPlay },
  { id: 'video', label: '视频与动画', short: '视频', icon: MonitorPlay },
  { id: 'question', label: '题库与测评', short: '题库', icon: ListChecks },
  { id: 'image', label: '图表与图片', short: '图表', icon: ImageIcon },
  { id: 'other', label: '其他资源', short: '其他', icon: Layers }
];
function entryKind(item: CaseLibraryEntry) {
  const path = item.source_path || item.title;
  if (/\.(pptx?|odp)$/i.test(path)) return 'slides';
  if (/\.(mp4|mov|webm|avi)$/i.test(path)) return 'video';
  if (/\.(png|jpe?g|webp|gif|svg)$/i.test(path)) return 'image';
  if (item.document_type === 'case' || item.knowledge_type === 'case') return 'case';
  if (item.document_type === 'textbook' || (!item.document_type && item.knowledge_type === 'textbook')) return 'textbook';
  return 'other';
}
function kindCount(kind: string) { return entries.value.filter(item => entryKind(item) === kind).length; }
function setKind(kind: string) { resourceKind.value = kind; resourcePage.value = 1; }
const sources = computed(() => [...new Set(entries.value.map(e => e.source).filter(Boolean))]);
const recommended = computed(() => entries.value.filter(e => entryKind(e) === 'case' && !hasRisk(e)).sort((a,b) => b.updated_at.localeCompare(a.updated_at)).slice(0,9));
const recommendedVisible = computed(() => recommended.value.slice(recommendationPage.value*3,recommendationPage.value*3+3));
const displayedEntries = computed(() => filteredEntries.value.slice((resourcePage.value-1)*12, resourcePage.value*12));
const resourceStats = computed(() => [
  {id:'case',label:'病例资源',icon:BriefcaseMedical,count:kindCount('case')},
  {id:'textbook',label:'教材资源',icon:BookOpenCheck,count:kindCount('textbook')},
  {id:'video',label:'多媒体资源',icon:MonitorPlay,count:kindCount('video')+kindCount('image')+kindCount('slides')},
  {id:'question',label:'题库资源',icon:ListChecks,count:kindCount('question')},
  {id:'other',label:'其他资源',icon:Layers,count:kindCount('other')}
]);

const selected = computed(() => entries.value.find((item) => item.id === selectedId.value) || null);

function documentTypeLabel(item: CaseLibraryEntry) {
  return item.document_type === 'evidence' ? '医学依据' : resourceKinds.find(k => k.id === entryKind(item))?.short || '其他';
}

function hasRisk(item: CaseLibraryEntry) {
  return (item.risk_flags || []).some((flag) => flag.startsWith('疑似'));
}

const filteredEntries = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  return entries.value.filter((item) => {
    const kind = entryKind(item);
    if (resourceKind.value === 'media' ? !['slides','video','image'].includes(kind) : resourceKind.value !== 'all' && kind !== resourceKind.value) return false;
    if (sourceFilter.value && item.source !== sourceFilter.value) return false;
    if (recentDays.value && Date.now() - new Date(item.created_at).getTime() > Number(recentDays.value)*86400000) return false;
    if (knowledgeTypeFilter.value !== 'all' && item.document_type !== knowledgeTypeFilter.value) return false;
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
    const data = await getTeachingKnowledge({}, scope);
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
  detailOpen.value = true;
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
  notice.value = '';
  createType.value = resourceKind.value === 'case' ? 'case' : 'textbook';
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
    await createTeachingKnowledge({ ...createForm.value, knowledge_type: createType.value }, isAdmin.value ? 'admin' : 'teacher');
    showCreate.value = false;
    notice.value = '知识条目已保存入库。';
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
  <div class="case-library-panel" :style="{'--library-hero':`url(${knowledgeBanner})`}">
    <section class="knowledge-hero">
      <div><span class="knowledge-eyebrow">MEDICAL TEACHING LIBRARY</span><h1>精品病例库</h1><p>精选教学病例与专业资料 · 串联临床思维、诊疗流程与教学解析</p><div class="knowledge-hero-tags"><span><CheckCircle2 :size="14"/>临床教学情境</span><span><CheckCircle2 :size="14"/>系统知识依据</span><span><CheckCircle2 :size="14"/>隐私脱敏审核</span><span><CheckCircle2 :size="14"/>教学资源管理</span></div></div>
    </section>
    <section class="knowledge-metrics"><button v-for="stat in resourceStats" :key="stat.id" type="button" :class="{active:resourceKind === stat.id}" @click="setKind(stat.id === 'video' ? 'media' : stat.id)"><i><component :is="stat.icon" :size="27"/></i><span><small>{{stat.label}}</small><strong>{{stat.count}}</strong></span></button></section>
    <div class="case-library-toolbar" data-tour="knowledge-library-toolbar">
      <div class="case-library-actions">
        <button class="button-secondary" type="button" :disabled="importing" @click="runImport">
          <LoaderCircle v-if="importing" class="spin" :size="17" /><Database v-else :size="17" />{{ importing ? '正在导入素材' : (isAdmin ? '导入教学资料' : '导入本地素材') }}
        </button>
        <div v-if="isAdmin" class="upload-group"><select v-model="uploadType" aria-label="资料类型"><option value="textbook">教材</option><option value="evidence">医学依据</option><option value="case">病例</option></select><label class="button-secondary upload-button"><input type="file" accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg" hidden @change="uploadFile" /><LoaderCircle v-if="uploading" class="spin" :size="17" /><Database v-else :size="17" />{{ uploading ? '正在上传' : '上传整本文档' }}</label></div>
        <button v-if="isAdmin" class="button-secondary" type="button" :disabled="processing" @click="runProcessing"><LoaderCircle v-if="processing" class="spin" :size="17" /><Sparkles v-else :size="17" />{{ processing ? 'OCR 处理中' : '启动批量 OCR' }}</button>
        <button v-if="isAdmin" class="button-secondary" type="button" :disabled="embeddingProcessing" @click="runEmbeddingProcessing"><LoaderCircle v-if="embeddingProcessing" class="spin" :size="17" /><Sparkles v-else :size="17" />{{ embeddingProcessing ? '向量生成中' : '生成 Qwen 向量' }}</button>
      </div>
      <button class="button-primary case-library-create" type="button" @click="openCreate"><Plus :size="17" />新增知识条目</button>
    </div>

    <div v-if="isAdmin && processing" class="processing-progress"><LoaderCircle class="spin" :size="16" />正在处理文档，完成后会自动更新列表<span v-if="processingCounts['待脱敏']">已完成 {{ processingCounts['待脱敏'] }} 份</span></div>

    <div v-if="notice" class="teacher-case-notice"><CheckCircle2 :size="17" />{{ notice }}<button type="button" title="关闭" @click="notice = ''"><X :size="15" /></button></div>

    <div class="knowledge-workspace">
      <aside class="knowledge-navigation">
        <h2><SlidersHorizontal :size="20"/>资源导航</h2>
        <button type="button" :class="{active:resourceKind==='all'}" @click="setKind('all')"><Library :size="22"/><strong>全部资源</strong><span>{{entries.length}}</span></button>
        <button v-for="kind in resourceKinds" :key="kind.id" type="button" :class="{active:resourceKind===kind.id}" @click="setKind(kind.id)"><component :is="kind.icon" :size="22"/><strong>{{kind.label}}</strong><span>{{kindCount(kind.id)}}</span><ChevronRight :size="14"/></button>
        <div class="knowledge-quality"><h3><ShieldCheck :size="16"/>资源质量</h3><span>已脱敏 <b>{{anonymizedCount}}</b></span><span>需复核 <b>{{riskCount}}</b></span><span>整本文档 <b>{{documentCount}}</b></span><span>待 OCR <b>{{ocrPendingCount}}</b></span><span>待生成向量 <b>{{embeddingPendingCount}}</b></span></div>
      </aside>
      <main class="knowledge-main">
        <section class="knowledge-recommendations">
          <header><h2><Star :size="21"/>教学病例精选</h2><button type="button" @click="setKind('case')">查看更多病例 <ArrowRight :size="15"/></button></header>
          <div v-if="recommendedVisible.length" class="knowledge-recommendation-grid"><button v-for="item in recommendedVisible" :key="item.id" type="button" @click="selectEntry(item.id)"><div class="knowledge-case-symbol"><BriefcaseMedical :size="32"/><small>{{item.category}}</small></div><div><span class="knowledge-tag">教学病例</span><h3>{{item.title}}</h3><small>{{item.diagnosis || item.category}}</small><p>{{item.chief_complaint || item.present_illness || '查看病例内容与教学依据'}}</p></div><ChevronRight :size="15"/></button></div>
          <div v-else class="knowledge-empty"><Library :size="26"/><p>{{loading?'正在加载教学资料…':'当前没有可推荐的已脱敏病例，可通过导入素材补充。'}}</p></div>
          <div v-if="recommended.length>3" class="knowledge-pager"><button aria-label="上一组病例" :disabled="recommendationPage===0" @click="recommendationPage--"><ChevronLeft :size="16"/></button><button v-for="n in Math.ceil(recommended.length/3)" :key="n" :class="{active:recommendationPage===n-1}" :aria-label="'第'+n+'组病例'" @click="recommendationPage=n-1"/><button aria-label="下一组病例" :disabled="(recommendationPage+1)*3>=recommended.length" @click="recommendationPage++"><ChevronRight :size="16"/></button></div>
        </section>
        <section class="knowledge-shortcuts"><button type="button" class="featured" @click="setKind('case')"><BriefcaseMedical :size="25"/><span><strong>病例库浏览</strong><small>按分类与关键词查找病例</small></span><ArrowRight :size="16"/></button><button type="button" @click="knowledgeTypeFilter='all';setKind('textbook')"><BookOpenCheck :size="25"/><span><strong>教材与参考</strong><small>浏览教材、章节与目录</small></span></button><button type="button" @click="setKind('all');query='';resourcePage=1;searchInput?.focus()"><Search :size="25"/><span><strong>资源检索</strong><small>标题、疾病与教学关键词</small></span></button><RouterLink :to="isAdmin?'/admin/dashboard':'/teacher/exam-settings'"><ListChecks :size="25"/><span><strong>教学应用</strong><small>{{isAdmin?'返回管理工作台':'配置命题与教学提示词'}}</small></span></RouterLink></section>
        <section class="knowledge-resource-panel">
          <header><h2>全部资源 <small>{{filteredEntries.length}}</small></h2><div class="knowledge-type-chips"><button type="button" :class="{active:resourceKind==='all'}" @click="setKind('all')">全部</button><button v-for="kind in resourceKinds" :key="kind.id" type="button" :class="{active:resourceKind===kind.id}" @click="setKind(kind.id)">{{kind.short}}</button></div><button type="button" class="button-primary" @click="openCreate"><Plus :size="16"/>新增知识条目</button></header>
          <div class="knowledge-resource-filters"><select v-model="categoryFilter" aria-label="知识分类筛选" @change="resourcePage=1"><option value="">全部知识分类</option><option v-for="(count,name) in categories" :key="name" :value="name">{{name}}（{{count}}）</option></select><select v-model="knowledgeTypeFilter" aria-label="资料类型筛选" @change="resourcePage=1"><option value="all">全部资料类型</option><option value="textbook">教材</option><option value="evidence">医学依据</option></select><label class="search-control"><Search :size="17"/><input ref="searchInput" v-model="query" placeholder="搜索病例、疾病、教材或关键词…" @input="resourcePage=1"/></label><select v-model="sourceFilter" aria-label="来源筛选" @change="resourcePage=1"><option value="">来源：全部</option><option v-for="source in sources" :key="source" :value="source">{{source}}</option></select><select v-model="recentDays" aria-label="上传时间筛选" @change="resourcePage=1"><option value="">上传时间：全部</option><option value="30">最近30天</option><option value="90">最近90天</option></select><select v-model="processingFilter" aria-label="处理状态筛选" @change="resourcePage=1"><option value="">全部处理状态</option><option value="OCR 待处理">OCR 待处理</option><option value="待脱敏">待脱敏</option><option value="OCR失败">OCR 失败</option><option value="已发布">已发布</option></select><select v-model="filterKind" aria-label="脱敏审核筛选" @change="resourcePage=1"><option value="all">全部审核状态</option><option value="anonymized">已脱敏</option><option value="risk">需复核</option></select></div>
          <div class="knowledge-table-wrap"><table><thead><tr><th>选择</th><th>资源名称</th><th>类型</th><th>所属分类</th><th>状态</th><th>来源</th><th>上传时间</th><th>操作</th></tr></thead><tbody><tr v-for="item in displayedEntries" :key="item.id" :class="{'entry-selected':selectedIds.includes(item.id)}"><td><input class="entry-checkbox" type="checkbox" :disabled="item.knowledge_type==='textbook'" :checked="selectedIds.includes(item.id)" :aria-label="'选择'+item.title" @change="toggleSelect(item.id)"/></td><td><button class="knowledge-title-link" type="button" @click="selectEntry(item.id)"><component :is="resourceKinds.find(k=>k.id===entryKind(item))?.icon || Library" :size="20"/><strong>{{item.title}}</strong></button></td><td><span class="knowledge-type-badge" :class="entryKind(item)">{{documentTypeLabel(item)}}</span></td><td>{{item.category || '未分类'}}</td><td><span :class="{'risk-text':hasRisk(item)}">{{hasRisk(item)?'需复核':item.processing_status || item.status}}</span></td><td>{{item.source || '未标注'}}</td><td class="knowledge-time">{{formatTime(item.created_at)}}</td><td><div class="knowledge-row-actions"><button type="button" aria-label="查看资源" @click="selectEntry(item.id)"><Eye :size="17"/></button><button type="button" aria-label="编辑资源" @click="selectEntry(item.id);beginEdit()"><FilePenLine :size="17"/></button></div></td></tr></tbody></table></div>
          <p v-if="loading" class="knowledge-empty"><LoaderCircle class="spin" :size="20"/>正在加载资源…</p><p v-else-if="!filteredEntries.length" class="knowledge-empty">没有匹配资源，请调整筛选或新增知识条目。</p>
          <footer><small>资源数量按当前知识库实际入库记录统计，尚未入库的类型显示 0。</small><div><button type="button" :disabled="resourcePage===1" @click="resourcePage--">上一页</button><span>{{resourcePage}} / {{Math.max(1,Math.ceil(filteredEntries.length/12))}}</span><button type="button" :disabled="resourcePage*12>=filteredEntries.length" @click="resourcePage++">下一页</button></div></footer>
        </section>
      </main>
    </div>
    <div v-if="detailOpen" class="knowledge-detail-overlay" @click.self="detailOpen=false"><div class="knowledge-detail-dialog" role="dialog" aria-modal="true" aria-label="教学资源详情"><div class="knowledge-detail-close"><button type="button" aria-label="关闭资源详情" @click="detailOpen=false"><X :size="21"/></button></div>
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

    </div>

    <div v-if="showCreate" class="case-library-modal" role="dialog" aria-modal="true" :aria-label="createType === 'case' ? '新增教学病例' : '新增教材知识'">
      <div class="case-library-modal-card">
        <header>
          <div><span><ShieldCheck :size="19" /></span><div><strong>{{ createType === 'case' ? '新增教学病例' : '新增教材知识条目' }}</strong><small>补充内容会作为讲解与命题的依据，保存后需要重建 embedding</small></div></div>
          <button class="icon-button" type="button" title="关闭" @click="showCreate = false"><X :size="18" /></button>
        </header>
        <form @submit.prevent="saveCreate"><p v-if="notice" role="alert" class="knowledge-form-notice">{{notice}}</p><label>条目类型<select v-model="createType"><option value="case">教学病例</option><option value="textbook">教材知识</option></select></label>
          <div>
            <label>条目标题<input v-model="createForm.title" placeholder="例如：心脏四腔结构" /></label>
            <label>分类<input v-model="createForm.category" list="category-options" placeholder="例如：循环系统" /></label>
          </div>
          <div>
            <label>来源<input v-model="createForm.source" placeholder="例如：《系统解剖学》第10版" /></label>
          </div>
          <div v-if="createType==='case'"><label>主要诊断<input v-model="createForm.diagnosis" maxlength="160"/></label><label>主诉<input v-model="createForm.chief_complaint" maxlength="300"/></label></div><label v-if="createType==='case'">现病史<textarea v-model="createForm.present_illness" rows="3" maxlength="2400"/></label><label>正文<textarea v-model="createForm.content" rows="8" placeholder="粘贴教材摘要或教师补充内容" /></label>
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
.knowledge-form-notice{padding:10px 12px;border-radius:10px;background:#fff3e9;color:#9a541a;font-size:13px;line-height:1.7}.case-library-modal-card select{padding:9px 11px;border:1px solid #dce7fa;border-radius:9px;background:#f8fbff;color:#102a56;font:inherit}
.case-library-panel{display:grid;gap:14px;color:#102a56!important;font-family:inherit!important;min-width:0}
.knowledge-hero{border-radius:20px;min-height:158px;padding:25px 34px;color:#fff;background:linear-gradient(90deg,#0863bf55,#1167b300),#176abe var(--library-hero) center/cover no-repeat;box-shadow:0 5px 15px #2861a312;display:flex;align-items:center;overflow:hidden}
.knowledge-hero>div{max-width:64%}.knowledge-eyebrow{font-size:10px;letter-spacing:2.5px;color:#ceeaff}.knowledge-hero h1{font-size:clamp(27px,3vw,42px);letter-spacing:3px;margin:5px 0 8px;color:#fff}.knowledge-hero p{font-size:14px;line-height:1.6;margin:0;color:#e9f6ff}.knowledge-hero-tags{display:flex;gap:9px;margin-top:16px;flex-wrap:wrap}.knowledge-hero-tags>span{display:flex;align-items:center;gap:5px;border-radius:20px;padding:5px 10px;background:#e4f4ffcf;color:#0b4c9b;font-size:11px}
.knowledge-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.knowledge-metrics>button{display:flex;align-items:center;gap:15px;background:linear-gradient(120deg,#fff,#edf4ff);border:1px solid #fff;padding:15px 20px;border-radius:18px;text-align:left;box-shadow:0 4px 12px #1d4d9810;cursor:pointer;color:#155eef}.knowledge-metrics>button.active{border-color:#7eacff;background:#e5f0ff}.knowledge-metrics i{width:50px;height:50px;display:grid;place-items:center;border-radius:50%;background:linear-gradient(135deg,#e3f1ff,#d1e2ff);flex-shrink:0}.knowledge-metrics small{color:#465f88;font-size:12px}.knowledge-metrics strong{display:block;font-size:29px;margin-top:3px;line-height:1.2}.knowledge-workspace{display:grid;grid-template-columns:230px minmax(0,1fr);gap:14px;align-items:start}.knowledge-navigation{border-radius:18px;background:linear-gradient(145deg,#fff,#f1f6ff);border:1px solid #fff;padding:15px 10px;box-shadow:0 4px 14px #214d8d0d}.knowledge-navigation h2{display:flex;align-items:center;gap:9px;font-size:18px;padding:4px 8px 14px;margin:0;color:#102a56}.knowledge-navigation h2 svg{color:#155eef}.knowledge-navigation>button{display:flex;align-items:center;gap:10px;width:100%;min-height:52px;padding:10px 8px;border-radius:11px;border:1px solid transparent;background:transparent;text-align:left;cursor:pointer;color:#264a83}.knowledge-navigation>button>strong{font-size:12px;flex:1}.knowledge-navigation>button>span{font-size:12px}.knowledge-navigation>button.active{background:linear-gradient(90deg,#e4f0ff,#f7faff);border-color:#96b7ff;color:#155eef}.knowledge-quality{border-top:1px solid #dfe8f9;padding:15px 10px 2px;margin-top:10px;font-size:12px;color:#64748b;display:grid;gap:11px}.knowledge-quality h3{display:flex;align-items:center;gap:7px;font-size:13px;margin:0;color:#30588f}.knowledge-quality span{display:flex;justify-content:space-between}.knowledge-main{min-width:0;display:grid;gap:14px}.knowledge-recommendations,.knowledge-resource-panel{background:linear-gradient(145deg,#ffffffed,#f6faff);border-radius:18px;border:1px solid white;padding:18px;box-shadow:0 5px 18px #1b4c9a0b}.knowledge-recommendations>header,.knowledge-resource-panel>header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px}.knowledge-recommendations h2,.knowledge-resource-panel h2{display:flex;align-items:center;gap:8px;margin:0;font-size:18px}.knowledge-recommendations h2 svg{color:#155eef;fill:#155eef}.knowledge-recommendations>header>button,.knowledge-resource-panel footer button,.knowledge-pager button,.knowledge-detail-close button{background:none;border:0;display:inline-flex;align-items:center;gap:8px;color:#155eef;cursor:pointer;font-size:12px}.knowledge-recommendation-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.knowledge-recommendation-grid>button{min-width:0;display:flex;text-align:left;gap:12px;align-items:center;padding:13px;border:1px solid #dce7fc;border-radius:14px;background:#f9fbff;cursor:pointer;box-shadow:0 4px 10px #155eef08;color:#102a56}.knowledge-recommendation-grid>button>div:nth-child(2){flex:1;min-width:0}.knowledge-recommendation-grid h3{font-size:13px;margin:8px 0;line-height:1.5}.knowledge-recommendation-grid p{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:11px;line-height:1.7;margin:7px 0 0;color:#64748b}.knowledge-recommendation-grid small{font-size:10px;color:#536b91}.knowledge-case-symbol{flex:0 0 64px;min-height:102px;border-radius:10px;background:linear-gradient(140deg,#e6f2ff,#caddff);color:#2668de;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}.knowledge-case-symbol small{font-size:9px;text-align:center;max-width:60px}.knowledge-tag{font-size:9px;padding:3px 7px;border-radius:10px;background:#eaf0ff;color:#3161b1}.knowledge-pager{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:14px}.knowledge-pager>button:not(:first-child):not(:last-child){width:7px;height:7px;min-height:0;border-radius:10px;padding:0;background:#cbdcff}.knowledge-pager>button.active{width:20px!important;background:#155eef!important}.knowledge-shortcuts{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:10px}.knowledge-shortcuts>button,.knowledge-shortcuts>a{display:flex;align-items:center;gap:10px;min-width:0;padding:17px 13px;border-radius:15px;background:linear-gradient(130deg,#fff,#eff5ff);border:1px solid #fff;cursor:pointer;color:#155eef;text-align:left;text-decoration:none;box-shadow:0 4px 14px #155eef0d}.knowledge-shortcuts strong{display:block;font-size:13px;color:#102a56}.knowledge-shortcuts small{display:block;margin-top:6px;font-size:10px;color:#64748b;line-height:1.4}.knowledge-shortcuts .featured{background:linear-gradient(110deg,#307fff,#155eef);color:#fff}.knowledge-shortcuts .featured :is(strong,small){color:#fff}.knowledge-resource-panel>header>h2 small{font-size:12px;color:#64748b}.knowledge-type-chips{display:flex;gap:2px;flex-wrap:wrap}.knowledge-type-chips button{padding:6px 10px;border-radius:20px;font-size:11px!important;border:1px solid #dce7fa;background:#f6f9ff;color:#35527d;cursor:pointer}.knowledge-type-chips button.active{background:#155eef;border-color:#155eef;color:white}.knowledge-resource-filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:15px}.knowledge-resource-filters .search-control{flex:1 1 250px}.knowledge-resource-filters select{min-width:0;max-width:170px;height:35px;background:#fff;border:1px solid #dce7fa;padding:0 8px;border-radius:9px;color:#425b82;font-size:11px!important}.knowledge-resource-filters input{font-size:12px!important}.knowledge-table-wrap{overflow:auto;max-height:570px;min-width:0}.knowledge-table-wrap table{width:100%;border-collapse:collapse;font-size:12px;color:#425b82}.knowledge-table-wrap th{background:#eaf1ff;text-align:left;padding:11px 9px;white-space:nowrap;font-size:11px}.knowledge-table-wrap td{padding:11px 9px;border-bottom:1px solid #e5edfa;vertical-align:middle;font-size:11px}.knowledge-table-wrap .entry-selected{background:#e8f2ff}.knowledge-title-link{display:flex;gap:8px;align-items:center;text-align:left;cursor:pointer;border:0;background:none;color:#102a56;min-width:160px;max-width:320px;font-size:12px!important;line-height:1.6}.knowledge-title-link svg{color:#155eef;flex-shrink:0}.knowledge-type-badge{padding:3px 7px;background:#edf0ff;color:#5f51a5;border-radius:15px;white-space:nowrap;font-size:10px}.knowledge-type-badge.case{background:#fff0d9;color:#a56b27}.knowledge-type-badge.textbook{background:#e7f5ee;color:#377552}.knowledge-row-actions{display:flex;gap:8px}.knowledge-row-actions button{padding:2px;background:none;border:0;color:#155eef;cursor:pointer}.knowledge-time{white-space:nowrap}.knowledge-resource-panel footer{display:flex;justify-content:space-between;gap:15px;align-items:center;margin-top:15px}.knowledge-resource-panel footer>small{color:#64748b;font-size:10px;line-height:1.6}.knowledge-resource-panel footer>div{display:flex;align-items:center;gap:10px;font-size:11px;white-space:nowrap}.knowledge-empty{display:flex;align-items:center;justify-content:center;gap:10px;min-height:110px;text-align:center;color:#64748b;font-size:12px;line-height:1.8}.knowledge-detail-overlay{position:fixed;inset:0;z-index:70;background:#102a5677;padding:24px;display:grid;place-items:center}.knowledge-detail-dialog{width:min(900px,100%);max-height:90dvh;overflow:auto;background:#fff;border-radius:20px;padding:20px;color:#102a56}.knowledge-detail-close{display:flex;justify-content:flex-end}.knowledge-detail-dialog .case-library-detail{border:0;padding:12px;box-shadow:none}.knowledge-detail-dialog .case-library-detail h2{font-size:23px}.knowledge-detail-dialog .case-library-detail header{margin-top:4px}.knowledge-detail-dialog .case-library-detail header>div:first-child{display:block}.knowledge-detail-dialog .case-library-detail header>div:last-child{display:flex}.case-library-panel>.case-library-toolbar{margin:0}.case-library-panel .button-primary{background:#155eef;border-radius:10px;font-size:12px}.case-library-panel .button-secondary{border-radius:10px;color:#30588f;font-size:12px}.case-library-panel .teacher-case-notice{margin:0}.knowledge-resource-panel button:disabled,.knowledge-pager button:disabled{opacity:.4;cursor:not-allowed}
@media(max-width:1250px){.knowledge-workspace{grid-template-columns:195px minmax(0,1fr)}.knowledge-recommendation-grid{grid-template-columns:1fr}.knowledge-recommendation-grid>button{min-height:110px}.knowledge-case-symbol{min-height:86px}.knowledge-shortcuts{grid-template-columns:repeat(2,minmax(0,1fr))}.knowledge-metrics>button{padding:13px 12px;gap:10px}.knowledge-metrics i{height:36px;width:36px}.knowledge-metrics strong{font-size:24px}}
@media(max-width:760px){.knowledge-hero{padding:22px;min-height:190px;background-position:65% center;background-image:linear-gradient(90deg,#0863bfee,#0863bf99),var(--library-hero)}.knowledge-hero>div{max-width:100%}.knowledge-hero-tags{gap:5px}.knowledge-hero-tags>span{font-size:9px;padding:4px 7px}.knowledge-hero p{font-size:12px}.knowledge-eyebrow{font-size:8px;letter-spacing:2px}.knowledge-metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.knowledge-metrics>button:last-child{grid-column:1/-1}.knowledge-workspace{grid-template-columns:1fr}.knowledge-navigation{display:flex;flex-wrap:wrap;gap:5px}.knowledge-navigation h2{width:100%;padding:4px 5px}.knowledge-navigation>button{width:auto;flex:1 1 135px;min-height:40px;padding:8px}.knowledge-navigation>button strong{font-size:11px}.knowledge-navigation>button>svg{width:17px}.knowledge-quality{width:100%;grid-template-columns:repeat(3,1fr);gap:10px;padding:10px 5px}.knowledge-quality h3{grid-column:1/-1}.knowledge-recommendations,.knowledge-resource-panel{padding:14px}.knowledge-resource-filters select{max-width:100%;flex:1}.knowledge-resource-panel footer{align-items:flex-start;flex-direction:column}.knowledge-shortcuts>button,.knowledge-shortcuts>a{padding:13px 10px}.knowledge-shortcuts strong{font-size:12px}.knowledge-detail-overlay{padding:10px}.knowledge-detail-dialog{padding:12px}.knowledge-detail-dialog .case-library-detail header{flex-direction:column}}
.case-library-toolbar { display: flex; justify-content: flex-start; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0 0 14px; }
.case-library-create { margin-left: auto; flex: 0 0 auto; }
.case-library-panel { font-family: "MiSans", "Microsoft YaHei UI", "PingFang SC", sans-serif; color: #18363d; }
.case-library-panel button, .case-library-panel input, .case-library-panel textarea, .case-library-panel select { font-size: 15px; }
.case-library-panel .case-management-scroll small, .case-library-panel .case-library-category, .case-library-panel .compile-publish-toggle { font-size: 14px; }
.upload-button { cursor: pointer; }
.upload-group { display: inline-flex; align-items: center; gap: 8px; }
.upload-group select { height: 40px; padding: 0 10px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #fff; color: #24515a; }
.case-library-heading { margin: 0 0 18px; }
.case-library-heading h1 { margin: 0 0 6px; font-size: clamp(1.7rem, 2.8vw, 2.35rem); }
.case-library-heading p { margin: 0; max-width: 68ch; }
.case-library-compile { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.compile-publish-toggle { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted, #64748b); font-size: 13px; cursor: pointer; }
.compile-publish-toggle input { width: 15px; height: 15px; accent-color: #2f7d6c; }
.button-primary.ai-compile { background: #2f7d6c; }
.button-primary.ai-compile:disabled { opacity: .45; cursor: not-allowed; }
.entry-checkbox { flex: 0 0 auto; width: 15px; height: 15px; accent-color: #2f7d6c; cursor: pointer; }
.case-management-scroll > button.entry-selected { border-color: rgba(47, 125, 108, .3); background: #edf7f4; }
.case-library-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.case-library-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 0 0 16px; }
.case-library-stats article { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid var(--line, #e1e9ea); border-radius: 8px; background: #fff; color: var(--text-muted, #64748b); }
.case-library-stats article strong { display: block; font-size: 20px; line-height: 1.15; color: var(--text-primary, #16313a); }
.case-library-stats article small { display: block; font-size: 12px; white-space: nowrap; }
.case-library-stats article.warning { color: #b45309; border-color: #fde6c8; background: #fffbeb; }
.case-library-stats article.warning strong { color: #92400e; }
.case-library-detail dd { overflow-wrap: anywhere; }
.case-library-category { display: flex; align-items: center; gap: 8px; margin: 10px 0; color: var(--text-muted, #64748b); font-size: 13px; }
.case-library-category select { flex: 1; min-width: 0; height: 34px; padding: 0 8px; border: 1px solid var(--line, #e1e9ea); border-radius: 6px; background: #fff; color: var(--text-primary, #16313a); }
.knowledge-type-tabs { display: flex; gap: 4px; margin: 10px 0 2px; padding: 3px; border: 1px solid var(--line, #e1e9ea); border-radius: 7px; background: #f6fafb; }
.knowledge-type-tabs button { flex: 1; min-width: 0; padding: 6px 6px; border: 0; border-radius: 5px; background: transparent; color: var(--text-muted, #64748b); font-size: 12px; white-space: nowrap; cursor: pointer; }
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
  .case-library-modal-card form > div { grid-template-columns: 1fr; }
  .case-library-list { position: static; height: auto; max-height: none; }
  .case-library-list .case-management-scroll { max-height: 420px; }
  .case-library-create { margin-left: 0; width: 100%; justify-content: center; }
}
@media (max-width: 560px) {
  .case-library-modal-card form { padding: 14px; }
}
</style>
