<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Activity, ArrowLeft, ArrowRight, BookOpenCheck, Brain, Check, ChevronDown, ChevronRight, CircleAlert, Crosshair, ExternalLink, Eye, EyeOff, Layers3, LoaderCircle, LocateFixed, Maximize2, Minimize2, MousePointer2, PanelLeftClose, PanelLeftOpen, RotateCcw, ScanLine, Sparkles, Target, Video, X, ZoomIn } from '@lucide/vue';
import { getAnatomyExercises, getAnatomyGlossary, getAnatomyTextbook, sendAgentMessage, submitAnatomy } from '../api';
import anatomyImage from '../assets/medical/anatomy-organs.png';
import AnatomyViewer3D from '../components/anatomy/AnatomyViewer3D.vue';
import { mockAnatomyExercises } from '../data/anatomy';
import { anatomyAtlasNodes, anatomyAtlasSystems, type AnatomyAtlasHotspot } from '../data/anatomyAtlas';
import { anatomyImageSources, anatomyVideos } from '../data/anatomyResources';
import { ANATOMY_SYSTEMS_3D, ANATOMY_SYSTEM_3D_BY_ID, system3DColor } from '../data/anatomy3d';
import type { AnatomyExercise, AnatomyResult, AnatomyTextbookResult } from '../types';

interface Point { x: number; y: number }
interface Zone extends Point { width: number; height: number; shape?: 'ellipse' | 'rect'; covered?: boolean }

const route = useRoute();
const router = useRouter();
const systems = ['全部', '循环系统', '呼吸系统', '消化系统', '泌尿系统', '神经系统'];
const exercises = ref<AnatomyExercise[]>(mockAnatomyExercises.map((item) => ({ ...item, graph_node_ids: [...item.graph_node_ids] })));
const viewMode = ref<'body' | 'atlas' | 'practice'>('body');
const activeSystem = ref('循环系统');
const activeId = ref(exercises.value[0].id);
const point = ref<Point | null>(null);
const selectedZone = ref('');
const result = ref<AnatomyResult | null>(null);
const loading = ref(false);
const message = ref('');
const completed = ref(0);
const selectedStructure = ref('');
const atlasNodeId = ref('heart_overview');
const atlasStructureId = ref('');
const atlasResourceMode = ref<'videos' | 'images'>('videos');
const atlasNavCollapsed = ref(false);
const atlasResourcesExpanded = ref(false);
const imageFrame = ref<HTMLElement | null>(null);
const isDraggingImage = ref(false);
const imageDragStartX = ref(0);
const imageScrollStart = ref(0);
const imageMoved = ref(false);
const textbook = ref<AnatomyTextbookResult | null>(null);
const textbookLoading = ref(false);
const showTextbook = ref(false);
const agentLoading = ref(false);
const agentReply = ref('');
const agentPrompt = ref('');
const bodyViewer = ref<InstanceType<typeof AnatomyViewer3D> | null>(null);
const bodySelection = ref<{ id: string; name: string; system: string; systemName: string } | null>(null);
const hiddenSystems = ref<string[]>([]);
const bodyAutoRotate = ref(true);
const bodyStats = ref({ parts: 0, triangles: 0 });
const bodyWorkbench = ref<HTMLElement | null>(null);
const isBodyFullscreen = ref(false);
const focusedSystem = ref('');
const bodySystemCounts = ref<Record<string, number>>({});
const glossary = ref<Record<string, string>>({});
const bodyDisplayName = computed(() => {
  const selected = bodySelection.value;
  if (!selected) return '';
  return glossary.value[selected.name] ?? selected.name;
});
const hiddenDataSystems = computed(() =>
  hiddenSystems.value.flatMap((id) => ANATOMY_SYSTEM_3D_BY_ID[id]?.members ?? [])
);
const focusedMembers = computed(() =>
  focusedSystem.value ? (ANATOMY_SYSTEM_3D_BY_ID[focusedSystem.value]?.members ?? []) : []
);

const zones: Record<string, Zone> = {
  neck_midline: { x: 50, y: 9, width: 10, height: 14, shape: 'rect' },
  left_chest: { x: 54, y: 31, width: 20, height: 18 },
  midline_chest_abdomen: { x: 50, y: 38, width: 12, height: 50, shape: 'rect' },
  upper_mid_chest: { x: 51, y: 25, width: 18, height: 12 },
  left_lung: { x: 68, y: 26, width: 24, height: 32 },
  right_lung: { x: 32, y: 26, width: 24, height: 32 },
  right_upper_abdomen: { x: 35, y: 49, width: 31, height: 20 },
  left_upper_abdomen: { x: 63, y: 52, width: 25, height: 18 },
  epigastrium: { x: 54, y: 57, width: 27, height: 11 },
  central_abdomen: { x: 49, y: 69, width: 34, height: 25 },
  colon_frame: { x: 50, y: 69, width: 55, height: 35 },
  flank_bilateral: { x: 57, y: 69, width: 45, height: 24 },
  ureter_bilateral: { x: 54, y: 78, width: 36, height: 22 },
  pelvis_midline: { x: 50, y: 87, width: 19, height: 14 },
  head: { x: 50, y: 3, width: 24, height: 8, covered: false },
  posterior_head: { x: 50, y: 3, width: 24, height: 8, covered: false },
  lower_head: { x: 50, y: 5, width: 18, height: 8, covered: false },
  spine_midline: { x: 50, y: 47, width: 12, height: 70, covered: false }
};

const filtered = computed(() => activeSystem.value === '全部' ? exercises.value : exercises.value.filter((item) => item.system === activeSystem.value));
const active = computed(() => exercises.value.find((item) => item.id === activeId.value) ?? exercises.value[0]);
const activeZone = computed(() => zones[active.value.answer_zone]);
const activeStructure = computed(() => active.value.substructures?.find((item) => item.name === selectedStructure.value) ?? active.value.substructures?.[0]);
const covered = computed(() => activeZone.value?.covered !== false);
const score = computed(() => result.value ? Math.round(result.value.score_items.reduce((sum, item) => sum + item.score, 0) / result.value.score_items.length) : null);
const markerStyle = computed(() => point.value ? { left: point.value.x + '%', top: point.value.y + '%' } : {});
const zoneStyle = computed(() => activeZone.value ? {
  left: (activeZone.value.x - activeZone.value.width / 2) + '%',
  top: (activeZone.value.y - activeZone.value.height / 2) + '%',
  width: activeZone.value.width + '%',
  height: activeZone.value.height + '%',
  borderRadius: activeZone.value.shape === 'rect' ? '8px' : '50%'
} : {});
const visibleSystems = computed(() => viewMode.value === 'atlas' ? [...anatomyAtlasSystems] : systems);
const atlasNode = computed(() => anatomyAtlasNodes.find((item) => item.id === atlasNodeId.value) ?? anatomyAtlasNodes[0]);
const atlasNodesForSystem = computed(() => anatomyAtlasNodes.filter((item) => item.system === activeSystem.value));
const atlasParent = computed(() => anatomyAtlasNodes.find((item) => item.id === atlasNode.value.parent_id));
const atlasStructure = computed(() => atlasNode.value.structures.find((item) => item.id === atlasStructureId.value));
const atlasTargets = computed(() => atlasNode.value.hotspots.filter((item) => item.target_id));
const systemVideos = computed(() => anatomyVideos.filter((item) => item.system === activeSystem.value));
const systemImageSources = computed(() => anatomyImageSources.filter((item) => item.system === activeSystem.value));
const verifiedImageCount = computed(() => systemImageSources.value.filter((item) => item.status === '可接入').length);
const pendingImageCount = computed(() => systemImageSources.value.length - verifiedImageCount.value);
const atlasLevelLabel = (level: 'system' | 'organ' | 'detail') => level === 'system' ? '系统总览' : level === 'organ' ? '器官精细图' : '精细结构图';
const atlasLevelStatus = (level: 'system' | 'organ' | 'detail') => level === 'system' ? '第 1 层 · 系统总览' : level === 'organ' ? '第 2 层 · 器官精细图' : '第 3 层 · 精细结构图';

function hotspotStyle(hotspot: AnatomyAtlasHotspot) {
  return {
    left: (hotspot.x - hotspot.width / 2) + '%',
    top: (hotspot.y - hotspot.height / 2) + '%',
    width: hotspot.width + '%',
    height: hotspot.height + '%'
  };
}

function switchMode(mode: 'body' | 'atlas' | 'practice') {
  viewMode.value = mode;
  if (mode === 'body') {
    bodySelection.value = null;
  } else if (mode === 'atlas') {
    if (!anatomyAtlasSystems.includes(activeSystem.value as typeof anatomyAtlasSystems[number])) activeSystem.value = '循环系统';
    const root = anatomyAtlasNodes.find((item) => item.system === activeSystem.value && item.level === 'system');
    if (root) chooseAtlasNode(root.id);
  } else if (!systems.includes(activeSystem.value)) {
    changeSystem('全部');
  }
}

function toggleSystem(systemId: string) {
  const hidden = hiddenSystems.value;
  hiddenSystems.value = hidden.includes(systemId)
    ? hidden.filter((item) => item !== systemId)
    : [...hidden, systemId];
}

function focusOnSystem(systemId: string) {
  // Focusing a hidden system would show an empty stage, so reveal it first.
  if (systemId) hiddenSystems.value = hiddenSystems.value.filter((id) => id !== systemId);
  focusedSystem.value = systemId;
  bodySelection.value = null;
  agentReply.value = '';
  agentPrompt.value = '';
}

function groupCount(systemId: string): number {
  const system = ANATOMY_SYSTEM_3D_BY_ID[systemId];
  if (!system) return 0;
  return system.members.reduce((total, member) => total + (bodySystemCounts.value[member] ?? 0), 0);
}

function onBodyReady(payload: { parts: number; triangles: number; systems: Record<string, number> }) {
  bodyStats.value = { parts: payload.parts, triangles: payload.triangles };
  bodySystemCounts.value = payload.systems;
}

async function toggleBodyFullscreen() {
  const element = bodyWorkbench.value;
  if (!element) return;
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await element.requestFullscreen();
    }
  } catch {
    // Fullscreen can be blocked (iframe policy, permissions); the layout stays usable.
  }
}

function syncFullscreenState() {
  isBodyFullscreen.value = document.fullscreenElement === bodyWorkbench.value;
}

function onBodySelect(payload: { id: string; name: string; system: string; systemName: string }) {
  bodySelection.value = payload;
  agentReply.value = '';
  agentPrompt.value = '';
}

function onBodyClear() {
  bodySelection.value = null;
  agentReply.value = '';
  agentPrompt.value = '';
}

async function askBodyAgent(prompt: string) {
  const selected = bodySelection.value;
  if (!selected || agentLoading.value) return;
  agentLoading.value = true;
  agentPrompt.value = prompt;
  agentReply.value = '';
  const context = `当前解剖系统：${selected.systemName}；图谱：三维人体解剖模型；结构：${selected.name}`;
  try {
    const response = await sendAgentMessage(
      `${context}\n请围绕“${prompt}”进行医学教学讲解。只用于医学教育，不作诊断；优先引用已接入教材依据。`,
      'student',
      'anatomy_lab'
    );
    agentReply.value = response.reply;
  } catch {
    agentReply.value = '智能讲解服务暂不可用。你可以先查看教材详解，或稍后重试。';
  } finally {
    agentLoading.value = false;
  }
}

function chooseAtlasNode(id: string, structureId = '') {
  atlasNodeId.value = id;
  atlasStructureId.value = structureId;
  agentReply.value = '';
  agentPrompt.value = '';
}

function openAtlasHotspot(hotspot: AnatomyAtlasHotspot) {
  if (hotspot.target_id) chooseAtlasNode(hotspot.target_id, hotspot.structure_id ?? '');
  else if (hotspot.structure_id) atlasStructureId.value = hotspot.structure_id;
}

async function askAnatomyAgent(prompt: string) {
  if (!atlasStructure.value || agentLoading.value) return;
  agentLoading.value = true;
  agentPrompt.value = prompt;
  agentReply.value = '';
  const structure = atlasStructure.value;
  const context = `当前解剖系统：${atlasNode.value.system}；图谱：${atlasNode.value.title}；结构：${structure.name}；分类：${structure.category}；已知说明：${structure.description}；临床关联：${structure.clinical_note || '暂无'}`;
  try {
    const response = await sendAgentMessage(`${context}\n请围绕“${prompt}”进行医学教学讲解。只用于医学教育，不作诊断；优先引用已接入教材依据。`, 'student', 'anatomy_lab');
    agentReply.value = response.reply;
  } catch {
    agentReply.value = '智能讲解服务暂不可用。你可以先查看教材详解，或稍后重试。';
  } finally {
    agentLoading.value = false;
  }
}

async function openTextbook(name: string) {
  showTextbook.value = true;
  textbookLoading.value = true;
  textbook.value = null;
  try {
    textbook.value = await getAnatomyTextbook(name);
  } catch {
    textbook.value = { found: false, query: name, hint: '教材检索服务暂不可用' };
  } finally {
    textbookLoading.value = false;
  }
}

watch(atlasStructureId, (structureId) => {
  if (!structureId || !atlasStructure.value) return;
  openTextbook(atlasStructure.value.name);
});

function choose(id: string) {
  activeId.value = id;
  point.value = null;
  selectedZone.value = '';
  result.value = null;
  message.value = '';
  selectedStructure.value = '';
}

function changeSystem(system: string) {
  activeSystem.value = system;
  if (viewMode.value === 'atlas') {
    const root = anatomyAtlasNodes.find((item) => item.system === system && item.level === 'system');
    if (root) chooseAtlasNode(root.id);
    return;
  }
  const first = exercises.value.find((item) => system === '全部' || item.system === system);
  if (first) choose(first.id);
}

function contains(zone: Zone, value: Point) {
  const dx = Math.abs(value.x - zone.x) / (zone.width / 2);
  const dy = Math.abs(value.y - zone.y) / (zone.height / 2);
  return zone.shape === 'rect' ? dx <= 1 && dy <= 1 : dx * dx + dy * dy <= 1;
}

function locate(event: MouseEvent) {
  if (!covered.value || loading.value || imageMoved.value) { imageMoved.value = false; return; }
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  point.value = { x: ((event.clientX - rect.left) / rect.width) * 100, y: ((event.clientY - rect.top) / rect.height) * 100 };
  selectedZone.value = contains(activeZone.value, point.value) ? active.value.answer_zone : 'outside';
  result.value = null;
  message.value = '定位点已记录，提交后显示标准区域。';
}

function startImageDrag(event: PointerEvent) {
  if (!imageFrame.value) return;
  isDraggingImage.value = true;
  imageMoved.value = false;
  imageDragStartX.value = event.clientX;
  imageScrollStart.value = imageFrame.value.scrollLeft;
  imageFrame.value.setPointerCapture?.(event.pointerId);
}

function dragImage(event: PointerEvent) {
  if (!isDraggingImage.value || !imageFrame.value) return;
  const delta = event.clientX - imageDragStartX.value;
  if (Math.abs(delta) > 4) imageMoved.value = true;
  imageFrame.value.scrollLeft = imageScrollStart.value - delta;
}

function stopImageDrag(event?: PointerEvent) {
  if (event && imageFrame.value?.hasPointerCapture?.(event.pointerId)) imageFrame.value.releasePointerCapture(event.pointerId);
  isDraggingImage.value = false;
}

function fallback(correct: boolean): AnatomyResult {
  return {
    correct,
    feedback: correct ? '定位正确，能够把解剖结构与临床场景联系起来。' : '当前定位不在' + active.value.target + '的标准区域。' + active.value.explanation,
    explanation: active.value.explanation,
    clinical_link: active.value.clinical_link,
    score_items: [
      { name: '定位准确性', score: correct ? 94 : 56, max_score: 100, feedback: '依据标准区域评判。' },
      { name: '解剖名称掌握', score: correct ? 88 : 64, max_score: 100, feedback: '结合结构名称复习。' },
      { name: '临床关联理解', score: correct ? 90 : 66, max_score: 100, feedback: active.value.clinical_link },
      { name: '错误原因分析', score: correct ? 92 : 70, max_score: 100, feedback: '已显示标准区域。' }
    ]
  };
}

async function submit() {
  if (!point.value) { message.value = '请先在器官图上点击你判断的位置。'; return; }
  loading.value = true;
  try { result.value = await submitAnatomy(active.value.id, selectedZone.value); }
  catch { result.value = fallback(selectedZone.value === active.value.answer_zone); }
  finally { loading.value = false; completed.value += 1; message.value = ''; }
}

function next() {
  const index = filtered.value.findIndex((item) => item.id === active.value.id);
  choose(filtered.value[(index + 1) % filtered.value.length]?.id ?? exercises.value[0].id);
}

onMounted(async () => {
  try {
    const remote = await getAnatomyExercises();
    if (remote.length) exercises.value = remote;
  } catch {}
  try {
    const terms = await getAnatomyGlossary();
    glossary.value = terms.terms ?? {};
  } catch {}
  const requested = typeof route.query.exercise === 'string' ? route.query.exercise : '';
  if (requested && exercises.value.some((item) => item.id === requested)) {
    viewMode.value = 'practice';
    choose(requested);
  }
  document.addEventListener('fullscreenchange', syncFullscreenState);
});

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState);
  if (document.fullscreenElement) void document.exitFullscreen();
});
</script>

<template>
  <div class="workspace-page anatomy-page">
    <header class="page-title-row anatomy-page-heading">
      <div>
        <span class="section-kicker">虚拟解剖实验室 · 观察与定位</span>
        <h1>在三维结构中学习人体</h1>
        <p>从系统总览进入器官和精细结构，点击热点获取教材依据，再用定位练习检验空间认知。</p>
      </div>
      <div class="anatomy-summary">
        <span><strong>{{ exercises.length }}</strong><small>练习项目</small></span>
        <span><strong>{{ anatomyAtlasSystems.length }}</strong><small>人体系统</small></span>
        <span><strong>{{ completed }}</strong><small>本次完成</small></span>
      </div>
    </header>

    <div class="anatomy-mode-switch" role="tablist" aria-label="选择解剖学习模式">
      <button type="button" role="tab" :aria-selected="viewMode === 'body'" :class="{ active: viewMode === 'body' }" @click="switchMode('body')"><ScanLine :size="18" /><span><strong>三维人体解剖</strong><small>点击结构查看教材依据</small></span></button>
      <button type="button" role="tab" :aria-selected="viewMode === 'atlas'" :class="{ active: viewMode === 'atlas' }" @click="switchMode('atlas')"><Layers3 :size="18" /><span><strong>图谱分层浏览</strong><small>系统 → 器官 → 精细结构</small></span></button>
      <button type="button" role="tab" :aria-selected="viewMode === 'practice'" :class="{ active: viewMode === 'practice' }" @click="switchMode('practice')"><Crosshair :size="18" /><span><strong>空间定位测验</strong><small>点击结构并获得即时反馈</small></span></button>
    </div>
    <p class="anatomy-flow-note"><MousePointer2 :size="15" /><template v-if="viewMode === 'body'">拖动旋转三维人体，滚轮缩放，点击任意结构进入 AI 讲解与教材溯源。</template><template v-else-if="viewMode === 'atlas'">建议先点击图中热点完成结构探索，再切换到"空间定位测验"检验学习结果。</template><template v-else>在人体图上点击你判断的位置，提交后显示标准区域与评分。</template></p>

    <div v-if="viewMode !== 'body'" class="anatomy-system-tabs" role="tablist" aria-label="选择人体系统">
      <button v-for="system in visibleSystems" :key="system" type="button" role="tab" :aria-selected="activeSystem === system" :class="{ active: activeSystem === system }" @click="changeSystem(system)">
        <Brain v-if="system === '神经系统'" :size="17" /><Activity v-else :size="17" />{{ system }}
      </button>
    </div>

    <section v-if="viewMode === 'body'" ref="bodyWorkbench" class="anatomy-body-workbench" :class="{ 'is-fullscreen': isBodyFullscreen }">
      <aside class="body-system-rail">
        <header><span><Layers3 :size="18" /><b>人体系统</b></span><small>{{ ANATOMY_SYSTEMS_3D.length }} 个系统</small></header>
        <div class="body-system-list">
          <div class="body-system-row" :class="{ active: !focusedSystem }">
            <button type="button" class="body-system-focus" @click="focusOnSystem('')">
              <i class="body-system-all" />
              <span><strong>整体人体</strong><small>{{ bodyStats.parts }} 个结构 · 观察系统之间的位置关系</small></span>
            </button>
          </div>
          <div v-for="system in ANATOMY_SYSTEMS_3D" :key="system.id" class="body-system-row" :class="{ active: focusedSystem === system.id, muted: hiddenSystems.includes(system.id) }">
            <button type="button" class="body-system-focus" :title="system.summary" @click="focusOnSystem(system.id)">
              <i :style="{ background: system.color }" />
              <span><strong>{{ system.name }}</strong><small>{{ groupCount(system.id) }} 个结构 · {{ focusedSystem === system.id ? '正在单独查看' : '点击单独查看' }}</small></span>
            </button>
            <button type="button" class="body-system-eye" :title="(hiddenSystems.includes(system.id) ? '显示' : '隐藏') + system.name" :aria-label="(hiddenSystems.includes(system.id) ? '显示' : '隐藏') + system.name" :aria-pressed="!hiddenSystems.includes(system.id)" @click="toggleSystem(system.id)">
              <EyeOff v-if="hiddenSystems.includes(system.id)" :size="15" /><Eye v-else :size="15" />
            </button>
          </div>
        </div>
        <div class="body-viewer-tools">
          <button type="button" :class="{ active: bodyAutoRotate }" @click="bodyAutoRotate = !bodyAutoRotate"><RotateCcw :size="15" />自动旋转</button>
          <button type="button" @click="bodyViewer?.resetView()"><LocateFixed :size="15" />复位</button>
          <button type="button" class="body-fullscreen-button" :aria-pressed="isBodyFullscreen" :title="isBodyFullscreen ? '退出全屏（Esc）' : '全屏查看三维人体（Esc 退出）'" @click="toggleBodyFullscreen">
            <Minimize2 v-if="isBodyFullscreen" :size="15" /><Maximize2 v-else :size="15" />{{ isBodyFullscreen ? '退出全屏' : '全屏查看' }}
          </button>
        </div>
        <div class="body-viewer-meta">
          <span><strong>{{ bodyStats.parts }}</strong><small>可选中结构</small></span>
          <span><strong>{{ Math.round(bodyStats.triangles / 1000) }}k</strong><small>三角面</small></span>
        </div>
        <p class="body-attribution">模型：BodyParts3D 4.0 · CC BY 4.0</p>
      </aside>

      <main class="body-stage">
        <AnatomyViewer3D
          ref="bodyViewer"
          :hidden-systems="hiddenDataSystems"
          :focus-systems="focusedMembers"
          :selected-id="bodySelection?.id ?? ''"
          :auto-rotate="bodyAutoRotate"
          @select="onBodySelect"
          @clear="onBodyClear"
          @ready="onBodyReady"
        />
        <footer class="body-stage-note">
          <span><MousePointer2 :size="15" />点击结构查看详情</span>
          <span><RotateCcw :size="15" />拖动旋转 · 滚轮缩放</span>
          <small v-if="bodySelection">{{ bodySelection.systemName }} · {{ bodyDisplayName }}</small>
          <small v-else-if="focusedSystem">{{ ANATOMY_SYSTEM_3D_BY_ID[focusedSystem]?.name }} · 单独查看中</small>
          <small v-else>整体人体 · 尚未选中结构</small>
        </footer>
      </main>

      <aside class="body-detail-panel">
        <template v-if="bodySelection">
          <div class="body-selection-head">
            <i :style="{ background: system3DColor(bodySelection.system) }" />
            <div><span>{{ bodySelection.systemName }}</span><h2>{{ bodyDisplayName }}</h2><small v-if="bodyDisplayName !== bodySelection.name">{{ bodySelection.name }}</small></div>
          </div>
          <section class="body-agent-block">
            <strong><Sparkles :size="16" />AnatomyAgent 讲解</strong>
            <div class="atlas-agent-prompts">
              <button type="button" :disabled="agentLoading" @click="askBodyAgent('它的主要功能和结构特点是什么？')">功能结构</button>
              <button type="button" :disabled="agentLoading" @click="askBodyAgent('它与周围结构有什么空间关系？')">空间关系</button>
              <button type="button" :disabled="agentLoading" @click="askBodyAgent('它有哪些重要的临床联系？')">临床联系</button>
              <button type="button" :disabled="agentLoading" @click="askBodyAgent('请用考试重点总结它。')">考试重点</button>
            </div>
            <div v-if="agentLoading || agentReply" class="atlas-agent-answer" role="status" aria-live="polite">
              <strong><Sparkles :size="15" /> AnatomyAgent{{ agentLoading ? ' 正在检索教材并组织讲解' : ' 讲解' }}</strong>
              <p v-if="agentLoading">正在结合当前结构、教材索引和知识图谱生成回答…</p>
              <p v-else>{{ agentReply }}</p>
            </div>
          </section>
          <div class="body-detail-actions">
            <button class="button-secondary" type="button" @click="openTextbook(bodyDisplayName)"><BookOpenCheck :size="16" />教材详解</button>
            <button class="text-button" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: bodyDisplayName } })">知识图谱 <ArrowRight :size="15" /></button>
          </div>
        </template>
        <div v-else class="body-empty-detail">
          <MousePointer2 :size="26" />
          <strong>{{ focusedSystem ? ANATOMY_SYSTEM_3D_BY_ID[focusedSystem]?.name + ' · 等待选择' : '点击模型中的结构' }}</strong>
          <p v-if="focusedSystem">{{ ANATOMY_SYSTEM_3D_BY_ID[focusedSystem]?.summary }} 点击图中任意结构查看 AI 讲解、教材依据和知识图谱入口。</p>
          <p v-else>左侧可以单独查看某个系统，也可以按系统显示或隐藏结构。点击任意结构后，这里会给出 AI 讲解、教材依据和知识图谱入口。</p>
        </div>
      </aside>
    </section>

    <section v-else-if="viewMode === 'atlas'" class="anatomy-atlas-workbench" :class="{ 'nav-collapsed': atlasNavCollapsed }">
      <aside class="atlas-layer-nav">
        <header><span><Layers3 :size="18" /><b>图谱层级</b></span><div><small>{{ atlasNodesForSystem.length }} 张图</small><button type="button" :title="atlasNavCollapsed ? '展开图谱层级' : '收起图谱层级'" @click="atlasNavCollapsed = !atlasNavCollapsed"><PanelLeftOpen v-if="atlasNavCollapsed" :size="17" /><PanelLeftClose v-else :size="17" /></button></div></header>
        <div class="atlas-layer-tree">
          <button v-for="node in atlasNodesForSystem" :key="node.id" type="button" :class="[{ active: node.id === atlasNode.id }, `level-${node.level}`]" @click="chooseAtlasNode(node.id)">
            <span><Activity v-if="node.level === 'system'" :size="16" /><ZoomIn v-else :size="15" /></span><span><strong>{{ node.title }}</strong><small>{{ atlasLevelLabel(node.level) }}</small></span><ChevronRight :size="15" />
          </button>
        </div>
        <div class="atlas-learning-tip"><MousePointer2 :size="17" /><p><strong>点击图中热点</strong>带边框区域可以进入下一层或查看结构说明。</p></div>
      </aside>

      <main class="atlas-image-lab">
        <header>
          <div class="atlas-breadcrumb"><button v-if="atlasParent" type="button" @click="chooseAtlasNode(atlasParent.id)"><ArrowLeft :size="15" />{{ atlasParent.title }}</button><span v-else>{{ atlasNode.system }}</span><ChevronRight :size="14" /><strong>{{ atlasNode.title }}</strong></div>
          <span><Eye :size="15" />{{ atlasNode.instruction }}</span>
        </header>
        <div class="atlas-image-canvas">
          <div class="atlas-image-stage" :style="{ aspectRatio: atlasNode.image_aspect }">
            <img :src="atlasNode.image" :alt="atlasNode.title" />
            <button v-for="(hotspot, index) in atlasNode.hotspots" :key="hotspot.id" type="button" class="atlas-hotspot" :class="{ selected: hotspot.structure_id === atlasStructureId, 'is-full-image': hotspot.width === 100 && hotspot.height === 100 }" :style="hotspotStyle(hotspot)" :aria-label="`查看${hotspot.label}`" @click="openAtlasHotspot(hotspot)"><span>{{ index + 1 }}<b>{{ hotspot.label }}</b></span></button>
          </div>
        </div>
        <footer><span><MousePointer2 :size="15" />{{ atlasNode.hotspots.length }} 个可交互热点</span><small>{{ atlasNode.source_label }} · 仅用于医学教学</small></footer>
      </main>

      <aside class="atlas-detail-panel">
        <div class="atlas-level-status"><span>{{ atlasNode.system }}</span><b>{{ atlasLevelStatus(atlasNode.level) }}</b></div>
        <span class="section-kicker">当前图谱</span><h2>{{ atlasNode.title }}</h2><p>{{ atlasNode.description }}</p>
        <section v-if="atlasTargets.length" class="atlas-drilldown-list">
          <strong><ZoomIn :size="17" />点击下钻</strong>
          <button v-for="target in atlasTargets" :key="target.id" type="button" @click="openAtlasHotspot(target)"><span><b>{{ target.label }}</b><small>进入{{ atlasNode.level === 'organ' ? '精细结构图' : '器官精细图' }}</small></span><ArrowRight :size="16" /></button>
        </section>
        <section v-if="atlasNode.structures.length" class="atlas-structure-list">
          <strong><Layers3 :size="17" />本图结构</strong>
          <div><button v-for="structure in atlasNode.structures" :key="structure.id" type="button" :class="{ active: structure.id === atlasStructureId }" @click="atlasStructureId = structure.id">{{ structure.name }}</button></div>
        </section>
        <article v-if="atlasStructure" class="atlas-structure-detail">
          <span>{{ atlasStructure.category }}</span><h3>{{ atlasStructure.name }}</h3><p>{{ atlasStructure.description }}</p><div><Activity :size="16" /><small>临床关联</small><strong>{{ atlasStructure.clinical_note }}</strong></div>
          <div class="atlas-structure-actions">
            <button class="button-primary" type="button" @click="askAnatomyAgent('它的主要功能和结构特点是什么？')"><Brain :size="16" />AI讲解</button>
            <button class="button-secondary textbook-reopen" type="button" @click="openTextbook(atlasStructure.name)"><BookOpenCheck :size="16" />教材详解</button>
          </div>
          <div class="atlas-agent-prompts" aria-label="解剖讲解快捷问题">
            <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('它与周围结构有什么空间关系？')">空间关系</button>
            <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('它有哪些重要的临床联系？')">临床联系</button>
            <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('请用考试重点总结它。')">考试重点</button>
          </div>
          <div v-if="agentLoading || agentReply" class="atlas-agent-answer" role="status" aria-live="polite">
            <strong><Sparkles :size="15" /> AnatomyAgent{{ agentLoading ? ' 正在检索教材并组织讲解' : ' 讲解' }}</strong>
            <p v-if="agentLoading">正在结合当前结构、教材索引和知识图谱生成回答…</p>
            <p v-else>{{ agentReply }}</p>
            <small v-if="agentPrompt">本次问题：{{ agentPrompt }}</small>
          </div>
        </article>
        <div v-else class="atlas-empty-detail"><MousePointer2 :size="25" /><strong>选择一个热点</strong><p>点击图中带编号区域，查看该结构的中文说明与临床关联。</p></div>
        <section class="atlas-resource-panel">
          <button class="atlas-resource-toggle" type="button" :aria-expanded="atlasResourcesExpanded" @click="atlasResourcesExpanded = !atlasResourcesExpanded"><strong><Video :size="17" />配套学习资源</strong><span><small>{{ systemVideos.length }} 个视频 · {{ verifiedImageCount }} 个可接入图源 · {{ pendingImageCount }} 个待核对</small><ChevronDown :size="16" /></span></button>
          <div v-show="atlasResourcesExpanded" class="atlas-resource-content">
          <div class="atlas-resource-tabs" role="tablist" aria-label="选择资源类型">
            <button type="button" role="tab" :aria-selected="atlasResourceMode === 'videos'" :class="{ active: atlasResourceMode === 'videos' }" @click="atlasResourceMode = 'videos'">B站视频</button>
            <button type="button" role="tab" :aria-selected="atlasResourceMode === 'images'" :class="{ active: atlasResourceMode === 'images' }" @click="atlasResourceMode = 'images'">解剖图源</button>
          </div>
          <div v-if="atlasResourceMode === 'videos'" class="atlas-resource-list">
            <a v-for="video in systemVideos" :key="video.id" :href="video.url" target="_blank" rel="noopener noreferrer">
              <span><b>{{ video.topic }} · {{ video.title }}</b><small>{{ video.publisher }} · {{ video.duration }}</small></span><em :class="{ pending: video.status === '待复核' }">{{ video.status }}</em><ExternalLink :size="15" />
            </a>
          </div>
          <div v-else class="atlas-resource-list">
            <a v-for="source in systemImageSources" :key="source.id" :href="source.url" target="_blank" rel="noopener noreferrer">
              <span><b>{{ source.topic }} · {{ source.title }}</b><small>{{ source.figure }} · {{ source.license }}</small></span><em :class="{ pending: source.status !== '可接入' }">{{ source.status }}</em><ExternalLink :size="15" />
            </a>
          </div>
          <p>外部资源仅用于课程学习。OpenStax 图源采用 CC BY-NC-SA 4.0；Blausen 候选须以各 Wikimedia 文件页的最终授权为准，核对前不作为正式课程素材。</p>
          </div>
        </section>
        <button class="text-button atlas-graph-link" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: atlasStructure?.name || atlasNode.title } })">查看相关知识图谱 <ArrowRight :size="15" /></button>
      </aside>
    </section>

    <section v-else class="anatomy-workbench">
      <aside class="anatomy-exercise-rail">
        <header><span><ScanLine :size="18" />定位任务</span><small>{{ filtered.length }} 项</small></header>
        <div class="anatomy-exercise-list">
          <button v-for="(exercise, index) in filtered" :key="exercise.id" type="button" :class="{ active: exercise.id === active.id }" @click="choose(exercise.id)">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <span><strong>{{ exercise.title }}</strong><small>{{ exercise.system }}<template v-if="exercise.organ"> · {{ exercise.organ }}</template></small></span>
            <CircleAlert v-if="zones[exercise.answer_zone]?.covered === false" :size="15" /><ArrowRight v-else :size="16" />
          </button>
        </div>
      </aside>

      <main class="anatomy-visual-lab">
        <header class="anatomy-lab-toolbar">
          <div><LocateFixed :size="18" /><span><strong>躯干前面观</strong><small>点击图像完成定位</small></span></div>
          <span class="orientation-mark"><b>R</b> 患者右侧 · 患者左侧 <b>L</b></span>
        </header>
        <div ref="imageFrame" class="anatomy-image-frame" :class="{ 'is-dragging': isDraggingImage }" @pointerdown="startImageDrag" @pointermove="dragImage" @pointerup="stopImageDrag" @pointercancel="stopImageDrag" @pointerleave="stopImageDrag">
          <button class="anatomy-image-stage" type="button" :disabled="!covered" :aria-label="covered ? '在人体图上定位' + active.target : '当前图谱未覆盖该结构'" @click="locate">
            <img :src="anatomyImage" alt="虚拟教学用人体躯干器官解剖图" />
            <span v-if="point" class="student-marker" :class="{ correct: result?.correct, wrong: result && !result.correct }" :style="markerStyle"><Crosshair :size="24" /></span>
            <span v-if="result && covered" class="standard-zone" :style="zoneStyle"><span>标准区域</span></span>
          </button>
          <div v-if="!covered" class="anatomy-unavailable-state"><Brain :size="34" /><strong>当前图谱未覆盖该结构</strong><p>现有图片为躯干前面观，请先选择循环、呼吸、消化或泌尿系统练习。</p></div>
        </div>
        <footer class="anatomy-stage-note"><span><Target :size="16" />学生点击点</span><span><LocateFixed :size="16" />提交后显示标准区域</span><small>虚拟教学图像，不含真实患者信息</small></footer>
      </main>

      <aside class="anatomy-task-panel">
        <div class="anatomy-task-status"><span>{{ active.system }}</span><b>{{ result ? '已评判' : '待定位' }}</b></div>
        <span class="section-kicker">当前任务</span><h2>{{ active.title }}</h2><p class="anatomy-prompt">{{ active.prompt }}</p>
        <section v-if="active.substructures?.length" class="anatomy-structure-panel">
          <header><strong><Layers3 :size="17" />{{ active.organ || active.target }}精细结构</strong><small>{{ active.substructures.length }} 项</small></header>
          <div class="anatomy-structure-tabs">
            <button v-for="structure in active.substructures" :key="structure.name" type="button" :class="{ active: activeStructure?.name === structure.name }" @click="selectedStructure = structure.name">{{ structure.name }}</button>
          </div>
          <article v-if="activeStructure">
            <span>{{ activeStructure.category }}</span><strong>{{ activeStructure.name }}</strong><p>{{ activeStructure.description }}</p><small v-if="activeStructure.clinical_note">临床提示：{{ activeStructure.clinical_note }}</small>
          </article>
        </section>
        <div v-if="!result" class="anatomy-instructions">
          <strong><Crosshair :size="17" />操作步骤</strong>
          <ol><li><span>1</span>观察器官相对位置</li><li><span>2</span>点击判断的中心位置</li><li><span>3</span>提交并查看临床关联</li></ol>
          <p v-if="message" class="anatomy-message"><CircleAlert :size="16" />{{ message }}</p>
        </div>
        <div v-else class="anatomy-result" :class="result.correct ? 'is-correct' : 'is-wrong'">
          <header><span><Check v-if="result.correct" :size="20" /><CircleAlert v-else :size="20" /></span><div><small>{{ result.correct ? '定位正确' : '建议重新定位' }}</small><strong>综合得分 {{ score }}</strong></div></header>
          <p>{{ result.feedback }}</p>
          <div class="anatomy-score-list"><div v-for="item in result.score_items" :key="item.name"><span><b>{{ item.name }}</b><strong>{{ item.score }}</strong></span><i><span :style="{ width: item.score + '%' }"></span></i></div></div>
          <section><strong><BookOpenCheck :size="17" />解剖解释</strong><p>{{ result.explanation }}</p></section>
          <section><strong><Activity :size="17" />临床关联</strong><p>{{ result.clinical_link }}</p></section>
        </div>
        <section class="anatomy-video-panel">
          <header><strong><Video :size="17" />B站讲解视频</strong><small>课程组审核后发布</small></header>
          <template v-if="active.video_resources?.length">
            <a v-for="video in active.video_resources.filter((item) => item.url)" :key="video.title" :href="video.url" target="_blank" rel="noopener noreferrer"><span><b>{{ video.title }}</b><small>{{ video.status }} · {{ video.contributor || '课程组' }}</small></span><ExternalLink :size="16" /></a>
            <p v-if="!active.video_resources.some((item) => item.url)">链接待负责同学收集，并由课程组审核内容与版权后开放。</p>
          </template>
          <p v-else>当前器官暂无已录入视频，链接采集清单可继续补充。</p>
        </section>
        <div class="anatomy-actions">
          <button v-if="!result" class="button-primary" type="button" :disabled="loading || !covered" @click="submit"><LoaderCircle v-if="loading" class="spin" :size="18" /><Target v-else :size="18" />{{ loading ? '正在评判' : '提交定位' }}</button>
          <template v-else><button class="button-secondary" type="button" @click="choose(active.id)"><RotateCcw :size="17" />重新练习</button><button class="button-primary" type="button" @click="next">下一题<ArrowRight :size="17" /></button></template>
          <button class="text-button" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: active.target } })">查看相关知识图谱</button>
        </div>
      </aside>
    </section>

    <div v-if="showTextbook" class="textbook-modal" role="dialog" aria-modal="true" aria-label="教材详解">
      <div class="textbook-modal-card">
        <header>
          <div><span><BookOpenCheck :size="20" /></span><div><strong>{{ atlasStructure?.name }} · 教材详解</strong><small>基于《系统解剖学》（第10版）本地索引检索</small></div></div>
          <button class="icon-button" type="button" title="关闭" aria-label="关闭教材详解" @click="showTextbook = false"><X :size="18" /></button>
        </header>
        <div class="textbook-modal-body">
          <div v-if="textbookLoading" class="textbook-state"><LoaderCircle class="spin" :size="24" />正在检索教材</div>
          <template v-else-if="textbook?.found">
            <p class="textbook-citation">{{ textbook.citation }}</p>
            <h2>{{ textbook.title }}</h2>
            <p class="textbook-content">{{ textbook.content }}</p>
          </template>
          <div v-else class="textbook-state empty"><BookOpenCheck :size="24" /><strong>暂未找到详细讲解</strong><p>{{ textbook?.hint || '可查看相关知识图谱或在教材中进一步检索。' }}</p></div>
        </div>
      </div>
    </div>
  </div>
</template>
