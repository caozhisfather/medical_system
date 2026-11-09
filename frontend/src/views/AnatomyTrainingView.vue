<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Activity, ArrowLeft, ArrowRight, BarChart3, BookOpenCheck, Brain, Check, ChevronDown, ChevronRight, CircleAlert, CircleCheck, Crosshair, ExternalLink, Eye, EyeOff, GraduationCap, House, Layers3, LoaderCircle, LocateFixed, Maximize2, Minimize2, Minus, MousePointer2, Network, PanelLeftClose, PanelLeftOpen, Plus, RotateCcw, ScanLine, Search, Target, Video, X, Zap, ZoomIn } from '@lucide/vue';
import { getAnatomyExercises, getAnatomyGlossary, getAnatomyEvidence, getAnatomyNotes, getAnatomyTextbook, saveAnatomyNote, sendAgentMessage, speakDigitalHuman, submitAnatomy } from '../api';
import anatomyImage from '../assets/medical/anatomy-organs.png';
import AnatomyGraphIcon from '../components/AnatomyGraphIcon.vue';
import AnatomyViewer3D from '../components/anatomy/AnatomyViewer3D.vue';
import AnatomyQuizPanel from '../components/anatomy/AnatomyQuizPanel.vue';
import DigitalHumanLecture from '../components/anatomy/DigitalHumanLecture.vue';
import digitalHumanPoster from '../assets/digital-human/medical-tutor.png';
import MarkdownContent from '../components/MarkdownContent.vue';
import TextbookPageViewer from '../components/TextbookPageViewer.vue';
import { mockAnatomyExercises } from '../data/anatomy';
import { anatomyAtlasNodes, anatomyAtlasSystems, type AnatomyAtlasHotspot } from '../data/anatomyAtlas';
import { resolveAnatomyPracticeTarget } from '../data/anatomyPractice';
import { anatomyImageSources, anatomyVideos } from '../data/anatomyResources';
import { ANATOMY_SYSTEMS_3D, ANATOMY_SYSTEM_3D_BY_ID, ATLAS_3D_URL, ATLAS_ORGAN_URL, system3DColor, system3DName, type AnatomyOrgan, type AnatomyOrganPayload } from '../data/anatomy3d';
import type { AgentAction, AgentResponse, AnatomyEvidenceItem, AnatomyEvidenceResponse, AnatomyExercise, AnatomyResult, AnatomyTextbookResult, DigitalHumanResponse, TextbookAnnotationStroke } from '../types';

interface Point { x: number; y: number }
interface Zone extends Point { width: number; height: number; shape?: 'ellipse' | 'rect'; covered?: boolean }
interface TextbookNoteEditor {
  id: string;
  content: string;
  annotations: TextbookAnnotationStroke[];
  saving: boolean;
  revision: number;
  savedRevision: number;
}
interface TextbookNoteSchedule {
  timer: ReturnType<typeof setTimeout>;
  item: AnatomyEvidenceItem;
}

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
const atlasImageAspect = ref('');
const atlasResourceMode = ref<'videos' | 'images'>('videos');
const atlasNavCollapsed = ref(false);
const atlasResourcesExpanded = ref(false);
const imageFrame = ref<HTMLElement | null>(null);
const isDraggingImage = ref(false);
const imageDragStartX = ref(0);
const imageDragStartY = ref(0);
const imageScrollStart = ref(0);
const imageScrollTop = ref(0);
const imageMoved = ref(false);
const practiceZoom = ref(1);
const practiceInfoTab = ref<'structure' | 'clinical'>('structure');
const practiceWorkbench = ref<HTMLElement | null>(null);
const isPracticeFullscreen = ref(false);
const textbook = ref<AnatomyTextbookResult | null>(null);
const textbookLoading = ref(false);
const showTextbook = ref(false);
const textbookEvidence = ref<AnatomyEvidenceResponse | null>(null);
const textbookNotes = reactive<Record<string, TextbookNoteEditor>>({});
const textbookNoteTimers = new Map<string, TextbookNoteSchedule>();
const textbookNoteSaveChains = new Map<string, Promise<void>>();
let textbookRequestId = 0;
const agentLoading = ref(false);
const agentReply = ref('');
const agentResponse = ref<AgentResponse | null>(null);
const digitalHuman = ref<DigitalHumanResponse | null>(null);
const digitalHumanLoading = ref(false);
const digitalHumanPlaying = ref(false);
const digitalHumanMuted = ref(false);
const digitalHumanError = ref('');
const digitalHumanSessionId = `anatomy-tutor-${Date.now().toString(36)}`;
let digitalHumanRequestId = 0;
watch(agentReply, value => {
  if (!value) {
    agentResponse.value = null;
    resetDigitalHuman();
  }
}, { flush: 'sync' });
const agentPrompt = ref('');
const bodyViewer = ref<InstanceType<typeof AnatomyViewer3D> | null>(null);
const bodySelection = ref<{ id: string; name: string; system: string; systemName: string } | null>(null);
const hiddenSystems = ref<string[]>([]);
const hiddenOrganIds = ref<string[]>([]);
const hiddenPartIds = ref<string[]>([]);
const bodyAutoRotate = ref(false);
const viewedParts = ref(new Set<string>());
const structureSearch = ref('');
const showStructureSearch = ref(false);
const structureSearchInput = ref<HTMLInputElement | null>(null);
const bodyStats = ref({ parts: 0, triangles: 0 });
const quizTarget = ref<{ en: string; cn: string; system: string } | null>(null);
const bodyWorkbench = ref<HTMLElement | null>(null);
const isBodyFullscreen = ref(false);
const focusedSystem = ref('');
const focusedOrganId = ref('');
const organPayload = ref<AnatomyOrganPayload | null>(null);
const partInfo = ref<Map<string, { name: string; system: string }>>(new Map());
const bodySystemCounts = ref<Record<string, number>>({});
const glossary = ref<Record<string, string>>({});
const viewingProgress = computed(() => bodyStats.value.parts
  ? Math.round(viewedParts.value.size / bodyStats.value.parts * 1000) / 10
  : 0);
const structureMatches = computed(() => {
  const keyword = structureSearch.value.trim().toLocaleLowerCase();
  if (!keyword) return [];
  return [...partInfo.value].filter(([, info]) => info.name.toLocaleLowerCase().includes(keyword)
    || (glossary.value[info.name] ?? '').includes(keyword)).slice(0, 8);
});
const bodyDisplayName = computed(() => {
  const selected = bodySelection.value;
  if (!selected) return '';
  return glossary.value[selected.name] ?? selected.name;
});
const hiddenDataSystems = computed(() =>
  hiddenSystems.value.flatMap((id) => ANATOMY_SYSTEM_3D_BY_ID[id]?.members ?? [])
);
const hiddenDataParts = computed(() => hiddenPartIds.value);
const focusedMembers = computed(() =>
  focusedSystem.value ? (ANATOMY_SYSTEM_3D_BY_ID[focusedSystem.value]?.members ?? []) : []
);
const focusedSystemName = computed(() => ANATOMY_SYSTEM_3D_BY_ID[focusedSystem.value]?.name ?? '');
const systemOrgans = computed<AnatomyOrgan[]>(() => {
  if (!focusedSystem.value || !organPayload.value) return [];
  return organPayload.value.systems.find((entry) => entry.system === focusedSystem.value)?.organs ?? [];
});
const focusedOrgan = computed<AnatomyOrgan | null>(
  () => systemOrgans.value.find((organ) => organ.id === focusedOrganId.value) ?? null
);
const focusParts = computed(() => focusedOrgan.value?.partIds ?? []);
const organFineStructures = computed(() => {
  const organ = focusedOrgan.value;
  if (!organ) return [];
  return organ.partIds.map((id) => {
    const info = partInfo.value.get(id);
    const english = info?.name ?? id;
    return { id, english, label: glossary.value[english] ?? english };
  });
});

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
const practiceTarget = computed(() => resolveAnatomyPracticeTarget(active.value.id, activeStructure.value?.name ?? ''));
const practiceZone = computed<Zone | undefined>(() => {
  const target = practiceTarget.value?.hotspot;
  if (!target) return activeZone.value;
  return {
    x: target.x,
    y: target.y,
    width: target.width,
    height: target.height,
    shape: 'ellipse'
  };
});
const covered = computed(() => Boolean(practiceZone.value));
const practiceImageUrl = computed(() => practiceTarget.value?.node.image || anatomyImage);
const practiceImageAspect = ref('1086 / 1448');
const practiceStageStyle = computed(() => {
  const [width, height] = practiceImageAspect.value.split('/').map(Number);
  const zoom = practiceZoom.value;
  const ratio = width / height;
  return { aspectRatio: practiceImageAspect.value, width: `min(${zoom * 100}%, ${ratio * zoom * 100}cqh, ${ratio * zoom * 540}px)` };
});
const practicePrompt = computed(() => practiceTarget.value
  ? `请在《${practiceTarget.value.node.title}》中点击：${practiceTarget.value.label}`
  : active.value.prompt);
const practiceCitation = computed(() => practiceTarget.value
  ? `${practiceTarget.value.node.title} · ${practiceTarget.value.node.source_label}`
  : '本地二维训练图');
const score = computed(() => result.value ? Math.round(result.value.score_items.reduce((sum, item) => sum + item.score, 0) / result.value.score_items.length) : null);
const markerStyle = computed(() => point.value ? { left: point.value.x + '%', top: point.value.y + '%' } : {});
const zoneStyle = computed(() => practiceZone.value ? {
  left: (practiceZone.value.x - practiceZone.value.width / 2) + '%',
  top: (practiceZone.value.y - practiceZone.value.height / 2) + '%',
  width: practiceZone.value.width + '%',
  height: practiceZone.value.height + '%',
  borderRadius: practiceZone.value.shape === 'rect' ? '8px' : '50%'
} : {});
const visibleSystems = computed(() => viewMode.value === 'atlas' ? [...anatomyAtlasSystems] : systems);
const atlasNode = computed(() => anatomyAtlasNodes.find((item) => item.id === atlasNodeId.value) ?? anatomyAtlasNodes[0]);
const atlasNodesForSystem = computed(() => anatomyAtlasNodes.filter((item) => item.system === activeSystem.value));
const atlasRoot = computed(() => atlasNodesForSystem.value.find(node => node.level === 'system'));
const atlasStageStyle = computed(() => {
  const aspectRatio = atlasImageAspect.value || atlasNode.value.image_aspect;
  const [width, height] = aspectRatio.split('/').map(Number);
  return { aspectRatio, maxWidth: width > 0 && height > 0 ? (width / height * 560) + 'px' : undefined };
});
const atlasSystemIconIds = Object.fromEntries(ANATOMY_SYSTEMS_3D.map(system => [system.name, 'anatomy_system_' + system.id]));
const atlasParent = computed(() => anatomyAtlasNodes.find((item) => item.id === atlasNode.value.parent_id));
const atlasStructure = computed(() => atlasNode.value.structures.find((item) => item.id === atlasStructureId.value));
const atlasTargets = computed(() => atlasNode.value.hotspots.filter((item) => item.target_id));
const systemVideos = computed(() => anatomyVideos.filter((item) => item.system === activeSystem.value));
const systemImageSources = computed(() => anatomyImageSources.filter((item) => item.system === activeSystem.value));
const atlasLevelLabel = (level: 'system' | 'organ' | 'detail') => level === 'system' ? '系统总览' : level === 'organ' ? '器官精细图' : '精细结构图';
const atlasLevelStatus = (level: 'system' | 'organ' | 'detail') => level === 'system' ? '第 1 层 · 系统总览' : level === 'organ' ? '第 2 层 · 器官精细图' : '第 3 层 · 精细结构图';

function hotspotStyle(hotspot: AnatomyAtlasHotspot) {
  const left = Math.max(0, Math.min(100 - hotspot.width, hotspot.x - hotspot.width / 2));
  const top = Math.max(0, Math.min(100 - hotspot.height, hotspot.y - hotspot.height / 2));
  return {
    left: left + '%',
    top: top + '%',
    width: hotspot.width + '%',
    height: hotspot.height + '%'
  };
}

function syncAtlasImageAspect(event: Event) {
  const image = event.target as HTMLImageElement;
  if (image.naturalWidth && image.naturalHeight) atlasImageAspect.value = `${image.naturalWidth} / ${image.naturalHeight}`;
}

function syncPracticeImageAspect(event: Event) {
  const image = event.target as HTMLImageElement;
  if (image.naturalWidth && image.naturalHeight) practiceImageAspect.value = `${image.naturalWidth} / ${image.naturalHeight}`;
}

watch(practiceTarget, (target) => {
  practiceImageAspect.value = target?.node.image_aspect || '1086 / 1448';
}, { immediate: true });

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
  focusedOrganId.value = '';
  bodySelection.value = null;
  agentReply.value = '';
  agentPrompt.value = '';
}

function toggleOrgan(organ: AnatomyOrgan) {
  const hidden = hiddenOrganIds.value.includes(organ.id);
  hiddenOrganIds.value = hidden
    ? hiddenOrganIds.value.filter((id) => id !== organ.id)
    : [...hiddenOrganIds.value, organ.id];
  if (hidden) hiddenPartIds.value = hiddenPartIds.value.filter((id) => !organ.partIds.includes(id));
  else hiddenPartIds.value = [...new Set([...hiddenPartIds.value, ...organ.partIds])];
}

function toggleFineStructure(partId: string) {
  hiddenPartIds.value = hiddenPartIds.value.includes(partId)
    ? hiddenPartIds.value.filter((id) => id !== partId)
    : [...hiddenPartIds.value, partId];
  const organ = systemOrgans.value.find((item) => item.partIds.includes(partId));
  if (organ && organ.partIds.every((id) => hiddenPartIds.value.includes(id))) {
    if (!hiddenOrganIds.value.includes(organ.id)) hiddenOrganIds.value = [...hiddenOrganIds.value, organ.id];
  } else if (organ) {
    hiddenOrganIds.value = hiddenOrganIds.value.filter((id) => id !== organ.id);
  }
}

function revealPart(partId: string) {
  hiddenPartIds.value = hiddenPartIds.value.filter((id) => id !== partId);
  const organ = systemOrgans.value.find((item) => item.partIds.includes(partId));
  if (organ) hiddenOrganIds.value = hiddenOrganIds.value.filter((id) => id !== organ.id);
}

function focusOrgan(organId: string) {
  const organ = systemOrgans.value.find((item) => item.id === organId);
  if (organ) {
    hiddenOrganIds.value = hiddenOrganIds.value.filter((id) => id !== organ.id);
    hiddenPartIds.value = hiddenPartIds.value.filter((id) => !organ.partIds.includes(id));
  }
  focusedOrganId.value = focusedOrganId.value === organId ? '' : organId;
  bodySelection.value = null;
  agentReply.value = '';
  agentPrompt.value = '';
}

function selectOrganPart(partId: string) {
  revealPart(partId);
  const info = partInfo.value.get(partId);
  if (!info) return;
  onBodySelect({ id: partId, name: info.name, system: info.system, systemName: system3DName(info.system) });
}

function startQuizForSelection() {
  const selected = bodySelection.value;
  if (!selected) return;
  quizTarget.value = {
    en: selected.name,
    cn: glossary.value[selected.name] ?? '',
    system: selected.systemName
  };
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
  const element = document.fullscreenElement;
  isBodyFullscreen.value = Boolean(element && element === bodyWorkbench.value);
  isPracticeFullscreen.value = Boolean(element && element === practiceWorkbench.value);
}

async function togglePracticeFullscreen() {
  const element = practiceWorkbench.value;
  if (!element) return;
  try {
    if (document.fullscreenElement === element) await document.exitFullscreen();
    else await element.requestFullscreen();
  } catch {
    message.value = '当前浏览器无法进入全屏，可以继续使用放大和缩小。';
  }
}

async function adjustPracticeZoom(amount: number) {
  const frame = imageFrame.value;
  if (!frame) return;
  const x = (frame.scrollLeft + frame.clientWidth / 2) / frame.scrollWidth;
  const y = (frame.scrollTop + frame.clientHeight / 2) / frame.scrollHeight;
  practiceZoom.value = Math.max(1, Math.min(2, practiceZoom.value + amount));
  await nextTick();
  frame.scrollTo(x * frame.scrollWidth - frame.clientWidth / 2, y * frame.scrollHeight - frame.clientHeight / 2);
}

function resetPracticeView() {
  practiceZoom.value = 1;
  imageFrame.value?.scrollTo(0, 0);
}

async function openStructureSearch() {
  showStructureSearch.value = !showStructureSearch.value;
  if (showStructureSearch.value) {
    await nextTick();
    structureSearchInput.value?.focus();
  }
}

function selectSearchResult(partId: string, dataSystem: string) {
  const group = ANATOMY_SYSTEMS_3D.find(system => system.members.includes(dataSystem));
  focusOnSystem(group?.id ?? '');
  selectOrganPart(partId);
  showStructureSearch.value = false;
}

function onBodySelect(payload: { id: string; name: string; system: string; systemName: string }) {
  viewedParts.value.add(payload.id);
  bodySelection.value = payload;
  agentReply.value = '';
  agentPrompt.value = '';
}

function onBodyClear() {
  bodySelection.value = null;
  agentReply.value = '';
  agentPrompt.value = '';
}

function resetDigitalHuman() {
  digitalHumanRequestId += 1;
  digitalHuman.value = null;
  digitalHumanLoading.value = false;
  digitalHumanPlaying.value = false;
  digitalHumanError.value = '';
}

function toSpokenText(markdown: string) {
  return markdown
    .replace(/```[\s\S]*?```/g, '')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^\s*[-*_]{3,}\s*$/gm, '')
    .replace(/^\s*[-+*]\s+/gm, '')
    .replace(/^\s*\d+[.)]\s+/gm, '')
    .replace(/^\s*[#>|]+\s*/gm, '')
    .replace(/[|*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 1200);
}

async function startDigitalHumanNarration(reply: string, topic: string) {
  const spokenText = toSpokenText(reply);
  if (!spokenText) return;
  const requestId = ++digitalHumanRequestId;
  digitalHumanLoading.value = true;
  digitalHumanPlaying.value = false;
  digitalHumanError.value = '';
  try {
    const response = await speakDigitalHuman({
      session_id: digitalHumanSessionId,
      text: spokenText,
      emotion: 'teaching',
      action: 'explain',
      avatar_id: 'standardized_patient_001',
      voice: 'zh_female_warm',
      mode: 'liveact',
      context: { role: 'tutor', topic, speaking_style: '教材优先、清晰分段、医学教学语气' }
    });
    if (requestId !== digitalHumanRequestId) return;
    digitalHuman.value = response;
    digitalHumanPlaying.value = true;
  } catch (error) {
    if (requestId === digitalHumanRequestId) digitalHumanError.value = error instanceof Error ? error.message : '数字人服务暂不可用';
  } finally {
    if (requestId === digitalHumanRequestId) digitalHumanLoading.value = false;
  }
}

function replayDigitalHuman() {
  if (agentReply.value) void startDigitalHumanNarration(agentReply.value, bodyDisplayName.value || atlasStructure.value?.name || '解剖结构');
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
      'anatomy_lab',
      { query: selected.name, part_id: selected.id }
    );
    if (bodySelection.value?.id !== selected.id || viewMode.value !== 'body') return;
    agentReply.value = response.reply;
    agentResponse.value = response;
    void startDigitalHumanNarration(response.reply, selected.name);
  } catch (error) {
    if (bodySelection.value?.id === selected.id && viewMode.value === 'body') agentReply.value = error instanceof Error ? error.message : '智能讲解服务暂不可用。';
  } finally {
    agentLoading.value = false;
  }
}

function atlasNameTerms(value: string) {
  const compact = value.replace(/[^\u4e00-\u9fffA-Za-z0-9]/g, '').toLocaleLowerCase();
  const terms = new Set<string>();
  for (const size of [2, 3]) {
    for (let index = 0; index <= compact.length - size; index += 1) {
      terms.add(compact.slice(index, index + size));
    }
  }
  return terms;
}

function resolveAtlasTargetStructure(targetId: string, source: AnatomyAtlasHotspot) {
  const target = anatomyAtlasNodes.find((item) => item.id === targetId);
  if (!target) return source.structure_id ?? '';
  if (source.structure_id && target.structures.some((item) => item.id === source.structure_id)) {
    return source.structure_id;
  }
  const sourceTerms = atlasNameTerms(source.label);
  let best: { id: string; score: number } | null = null;
  for (const hotspot of target.hotspots) {
    if (!hotspot.structure_id) continue;
    const targetTerms = atlasNameTerms(hotspot.label);
    const score = [...sourceTerms].filter((term) => targetTerms.has(term)).length;
    if (score > (best?.score ?? 0)) best = { id: hotspot.structure_id, score };
  }
  return best?.id ?? target.hotspots.find((item) => item.structure_id)?.structure_id ?? target.structures[0]?.id ?? '';
}

function chooseAtlasNode(id: string, structureId = '') {
  const nextNode = anatomyAtlasNodes.find((item) => item.id === id);
  atlasNodeId.value = id;
  atlasStructureId.value = structureId;
  atlasImageAspect.value = nextNode?.image_aspect ?? '';
  agentReply.value = '';
  agentPrompt.value = '';
}

function openAtlasHotspot(hotspot: AnatomyAtlasHotspot) {
  if (hotspot.target_id) chooseAtlasNode(
    hotspot.target_id,
    resolveAtlasTargetStructure(hotspot.target_id, hotspot)
  );
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
    const response = await sendAgentMessage(`${context}\n请围绕“${prompt}”进行医学教学讲解。只用于医学教育，不作诊断；优先引用已接入教材依据。`, 'student', 'anatomy_lab', { query: structure.name });
    if (atlasStructure.value?.id !== structure.id || viewMode.value !== 'atlas') return;
    agentReply.value = response.reply;
    agentResponse.value = response;
    void startDigitalHumanNarration(response.reply, structure.name);
  } catch (error) {
    if (atlasStructure.value?.id === structure.id && viewMode.value === 'atlas') agentReply.value = error instanceof Error ? error.message : '智能讲解服务暂不可用。';
  } finally {
    agentLoading.value = false;
  }
}

async function executeAgentAction(action: AgentAction) {
  if (action.type === 'open_textbook') {
    await openTextbook(action.target);
  } else if (action.type === 'open_graph') {
    if (document.fullscreenElement) await document.exitFullscreen();
    await router.push({ path: '/knowledge-graph', query: { q: action.target } });
  } else if (action.type === 'highlight_structure') {
    if (!partInfo.value.has(action.target)) return;
    const group = organPayload.value?.systems.find(entry => entry.organs.some(organ => organ.partIds.includes(action.target)));
    const organ = group?.organs.find(entry => entry.partIds.includes(action.target));
    if (group && organ) {
      focusedSystem.value = group.system;
      focusedOrganId.value = organ.id;
    hiddenSystems.value = hiddenSystems.value.filter(id => id !== group.system);
    revealPart(action.target);
    } else {
      focusedSystem.value = '';
      focusedOrganId.value = '';
      hiddenSystems.value = [];
    }
    viewMode.value = 'body';
    const previous = agentResponse.value;
    selectOrganPart(action.target);
    if (previous) { agentReply.value = previous.reply; agentResponse.value = previous; }
  }
}

async function openTextbook(name: string) {
  await flushAllTextbookNotes();
  const requestId = ++textbookRequestId;
  showTextbook.value = true;
  textbookLoading.value = true;
  textbook.value = null;
  textbookEvidence.value = null;
  for (const key of Object.keys(textbookNotes)) delete textbookNotes[key];
  try {
    const [legacy, evidence] = await Promise.allSettled([getAnatomyTextbook(name), getAnatomyEvidence(name)]);
    if (requestId !== textbookRequestId) return;
    if (legacy.status === 'fulfilled') textbook.value = legacy.value;
    if (evidence.status === 'fulfilled') {
      textbookEvidence.value = evidence.value;
      await loadTextbookNotes(evidence.value.evidence, requestId);
    }
    if (legacy.status === 'rejected' && evidence.status === 'rejected') {
      textbook.value = { found: false, query: name, hint: '教材检索服务暂不可用' };
    }
  } catch {
    textbook.value = { found: false, query: name, hint: '教材检索服务暂不可用' };
  } finally {
    if (requestId === textbookRequestId) textbookLoading.value = false;
  }
}

function textbookNoteKey(item: AnatomyEvidenceItem) {
  return `${item.document_id}:${item.page}`;
}

function textbookNoteFor(item: AnatomyEvidenceItem) {
  const key = textbookNoteKey(item);
  if (!textbookNotes[key]) {
    textbookNotes[key] = {
      id: '',
      content: '',
      annotations: [],
      saving: false,
      revision: 0,
      savedRevision: 0
    };
  }
  return textbookNotes[key];
}

async function loadTextbookNotes(items: AnatomyEvidenceItem[], requestId: number) {
  await Promise.all(items.slice(0, 5).map(async (item) => {
    const editor = textbookNoteFor(item);
    const revisionAtLoad = editor.revision;
    try {
      const notes = await getAnatomyNotes(item.document_id, item.page);
      if (requestId !== textbookRequestId || editor.revision !== revisionAtLoad) return;
      editor.content = notes[0]?.content ?? '';
      editor.annotations = notes[0]?.annotations ?? [];
      editor.id = notes[0]?.id ?? '';
      editor.revision = 0;
      editor.savedRevision = 0;
      editor.saving = false;
    } catch {
      // Notes require a signed-in account; the editor still works after login.
    }
  }));
}

function scheduleTextbookNoteSave(item: AnatomyEvidenceItem, delay = 650) {
  const key = textbookNoteKey(item);
  const editor = textbookNoteFor(item);
  const previous = textbookNoteTimers.get(key);
  if (previous) clearTimeout(previous.timer);
  editor.saving = true;
  const timer = setTimeout(() => {
    const scheduled = textbookNoteTimers.get(key);
    if (scheduled?.timer === timer) textbookNoteTimers.delete(key);
    void flushTextbookNote(item);
  }, delay);
  textbookNoteTimers.set(key, { timer, item });
}

function flushTextbookNote(item: AnatomyEvidenceItem) {
  const key = textbookNoteKey(item);
  const editor = textbookNoteFor(item);
  if (editor.revision <= editor.savedRevision) {
    editor.saving = false;
    return Promise.resolve();
  }
  const previous = textbookNoteSaveChains.get(key) ?? Promise.resolve();
  const next = previous.catch(() => undefined).then(async () => {
    if (editor.revision <= editor.savedRevision) {
      editor.saving = false;
      return;
    }
    const revision = editor.revision;
    const snapshot = {
      content: editor.content,
      annotations: editor.annotations.map((stroke) => ({
        ...stroke,
        points: stroke.points.map((point) => ({ ...point }))
      }))
    };
    let persisted = false;
    try {
      const response = await saveAnatomyNote({
        note_id: editor.id || undefined,
        document_id: item.document_id,
        page: item.page,
        line_start: item.line_start,
        line_end: item.line_end,
        content: snapshot.content,
        annotations: snapshot.annotations
      });
      editor.id = response.id;
      editor.savedRevision = Math.max(editor.savedRevision, revision);
      persisted = true;
    } catch {
      // Unauthenticated demo mode keeps the text in the open editor.
    }
    if (persisted && editor.savedRevision >= editor.revision) {
      editor.saving = false;
    } else if (persisted && editor.revision > revision) {
      scheduleTextbookNoteSave(item, 0);
    } else {
      editor.saving = false;
    }
  });
  textbookNoteSaveChains.set(key, next);
  const cleanup = () => {
    if (textbookNoteSaveChains.get(key) === next) textbookNoteSaveChains.delete(key);
  };
  void next.then(cleanup, cleanup);
  return next;
}

function saveTextbookNote(item: AnatomyEvidenceItem) {
  const editor = textbookNoteFor(item);
  editor.revision += 1;
  scheduleTextbookNoteSave(item);
}

function updateTextbookAnnotations(item: AnatomyEvidenceItem, annotations: TextbookAnnotationStroke[]) {
  const editor = textbookNoteFor(item);
  editor.annotations = annotations;
  saveTextbookNote(item);
}

async function flushAllTextbookNotes() {
  const items = [...textbookNoteTimers.values()].map((entry) => entry.item);
  for (const entry of textbookNoteTimers.values()) clearTimeout(entry.timer);
  textbookNoteTimers.clear();
  await Promise.allSettled([
    ...items.map((item) => flushTextbookNote(item)),
    ...textbookNoteSaveChains.values()
  ]);
}

function choose(id: string) {
  activeId.value = id;
  point.value = null;
  selectedZone.value = '';
  result.value = null;
  message.value = '';
  selectedStructure.value = '';
  practiceInfoTab.value = 'structure';
  resetPracticeView();
}

function choosePracticeStructure(name: string) {
  if (name === activeStructure.value?.name || loading.value) return;
  selectedStructure.value = name;
  point.value = null;
  selectedZone.value = '';
  result.value = null;
  message.value = '';
  resetPracticeView();
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
  const zone = practiceZone.value;
  if (!zone || loading.value || imageMoved.value) { imageMoved.value = false; return; }
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  point.value = { x: ((event.clientX - rect.left) / rect.width) * 100, y: ((event.clientY - rect.top) / rect.height) * 100 };
  selectedZone.value = contains(zone, point.value) ? active.value.answer_zone : 'outside';
  result.value = null;
  message.value = '定位点已记录，提交后显示标准区域。';
}

function startImageDrag(event: PointerEvent) {
  const frame = imageFrame.value;
  imageMoved.value = false;
  if (!frame || event.pointerType !== 'mouse' || event.button !== 0
    || (frame.scrollWidth <= frame.clientWidth && frame.scrollHeight <= frame.clientHeight)) return;
  isDraggingImage.value = true;
  imageDragStartX.value = event.clientX;
  imageDragStartY.value = event.clientY;
  imageScrollStart.value = frame.scrollLeft;
  imageScrollTop.value = frame.scrollTop;
}

function dragImage(event: PointerEvent) {
  if (!isDraggingImage.value || !imageFrame.value) return;
  const dx = event.clientX - imageDragStartX.value;
  const dy = event.clientY - imageDragStartY.value;
  if (Math.hypot(dx, dy) > 4 || imageMoved.value) {
    imageMoved.value = true;
    imageFrame.value.setPointerCapture?.(event.pointerId);
    imageFrame.value.scrollLeft = imageScrollStart.value - dx;
    imageFrame.value.scrollTop = imageScrollTop.value - dy;
  }
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
  try {
    result.value = await submitAnatomy({
      exercise_id: active.value.id,
      selected_zone: selectedZone.value,
      node_id: practiceTarget.value?.node.id ?? '',
      structure_id: practiceTarget.value?.targetId ?? '',
      click_x: point.value.x,
      click_y: point.value.y
    });
  }
  catch { result.value = fallback(selectedZone.value === active.value.answer_zone); }
  finally { loading.value = false; completed.value += 1; message.value = ''; }
}

function next() {
  const index = filtered.value.findIndex((item) => item.id === active.value.id);
  choose(filtered.value[(index + 1) % filtered.value.length]?.id ?? exercises.value[0].id);
}

watch(() => route.fullPath, () => {
  if (route.path !== '/student/anatomy') return;
  const requestedMode = typeof route.query.mode === 'string' ? route.query.mode : '';
  if (requestedMode === 'practice') {
    viewMode.value = 'practice';
  } else if (requestedMode === 'atlas') {
    viewMode.value = 'atlas';
  } else if (!requestedMode) {
    viewMode.value = 'body';
  }
  const requestedSystem = typeof route.query.system === 'string' ? route.query.system : '';
  if (requestedSystem && ANATOMY_SYSTEM_3D_BY_ID[requestedSystem]) {
    viewMode.value = 'body';
    focusOnSystem(requestedSystem);
  }
});

onMounted(async () => {
  try {
    const remote = await getAnatomyExercises();
    if (remote.length) exercises.value = remote;
  } catch {}
  try {
    const terms = await getAnatomyGlossary();
    glossary.value = terms.terms ?? {};
  } catch {}
  try {
    const [organResponse, atlasResponse] = await Promise.all([fetch(ATLAS_ORGAN_URL), fetch(ATLAS_3D_URL)]);
    if (organResponse.ok) organPayload.value = (await organResponse.json()) as AnatomyOrganPayload;
    if (atlasResponse.ok) {
      const manifest = await atlasResponse.json() as { parts?: Array<{ id: string; name: string; system: string }> };
      partInfo.value = new Map((manifest.parts ?? []).map((part) => [part.id, { name: part.name, system: part.system }]));
    }
  } catch {}
  const requested = typeof route.query.exercise === 'string' ? route.query.exercise : '';
  if (requested && exercises.value.some((item) => item.id === requested)) {
    viewMode.value = 'practice';
    choose(requested);
  }
  const requestedMode = typeof route.query.mode === 'string' ? route.query.mode : '';
  if (requestedMode === 'practice') viewMode.value = 'practice';
  if (requestedMode === 'atlas') viewMode.value = 'atlas';
  const requestedSystem = typeof route.query.system === 'string' ? route.query.system : '';
  if (requestedSystem && ANATOMY_SYSTEM_3D_BY_ID[requestedSystem]) {
    viewMode.value = 'body';
    focusOnSystem(requestedSystem);
  }
  document.addEventListener('fullscreenchange', syncFullscreenState);
});

onBeforeUnmount(() => {
  textbookRequestId += 1;
  void flushAllTextbookNotes();
  document.removeEventListener('fullscreenchange', syncFullscreenState);
  if (document.fullscreenElement) void document.exitFullscreen();
});
</script>

<template>
  <div class="workspace-page anatomy-page" :class="{ 'is-atlas-mode': viewMode === 'atlas', 'is-practice-mode': viewMode === 'practice' }">
    <header class="lab-hero">
      <div>
        <span class="section-kicker">虚拟解剖室</span>
        <h1>在三维结构中学习人体</h1>
        <p>从系统总览进入器官和精细结构，点击热点获取教材依据，再用定位练习检验空间认知。</p>
      </div>
      <div v-if="viewMode !== 'atlas'" class="lab-summary" aria-label="解剖室概览">
        <span><Layers3 /><strong>{{ exercises.length }}</strong><small>练习项目</small></span>
        <span><Network /><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong><small>人体系统</small></span>
        <span><CircleCheck /><strong>{{ completed }}</strong><small>本次完成</small></span>
      </div>
    </header>

    <div class="anatomy-mode-switch" data-tour="anatomy-mode-switch" role="tablist" aria-label="选择解剖学习模式">
      <button type="button" role="tab" :aria-selected="viewMode === 'body'" :class="{ active: viewMode === 'body' }" @click="switchMode('body')"><ScanLine :size="18" /><span><strong>三维人体解剖</strong><small>点击结构查看教材依据</small></span></button>
      <button type="button" role="tab" :aria-selected="viewMode === 'atlas'" :class="{ active: viewMode === 'atlas' }" @click="switchMode('atlas')"><Layers3 :size="18" /><span><strong>图谱分层浏览</strong><small>系统 → 器官 → 精细结构</small></span></button>
      <button type="button" role="tab" :aria-selected="viewMode === 'practice'" :class="{ active: viewMode === 'practice' }" @click="switchMode('practice')"><Crosshair :size="18" /><span><strong>空间定位测验</strong><small>点击结构并获得即时反馈</small></span></button>
    </div>
    <div v-if="viewMode !== 'body'" class="anatomy-system-tabs" role="tablist" aria-label="选择人体系统">
      <button v-for="system in visibleSystems" :key="system" type="button" role="tab" :disabled="viewMode === 'practice' && loading" :aria-selected="activeSystem === system" :class="{ active: activeSystem === system }" @click="changeSystem(system)">
        <AnatomyGraphIcon v-if="atlasSystemIconIds[system]" :node-id="atlasSystemIconIds[system]" width="24" height="24" /><ScanLine v-else :size="17" />{{ system }}
      </button>
    </div>

    <section v-if="viewMode === 'body'" ref="bodyWorkbench" class="anatomy-body-workbench" data-tour="anatomy-workspace" :class="{ 'is-fullscreen': isBodyFullscreen }">
      <aside class="body-system-rail">
        <header><span><Layers3 :size="18" /><b>人体系统</b></span><small>{{ ANATOMY_SYSTEMS_3D.length }} 个系统</small></header>
        <div class="body-system-list">
          <div class="body-system-row" :class="{ active: !focusedSystem }">
            <button type="button" class="body-system-focus" :aria-pressed="!focusedSystem" @click="focusOnSystem('')">
              <AnatomyGraphIcon node-id="anatomy_root" width="29" height="29" />
              <span><strong>整体人体</strong><small>{{ bodyStats.parts }} 个结构</small></span>
            </button>
          </div>
          <div v-for="system in ANATOMY_SYSTEMS_3D" :key="system.id" class="body-system-row" :class="{ active: focusedSystem === system.id, muted: hiddenSystems.includes(system.id) }">
            <button type="button" class="body-system-focus" :aria-pressed="focusedSystem === system.id" :title="system.summary" @click="focusOnSystem(system.id)">
              <AnatomyGraphIcon :node-id="'anatomy_system_' + system.id" width="29" height="29" />
              <span><strong>{{ system.name }}</strong><small>{{ groupCount(system.id) }} 个结构</small></span>
            </button>
            <button type="button" class="body-system-eye" :title="(hiddenSystems.includes(system.id) ? '显示' : '隐藏') + system.name" :aria-label="(hiddenSystems.includes(system.id) ? '显示' : '隐藏') + system.name" :aria-pressed="!hiddenSystems.includes(system.id)" @click="toggleSystem(system.id)">
              <EyeOff v-if="hiddenSystems.includes(system.id)" :size="15" /><Eye v-else :size="15" />
            </button>
          </div>
        </div>
        <div v-if="focusedSystem && systemOrgans.length" class="body-organ-list">
          <header><span><Layers3 :size="16" /><b>{{ focusedSystemName }} · 器官</b></span><small>{{ systemOrgans.length }} 个</small></header>
          <div>
            <div v-for="organ in systemOrgans" :key="organ.id" class="body-organ-row" :class="{ active: focusedOrganId === organ.id, muted: hiddenOrganIds.includes(organ.id) }" role="button" tabindex="0" @click="focusOrgan(organ.id)" @keydown.enter="focusOrgan(organ.id)">
              <span><strong>{{ organ.name }}</strong><small>{{ organ.partIds.length }} 个精细结构</small></span>
              <span class="body-organ-actions"><button type="button" class="body-structure-eye" :title="hiddenOrganIds.includes(organ.id) ? '显示器官' : '隐藏器官'" :aria-label="hiddenOrganIds.includes(organ.id) ? '显示器官' : '隐藏器官'" @click.stop="toggleOrgan(organ)"><EyeOff v-if="hiddenOrganIds.includes(organ.id)" :size="14" /><Eye v-else :size="14" /></button><ChevronRight :size="15" /></span>
            </div>
          </div>
        </div>
        <p class="body-attribution">模型：BodyParts3D 4.0 · CC BY 4.0</p>
      </aside>

      <div class="body-stage">
        <header class="lab-stage-bar">
          <div class="lab-stage-modes">
            <span><ScanLine :size="15" />3D 模型</span>
            <button type="button" @click="switchMode('atlas')"><Layers3 :size="15" />分层查看</button>
          </div>
          <div class="lab-stage-controls" role="group" aria-label="三维模型控制">
            <button type="button" :aria-label="isBodyFullscreen ? '退出全屏' : '全屏查看'" :title="isBodyFullscreen ? '退出全屏' : '全屏查看'" @click="toggleBodyFullscreen"><Minimize2 v-if="isBodyFullscreen" :size="16" /><Maximize2 v-else :size="16" /></button>
            <button type="button" aria-label="复位视角" title="复位视角" @click="bodyViewer?.resetView()"><LocateFixed :size="16" /></button>
            <button type="button" aria-label="放大模型" title="放大模型" @click="bodyViewer?.zoomView(.8)"><Plus :size="17" /></button>
            <button type="button" aria-label="缩小模型" title="缩小模型" @click="bodyViewer?.zoomView(1.25)"><Minus :size="17" /></button>
            <button type="button" aria-label="自动旋转" title="自动旋转" :aria-pressed="bodyAutoRotate" @click="bodyAutoRotate = !bodyAutoRotate"><RotateCcw :size="16" /></button>
          </div>
        </header>
        <AnatomyViewer3D
          ref="bodyViewer"
          :hidden-systems="hiddenDataSystems"
          :hidden-parts="hiddenDataParts"
          :focus-systems="focusedMembers"
          :focus-parts="focusParts"
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
      </div>

      <aside class="body-detail-panel" aria-label="结构信息与学习工具">
        <section class="lab-detail-overview">
          <h2><BookOpenCheck :size="18" />结构信息</h2>
          <strong>{{ bodyDisplayName || focusedOrgan?.name || focusedSystemName || '人体解剖（整体）' }}</strong>
          <p v-if="bodySelection">{{ bodySelection.systemName }} · 点击下方操作查看教材或练习。</p>
          <p v-else-if="focusedSystem">{{ ANATOMY_SYSTEM_3D_BY_ID[focusedSystem]?.summary }}。点击模型查看具体结构。</p>
          <p v-else>从整体人体进入各个系统和器官。拖动旋转模型，点击结构查看教材依据、空间关系与 AI 讲解。</p>
        </section>
        <section class="lab-quick">
          <h2><Zap :size="18" />快捷操作</h2>
          <div class="lab-quick-actions">
            <button type="button" :aria-expanded="showStructureSearch" @click="openStructureSearch"><Search :size="19" />结构检索</button>
            <button type="button" @click="switchMode('atlas')"><Target :size="19" />热点浏览</button>
            <button type="button" @click="switchMode('practice')"><Crosshair :size="19" />定位练习</button>
          </div>
          <div v-if="showStructureSearch" class="lab-structure-search">
            <input ref="structureSearchInput" v-model="structureSearch" aria-label="搜索解剖结构" placeholder="输入中文或英文结构名" />
            <div v-if="structureMatches.length" class="lab-structure-results">
              <button v-for="[id, item] in structureMatches" :key="id" type="button" @click="selectSearchResult(id, item.system)">{{ glossary[item.name] || item.name }}<ChevronRight :size="14" /></button>
            </div>
            <small v-else-if="structureSearch.trim()">没有找到匹配的结构</small>
          </div>
        </section>
        <section class="lab-progress">
          <h2><BarChart3 :size="18" />学习进度</h2>
          <div><span>本次浏览进度</span><strong>{{ viewingProgress }}%</strong></div>
          <progress :value="viewedParts.size" :max="bodyStats.parts || 1" aria-label="本次结构浏览进度"></progress>
          <small>已查看结构 <strong>{{ viewedParts.size }} / {{ bodyStats.parts }}</strong></small>
        </section>
        <div v-if="quizTarget" class="body-quiz-drawer">
          <button class="text-button" type="button" @click="quizTarget = null">关闭测验</button>
          <AnatomyQuizPanel :structure-en="quizTarget.en" :structure-cn="quizTarget.cn" :system="quizTarget.system" />
        </div>
        <section v-if="focusedOrgan" class="organ-structure-block">
          <header><span>{{ focusedSystemName }}</span><h3>{{ focusedOrgan.name }}</h3><small>{{ focusedOrgan.nameEn }}</small></header>
          <strong><Layers3 :size="15" />精细结构 · {{ organFineStructures.length }} 项</strong>
          <div class="organ-structure-list">
            <div v-for="item in organFineStructures" :key="item.id" class="body-organ-row fine" :class="{ active: bodySelection?.id === item.id, muted: hiddenPartIds.includes(item.id) }" role="button" tabindex="0" @click="selectOrganPart(item.id)" @keydown.enter="selectOrganPart(item.id)">
              <span><b>{{ item.label }}</b><small v-if="item.label !== item.english">{{ item.english }}</small></span>
              <span class="body-organ-actions"><button type="button" class="body-structure-eye" :title="hiddenPartIds.includes(item.id) ? '显示精细结构' : '隐藏精细结构'" :aria-label="hiddenPartIds.includes(item.id) ? '显示精细结构' : '隐藏精细结构'" @click.stop="toggleFineStructure(item.id)"><EyeOff v-if="hiddenPartIds.includes(item.id)" :size="13" /><Eye v-else :size="13" /></button><ChevronRight :size="14" /></span>
            </div>
          </div>
        </section>
        <template v-if="bodySelection">
          <div class="body-selection-head">
            <i :style="{ background: system3DColor(bodySelection.system) }" />
            <div><span>{{ bodySelection.systemName }}</span><h2>{{ bodyDisplayName }}</h2><small v-if="bodyDisplayName !== bodySelection.name">{{ bodySelection.name }}</small></div>
          </div>
          <section class="body-agent-block">
            <DigitalHumanLecture
              :agent-loading="agentLoading"
              :agent-reply="agentReply"
              :agent-response="agentResponse"
              :agent-prompt="agentPrompt"
              :narration="digitalHuman"
              :narration-loading="digitalHumanLoading"
              :narration-error="digitalHumanError"
              :playing="digitalHumanPlaying"
              :muted="digitalHumanMuted"
              :poster="digitalHumanPoster"
              @action="executeAgentAction"
              @replay="replayDigitalHuman"
              @update:playing="digitalHumanPlaying = $event"
              @update:muted="digitalHumanMuted = $event"
              @media-error="digitalHumanError = '数字人视频加载失败，已保留文字讲解与教材依据。'"
              @play-blocked="digitalHumanPlaying = false"
            >
              <template #prompts>
                <div class="atlas-agent-prompts">
                  <button type="button" :disabled="agentLoading" @click="askBodyAgent('它的主要功能和结构特点是什么？')">功能结构</button>
                  <button type="button" :disabled="agentLoading" @click="askBodyAgent('它与周围结构有什么空间关系？')">空间关系</button>
                  <button type="button" :disabled="agentLoading" @click="askBodyAgent('它有哪些重要的临床联系？')">临床联系</button>
                  <button type="button" :disabled="agentLoading" @click="askBodyAgent('请用考试重点总结它。')">考试重点</button>
                </div>
              </template>
            </DigitalHumanLecture>
          </section>
          <div class="body-detail-actions">
            <button class="button-primary" type="button" @click="startQuizForSelection"><Crosshair :size="16" />针对该结构出题</button>
            <button class="button-secondary" type="button" @click="openTextbook(bodyDisplayName)"><BookOpenCheck :size="16" />教材详解</button>
            <button class="text-button" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: bodyDisplayName } })">知识图谱 <ArrowRight :size="15" /></button>
          </div>
        </template>
      </aside>
    </section>

    <section v-else-if="viewMode === 'atlas'" class="anatomy-atlas-workbench" :class="{ 'nav-collapsed': atlasNavCollapsed }">
      <aside class="atlas-layer-nav">
        <header>
          <span><Layers3 :size="19" /><b>图谱层级</b></span>
          <div>
            <select :value="activeSystem" aria-label="切换图谱系统" @change="changeSystem(($event.target as HTMLSelectElement).value)">
              <option v-for="system in visibleSystems" :key="system" :value="system">{{ system }}</option>
            </select>
            <button type="button" :aria-label="atlasNavCollapsed ? '展开图谱层级' : '收起图谱层级'" :aria-expanded="!atlasNavCollapsed" @click="atlasNavCollapsed = !atlasNavCollapsed"><PanelLeftOpen v-if="atlasNavCollapsed" :size="17" /><PanelLeftClose v-else :size="17" /></button>
          </div>
        </header>
        <div class="atlas-layer-tree">
          <button v-for="node in atlasNodesForSystem" :key="node.id" type="button" :class="{ active: node.id === atlasNode.id }" :aria-current="node.id === atlasNode.id ? 'page' : undefined" @click="chooseAtlasNode(node.id)">
            <span><Activity v-if="node.level === 'system'" :size="16" /><ZoomIn v-else :size="15" /></span>
            <span><strong>{{ node.title }}</strong><small>{{ atlasLevelLabel(node.level) }}</small></span>
            <ChevronRight :size="15" />
          </button>
        </div>
      </aside>

      <div class="atlas-image-lab">
        <header>
          <nav class="atlas-breadcrumb" aria-label="图谱当前位置">
            <button v-if="atlasRoot" type="button" :aria-label="'返回' + atlasNode.system + '总览'" @click="chooseAtlasNode(atlasRoot.id)"><House :size="16" /></button>
            <ChevronRight v-if="atlasRoot" :size="13" />
            <span>{{ atlasNode.system }}</span><ChevronRight :size="13" />
            <template v-if="atlasParent && atlasParent.id !== atlasRoot?.id">
              <button type="button" @click="chooseAtlasNode(atlasParent.id)">{{ atlasParent.title }}</button><ChevronRight :size="13" />
            </template>
            <strong aria-current="page">{{ atlasNode.title }}</strong>
          </nav>
          <b class="atlas-level-chip">{{ atlasLevelStatus(atlasNode.level) }}</b>
        </header>
        <p class="atlas-image-instruction"><MousePointer2 :size="16" />{{ atlasNode.instruction }}</p>
        <div class="atlas-image-canvas">
          <div class="atlas-image-stage" :style="atlasStageStyle">
            <img :src="atlasNode.image" :alt="atlasNode.title" @load="syncAtlasImageAspect" />
            <button v-for="(hotspot, index) in atlasNode.hotspots" :key="hotspot.id" type="button" class="atlas-hotspot" :class="{ selected: hotspot.structure_id === atlasStructureId, 'is-full-image': hotspot.width === 100 && hotspot.height === 100 }" :style="hotspotStyle(hotspot)" :aria-label="`查看${hotspot.label}`" @click="openAtlasHotspot(hotspot)"><span>{{ index + 1 }}<b>{{ hotspot.label }}</b></span></button>
          </div>
        </div>
        <footer><span><MousePointer2 :size="15" />{{ atlasNode.hotspots.length }} 个可交互热点</span><small>{{ atlasNode.source_label }} · 仅用于医学教学</small></footer>
      </div>

      <aside class="atlas-detail-panel">
        <h2 class="atlas-detail-title"><AnatomyGraphIcon :node-id="atlasSystemIconIds[atlasNode.system]" width="30" height="30" />{{ atlasNode.title }}</h2><p>{{ atlasNode.description }}</p>
        <section v-if="atlasTargets.length" class="atlas-drilldown-list">
                    <button v-for="target in atlasTargets" :key="target.id" type="button" @click="openAtlasHotspot(target)"><span class="atlas-drilldown-icon"><ScanLine :size="17" /></span><span><b>{{ target.label }}</b><small>进入{{ atlasNode.level === 'organ' ? '精细结构图' : '器官精细图' }}</small></span><ChevronRight :size="16" /></button>
        </section>
        <section v-if="atlasNode.structures.length" class="atlas-structure-list">
          <strong><Layers3 :size="17" />本图结构</strong>
          <div><button v-for="structure in atlasNode.structures" :key="structure.id" type="button" :class="{ active: structure.id === atlasStructureId }" @click="atlasStructureId = structure.id">{{ structure.name }}</button></div>
        </section>
        <article v-if="atlasStructure" class="atlas-structure-detail">
          <span>{{ atlasStructure.category }}</span><h3>{{ atlasStructure.name }}</h3><p>{{ atlasStructure.description }}</p><div class="atlas-clinical-note"><Activity :size="16" /><small>临床关联</small><strong>{{ atlasStructure.clinical_note }}</strong></div>
          <div class="atlas-structure-actions">
            <button class="button-primary" type="button" @click="askAnatomyAgent('它的主要功能和结构特点是什么？')"><Brain :size="16" />AI讲解</button>
            <button class="button-secondary textbook-reopen" type="button" @click="openTextbook(atlasStructure.name)"><BookOpenCheck :size="16" />教材详解</button>
          </div>
          <DigitalHumanLecture
            :agent-loading="agentLoading"
            :agent-reply="agentReply"
            :agent-response="agentResponse"
            :agent-prompt="agentPrompt"
            :narration="digitalHuman"
            :narration-loading="digitalHumanLoading"
            :narration-error="digitalHumanError"
            :playing="digitalHumanPlaying"
            :muted="digitalHumanMuted"
            :poster="digitalHumanPoster"
            @action="executeAgentAction"
            @replay="replayDigitalHuman"
            @update:playing="digitalHumanPlaying = $event"
            @update:muted="digitalHumanMuted = $event"
            @media-error="digitalHumanError = '数字人视频加载失败，已保留文字讲解与教材依据。'"
            @play-blocked="digitalHumanPlaying = false"
          >
            <template #prompts>
              <div class="atlas-agent-prompts" aria-label="解剖讲解快捷问题">
                <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('它的主要功能和结构特点是什么？')">功能结构</button>
                <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('它与周围结构有什么空间关系？')">空间关系</button>
                <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('它有哪些重要的临床联系？')">临床联系</button>
                <button type="button" :disabled="agentLoading" @click="askAnatomyAgent('请用考试重点总结它。')">考试重点</button>
              </div>
            </template>
          </DigitalHumanLecture>
        </article>
        <div v-else class="atlas-empty-detail"><MousePointer2 :size="25" /><strong>选择一个热点</strong><p>点击图中带编号区域，查看该结构的中文说明与临床关联。</p></div>
        <button class="text-button atlas-graph-link" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: atlasStructure?.name || atlasNode.title } })">查看相关知识图谱 <ArrowRight :size="15" /></button>
      </aside>
      <section class="atlas-study-strip" aria-label="学习建议与图谱资源">
        <div class="atlas-study-summary">
          <div><GraduationCap :size="20" /><strong>学习建议</strong><small>{{ atlasTargets.length ? '先观察总览，再从热点进入下一层。' : '点击热点查看结构说明与临床关联。' }}</small></div>
          <div><Layers3 :size="18" /><strong>已进入层级</strong><small>{{ atlasLevelStatus(atlasNode.level) }}</small></div>
          <div><Crosshair :size="18" /><strong>热点数量</strong><small>{{ atlasNode.hotspots.length }} 个</small></div>
          <button class="atlas-resource-toggle" type="button" aria-controls="atlas-resource-content" :aria-expanded="atlasResourcesExpanded" @click="atlasResourcesExpanded = !atlasResourcesExpanded"><Video :size="18" /><strong>配套学习资源</strong><small>{{ systemVideos.length }} 个视频 · {{ systemImageSources.length }} 个图源</small><ChevronDown :size="16" /></button>
        </div>
          <div v-show="atlasResourcesExpanded" id="atlas-resource-content" class="atlas-resource-content">
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
    </section>

    <section v-else class="anatomy-workbench" data-tour="anatomy-practice-workspace">
      <aside class="anatomy-exercise-rail">
        <header><span><Crosshair :size="19" />定位任务</span><small>{{ filtered.length }} 项</small></header>
        <div class="anatomy-exercise-list">
          <button v-for="(exercise, index) in filtered" :key="exercise.id" type="button" :class="{ active: exercise.id === active.id }" :aria-current="exercise.id === active.id ? 'true' : undefined" :disabled="loading" @click="choose(exercise.id)">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <span><strong>{{ exercise.title }}</strong><small>{{ exercise.system }}<template v-if="exercise.organ"> · {{ exercise.organ }}</template></small></span>
            <CircleAlert v-if="zones[exercise.answer_zone]?.covered === false" :size="15" /><ArrowRight v-else :size="16" />
          </button>
        </div>
      </aside>

      <div ref="practiceWorkbench" class="anatomy-visual-lab">
        <header class="anatomy-lab-toolbar">
          <div><LocateFixed :size="18" /><span><strong>{{ practiceTarget?.node.title || '二维解剖定位' }}</strong><small>{{ covered ? '点击图中目标结构，提交后显示标准区域' : '当前任务暂无可用靶区' }}</small></span></div>
          <div class="practice-view-controls" role="group" aria-label="定位图视图控制">
            <button type="button" :aria-label="isPracticeFullscreen ? '退出全屏' : '全屏查看'" :title="isPracticeFullscreen ? '退出全屏' : '全屏查看'" @click="togglePracticeFullscreen"><Minimize2 v-if="isPracticeFullscreen" :size="16" /><Maximize2 v-else :size="16" /></button>
            <button type="button" aria-label="放大定位图" title="放大定位图" :disabled="practiceZoom >= 2" @click="adjustPracticeZoom(.25)"><Plus :size="17" /></button>
            <button type="button" aria-label="缩小定位图" title="缩小定位图" :disabled="practiceZoom <= 1" @click="adjustPracticeZoom(-.25)"><Minus :size="17" /></button>
            <button type="button" aria-label="重置视图" title="重置视图" @click="resetPracticeView"><RotateCcw :size="16" /></button>
          </div>
        </header>
        <div ref="imageFrame" class="anatomy-image-frame" :class="{ 'is-dragging': isDraggingImage }" @pointerdown="startImageDrag" @pointermove="dragImage" @pointerup="stopImageDrag" @pointercancel="stopImageDrag" @pointerleave="stopImageDrag">
          <button class="anatomy-image-stage" :style="practiceStageStyle" type="button" :disabled="!covered" :aria-label="covered ? '在二维解剖图中定位' + practiceTarget?.label : '当前任务没有可用靶区'" @click="locate">
            <img :src="practiceImageUrl" alt="二维器官与精细结构定位训练图" @load="syncPracticeImageAspect" />
            <span v-if="point" class="student-marker" :class="{ correct: result?.correct, wrong: result && !result.correct }" :style="markerStyle"><Crosshair :size="24" /></span>
            <span v-if="result && covered" class="standard-zone" :style="zoneStyle"><span>标准区域</span></span>
          </button>
        </div>
        <footer class="anatomy-stage-note"><span><Target :size="16" />目标：{{ practiceTarget?.label || active.target }}</span><small>{{ practiceCitation }}</small></footer>
      </div>

      <aside class="anatomy-task-panel">
        <section class="practice-task-overview">
          <nav class="practice-detail-nav" aria-label="定位任务资料">
            <button type="button" :aria-pressed="practiceInfoTab === 'structure'" @click="practiceInfoTab = 'structure'"><BookOpenCheck :size="15" />结构信息</button>
            <RouterLink :to="{ path: '/knowledge-graph', query: { q: activeStructure?.name || active.target } }"><Network :size="15" />相关图谱</RouterLink>
            <button type="button" :aria-pressed="practiceInfoTab === 'clinical'" @click="practiceInfoTab = 'clinical'"><Activity :size="15" />临床关联</button>
          </nav>
          <div class="anatomy-task-status"><span>{{ active.system }}</span><b>{{ result ? '已评判' : point ? '已标记' : '待定位' }}</b></div>
          <h2>{{ practiceTarget?.node.title || active.title }}</h2>
          <p v-if="practiceInfoTab === 'structure'" class="anatomy-prompt">{{ practicePrompt }}</p>
          <p v-else class="anatomy-prompt">{{ result?.clinical_link || activeStructure?.clinical_note || active.clinical_link || '当前任务暂无临床关联说明。' }}</p>
        </section>
        <section v-if="practiceInfoTab === 'structure' && active.substructures?.length" class="anatomy-structure-panel">
          <header><strong><Layers3 :size="17" />{{ active.organ || active.target }}精细结构</strong><small>{{ active.substructures.length }} 项</small></header>
          <div class="anatomy-structure-tabs">
            <button v-for="structure in active.substructures" :key="structure.name" type="button" :class="{ active: activeStructure?.name === structure.name }" :aria-pressed="activeStructure?.name === structure.name" :disabled="loading" @click="choosePracticeStructure(structure.name)">{{ structure.name }}</button>
          </div>
          <article v-if="activeStructure">
            <span>{{ activeStructure.category }}</span><strong>{{ activeStructure.name }}</strong><p>{{ activeStructure.description }}</p><small v-if="activeStructure.clinical_note">临床提示：{{ activeStructure.clinical_note }}</small>
          </article>
        </section>
        <div v-if="!result" class="anatomy-instructions">
          <strong><Crosshair :size="17" />操作步骤</strong>
          <ol><li><span>1</span>观察器官相对位置</li><li><span>2</span>点击判断的中心位置</li><li><span>3</span>提交并查看临床关联</li></ol>
          <p v-if="message" class="anatomy-message" :class="{ 'has-point': point }" role="status"><Check v-if="point" :size="16" /><CircleAlert v-else :size="16" />{{ message }}</p>
        </div>
        <div v-else class="anatomy-result" :class="result.correct ? 'is-correct' : 'is-wrong'">
          <header><span><Check v-if="result.correct" :size="20" /><CircleAlert v-else :size="20" /></span><div><small>{{ result.correct ? '定位正确' : '建议重新定位' }}</small><strong>综合得分 {{ score }}</strong></div></header>
          <p>{{ result.feedback }}</p>
          <div class="anatomy-score-list"><div v-for="item in result.score_items" :key="item.name"><span><b>{{ item.name }}</b><strong>{{ item.score }}</strong></span><i><span :style="{ width: item.score + '%' }"></span></i></div></div>
          <section><strong><BookOpenCheck :size="17" />解剖解释</strong><p>{{ result.explanation }}</p></section>
          <section><strong><Activity :size="17" />临床关联</strong><p>{{ result.clinical_link }}</p></section>
        </div>
        <div class="anatomy-actions">
          <button v-if="!result" class="button-primary" type="button" :disabled="loading || !covered" @click="submit"><LoaderCircle v-if="loading" class="spin" :size="18" /><Target v-else :size="18" />{{ loading ? '正在评判' : '提交定位' }}</button>
          <template v-else><button class="button-secondary" type="button" @click="choose(active.id)"><RotateCcw :size="17" />重新练习</button><button class="button-primary" type="button" @click="next">下一题<ArrowRight :size="17" /></button></template>
        </div>
        <details class="anatomy-video-panel">
          <summary><Video :size="17" />B站讲解视频<ChevronDown :size="15" /></summary>
          <template v-if="active.video_resources?.length">
            <a v-for="video in active.video_resources.filter((item) => item.url)" :key="video.title" :href="video.url" target="_blank" rel="noopener noreferrer"><span><b>{{ video.title }}</b><small>{{ video.status }} · {{ video.contributor || '课程组' }}</small></span><ExternalLink :size="16" /></a>
            <p v-if="!active.video_resources.some((item) => item.url)">链接待负责同学收集，并由课程组审核内容与版权后开放。</p>
          </template>
          <p v-else>当前器官暂无已录入视频，链接采集清单可继续补充。</p>
        </details>
      </aside>
    </section>

    <Teleport :to="isBodyFullscreen && bodyWorkbench ? bodyWorkbench : 'body'">
    <div v-if="showTextbook" class="textbook-modal" role="dialog" aria-modal="true" aria-label="教材详解" @click.self="showTextbook = false">
      <div class="textbook-modal-card">
        <header>
          <div><span><BookOpenCheck :size="20" /></span><div><strong>{{ textbook?.query || bodyDisplayName || atlasStructure?.name || '解剖结构' }} · 教材详解</strong><small>基于《系统解剖学》（第10版）本地索引检索</small></div></div>
          <button class="icon-button" type="button" title="关闭" aria-label="关闭教材详解" @click="showTextbook = false"><X :size="18" /></button>
        </header>
        <div class="textbook-modal-body">
          <template v-if="!textbookLoading && textbookEvidence?.found">
            <div v-if="textbookEvidence.answer" class="textbook-evidence-answer">
              <strong>教材优先讲解</strong>
              <MarkdownContent class="textbook-markdown" :content="textbookEvidence.answer" />
              <small>回答来源：{{ textbookEvidence.answer_source }}<template v-if="textbookEvidence.answer_model"> · {{ textbookEvidence.answer_model }}</template></small>
            </div>
            <article v-for="item in textbookEvidence.evidence" :key="`${item.document_id}-${item.page}`" class="textbook-evidence-item">
              <header><strong>{{ item.document_title }}</strong><span>第 {{ item.page }} 页 · 第 {{ item.line_start }}-{{ item.line_end }} 行 · 相似度 {{ Math.round(item.score * 100) }}%</span></header>
              <div class="textbook-evidence-grid">
                <TextbookPageViewer
                  :image-url="item.page_image_url"
                  :alt="`${item.document_title} 第 ${item.page} 页`"
                  :annotations="textbookNoteFor(item).annotations"
                  @update:annotations="updateTextbookAnnotations(item, $event)"
                />
                <div class="textbook-study-side">
                  <div class="textbook-evidence-lines"><p v-for="line in item.lines" :key="line.line" :class="{ matched: line.matched }"><b>{{ line.line }}</b><mark v-if="line.matched">{{ line.text }}</mark><template v-else>{{ line.text }}</template></p></div>
                  <label class="textbook-note-editor"><span>我的笔记</span><textarea v-model="textbookNoteFor(item).content" rows="5" placeholder="记录这页教材的理解、疑问或老师补充" @input="saveTextbookNote(item)" /><small>{{ textbookNoteFor(item).saving ? '正在保存...' : '笔记与勾画自动保存到当前账号' }}</small></label>
                </div>
              </div>
            </article>
          </template>
          <div v-if="textbookLoading" class="textbook-state"><LoaderCircle class="spin" :size="24" />正在检索教材</div>
          <template v-else-if="textbook?.found">
            <p class="textbook-citation">{{ textbook.citation }}</p>
            <h2>{{ textbook.title }}</h2>
            <MarkdownContent v-if="textbook.content" class="textbook-content" :content="textbook.content" />
          </template>
          <div v-else class="textbook-state empty"><BookOpenCheck :size="24" /><strong>暂未找到详细讲解</strong><p>{{ textbook?.hint || '可查看相关知识图谱或在教材中进一步检索。' }}</p></div>
        </div>
      </div>
    </div>
    </Teleport>
  </div>
</template>

<style scoped>
.anatomy-page {
  --lab-ink: #10244e;
  --lab-muted: #455c81;
  --lab-blue: #165def;
  --lab-panel: linear-gradient(145deg, #f9fbff, #ecf3ff);
  --lab-line: #dce8fb;
  color: var(--lab-ink);
}
.lab-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(245px, .7fr);
  align-items: center;
  position: relative;
  isolation: isolate;
  gap: 14px;
  min-height: 120px;
  margin-bottom: 10px;
  padding: 14px clamp(13px, 1.5vw, 24px);
  overflow: hidden;
  border: 1px solid #f0f6ff;
  border-radius: 17px;
  background: linear-gradient(110deg, #e4efff, #c5dffc 64%, #b7d4f6);
}
.lab-hero::before {
  position: absolute;
  z-index: -1;
  inset: 0 18% 0 32%;
  background: url('../assets/medical/dashboard-anatomy-hero.png') right top / cover no-repeat;
  mask-image: linear-gradient(90deg, transparent, #000 48%, #000 74%, transparent);
  content: '';
}
.lab-hero h1 { margin: 3px 0 5px; font-size: clamp(24px, 2.6vw, 39px); line-height: 1.16; }
.lab-hero p { max-width: 570px; margin: 0; color: var(--lab-muted); font-size: 13px; }
.lab-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  padding: 9px 7px;
  border: 1px solid #ffffffc7;
  border-radius: 13px;
  background: #f5f9ffd9;
  text-align: center;
}
.lab-summary span { display: grid; justify-items: center; gap: 1px; }
.lab-summary span + span { border-left: 1px solid #d9e8ff; }
.lab-summary svg { width: 19px; height: 19px; color: var(--lab-blue); }
.lab-summary strong { font-size: clamp(19px, 2vw, 26px); line-height: 1.25; }
.lab-summary small { color: var(--lab-muted); font-size: 11px; }

.anatomy-page .anatomy-mode-switch { gap: 8px; margin-bottom: 12px; }
.anatomy-page .anatomy-mode-switch button {
  min-width: min(30%, 215px);
  min-height: 56px;
  border-color: #f6f9ff;
  border-radius: 11px;
  background: var(--lab-panel);
  color: var(--lab-blue);
  box-shadow: 0 4px 12px #2559a71a;
}
.anatomy-page .anatomy-mode-switch button strong { color: var(--lab-ink); }
.anatomy-page .anatomy-mode-switch button small { color: var(--lab-muted); }
.anatomy-page .anatomy-mode-switch button.active { border-color: #76aaff; background: var(--ui-primary); color: #fff; box-shadow: 0 5px 12px #1558eb40; }
.anatomy-page .anatomy-mode-switch button.active :is(strong, small) { color: #fff; }

.anatomy-page .anatomy-body-workbench {
  grid-template-columns: minmax(158px, .85fr) minmax(0, 2.3fr) minmax(235px, 1.1fr);
  gap: 11px;
  height: clamp(515px, calc(100dvh - 240px), 820px);
  overflow: visible;
  background: transparent;
  box-shadow: none;
}
.anatomy-page .anatomy-body-workbench:fullscreen {
  height: 100dvh;
  padding: 10px;
  background: #e7f0ff;
}
.body-system-rail, .body-detail-panel {
  border: 1px solid #fff;
  border-radius: 14px;
  background: var(--lab-panel);
  box-shadow: 0 4px 16px #153b741a;
}
.body-system-rail > header { min-height: 39px; padding: 0 10px; border-color: var(--lab-line); }
.body-system-rail > header span { color: var(--lab-ink); }
.body-system-rail > header svg { color: var(--lab-blue); }
.body-system-rail > header small { color: var(--lab-muted); white-space: nowrap; }
.body-system-list { gap: 2px; padding: 5px 7px; }
.body-system-row { background: transparent; border-radius: 9px; }
.body-system-row.active { border-color: #b1d0ff; background: #deebff; }
.body-system-focus { grid-template-columns: 29px minmax(0,1fr); align-items: center; gap: 7px; padding: 4px 2px 4px 5px; }
.body-system-focus:hover { background: #e3eeff; }
.body-system-focus strong, .body-system-row.active .body-system-focus strong { color: var(--lab-ink); }
.body-system-focus small, .body-system-row.active .body-system-focus small { color: var(--lab-muted); }
.body-system-eye { width: 29px; color: #466792; border-color: transparent; }
.body-system-eye:hover { color: var(--lab-blue); background: #e3eeff; }
.body-attribution { margin: 0; padding: 7px 9px; color: var(--lab-muted); font-size: 10px; }

.body-stage {
  isolation: isolate;
  position: relative;
  overflow: hidden;
  border: 1px solid #37649e;
  border-radius: 15px;
  background: radial-gradient(ellipse at 50% 96%, #1154a4, #0b244d 49%, #081630 86%);
  box-shadow: 0 6px 20px #142e5e40;
}
.lab-stage-bar {
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 5px;
  padding: 8px;
  background: #091933;
}
.lab-stage-modes, .lab-stage-controls { display: flex; align-items: center; gap: 4px; }
.lab-stage-modes > *, .lab-stage-controls button {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: 0;
  border-radius: 6px;
  background: #21395b;
  color: #e7f1ff;
  font-size: 11px;
}
.lab-stage-modes > * { padding: 0 7px; }
.lab-stage-modes > span { background: #1759dc; font-weight: 750; }
.lab-stage-controls button { width: 28px; }
.lab-stage-controls button:hover, .lab-stage-modes button:hover, .lab-stage-controls [aria-pressed="true"] { background: #295cb4; }
.body-stage :deep(.anatomy-3d) { background: transparent; }
.body-stage :deep(.anatomy-3d::before) {
  position: absolute;
  z-index: -1;
  inset: auto 10% 9%;
  height: 12%;
  border: 1px solid #5ba8fc80;
  border-radius: 50%;
  background: radial-gradient(ellipse, #367ee257, #1c60b022 59%, transparent 70%);
  box-shadow: 0 0 20px #1d73db68, inset 0 0 15px #479dff43;
  content: '';
}
.body-stage :deep(.anatomy-3d-overlay) { background: #0c2245; }
.body-stage :deep(.anatomy-3d-bar i) { background: #468fff; }
.body-stage :deep(.anatomy-3d-legend) { background: #091932db; }
.body-stage :deep(.anatomy-3d-legend span) { color: #e1efff; }
.body-stage-note { min-height: 33px; flex-wrap: wrap; gap: 4px 9px; padding: 4px 8px; border-color: #234375; background: #0b1e3d; }
.body-stage-note span, .body-stage-note small { color: #d5e5ff; font-size: 10px; }
.body-stage-note small { margin-left: auto; }
.body-stage-note svg { width: 12px; height: 12px; }

.body-detail-panel { gap: 8px; padding: 0; border: 0; background: transparent; box-shadow: none; }
.body-detail-panel > * {
  flex: 0 0 auto;
  min-width: 0;
  padding: 11px;
  border: 1px solid #fff;
  border-radius: 13px;
  background: var(--lab-panel);
  box-shadow: 0 3px 12px #17396813;
}
.body-detail-panel :is(.lab-detail-overview, .lab-quick, .lab-progress) h2 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 8px;
  color: var(--lab-ink);
  font-size: 14px;
  line-height: 1.2;
}
.body-detail-panel h2 svg { flex: 0 0 auto; color: var(--lab-blue); }
.body-detail-panel .lab-detail-overview {
  background: linear-gradient(90deg, #f4f8fff7 42%, #e5efffbb), url('../assets/medical/dashboard-anatomy-hero.png') right top / auto 150% no-repeat, #eaf3ff;
}
.lab-detail-overview > strong { display: block; font-size: 17px; overflow-wrap: anywhere; }
.lab-detail-overview p { margin: 5px 0 0; color: var(--lab-muted); font-size: 12px; line-height: 1.55; }
.lab-quick-actions { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 5px; }
.lab-quick-actions button {
  display: grid;
  min-height: 53px;
  place-content: center;
  justify-items: center;
  gap: 3px;
  padding: 3px;
  border: 1px solid #e2ecfd;
  border-radius: 9px;
  background: #e5eeff;
  color: var(--lab-ink);
  font-size: 11px;
  font-weight: 700;
}
.lab-quick-actions button svg { color: var(--lab-blue); }
.lab-quick-actions button:hover, .lab-quick-actions button[aria-expanded="true"] { border-color: #91b7ff; background: #d9e7ff; }
.lab-structure-search { display: grid; gap: 5px; margin-top: 8px; }
.lab-structure-search input { width: 100%; min-width: 0; padding: 6px 8px; border: 1px solid #bbd1f0; border-radius: 7px; background: #fff; color: var(--lab-ink); font-size: 12px; }
.lab-structure-results { display: grid; gap: 3px; max-height: 170px; overflow: auto; }
.lab-structure-results button { display: flex; justify-content: space-between; gap: 6px; padding: 5px; border: 0; border-radius: 5px; background: #f9fbff; color: var(--lab-ink); text-align: left; }
.lab-progress div { display: flex; justify-content: space-between; gap: 6px; color: var(--lab-muted); font-size: 12px; }
.lab-progress progress { display: block; width: 100%; height: 8px; margin: 5px 0; accent-color: var(--lab-blue); }
.lab-progress > small { color: var(--lab-muted); font-size: 11px; }
.lab-progress strong { color: #1646c5; }

@media (max-width: 1050px) {
  .anatomy-page .anatomy-body-workbench { grid-template-columns: minmax(155px, .75fr) minmax(0, 2fr); grid-template-rows: auto auto; height: auto; }
  .body-stage { min-height: 500px; }
  .body-system-rail { max-height: 500px; }
  .body-detail-panel { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); overflow: visible; align-items: start; }
  .body-detail-panel > :not(.lab-detail-overview, .lab-quick, .lab-progress) { grid-column: 1 / -1; }
  .anatomy-page .anatomy-body-workbench:fullscreen { overflow: auto; }
}
@media (max-width: 620px) {
  .lab-hero { grid-template-columns: minmax(0,1fr); gap: 9px; }
  .lab-hero::before { inset: 0 0 32% 28%; opacity: .64; }
  .anatomy-page .anatomy-mode-switch button { min-width: 145px; flex: 0 0 145px; }
  .anatomy-page .anatomy-body-workbench { grid-template-columns: minmax(0,1fr); }
  .body-system-rail { max-height: 206px; }
  .body-stage { min-height: 460px; }
  .body-detail-panel { grid-template-columns: 1fr; }
}

.is-atlas-mode .lab-hero { grid-template-columns: minmax(0, 1fr); min-height: 110px; }
.is-atlas-mode .lab-hero::before { inset: 0 0 0 39%; background-position: right 65%; mask-image: linear-gradient(90deg, transparent, #000 48%, #000 88%, transparent); }
.is-atlas-mode .anatomy-mode-switch { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.is-atlas-mode .anatomy-mode-switch button { min-width: 0; min-height: 61px; padding-inline: clamp(10px, 2vw, 27px); gap: 11px; }
.is-atlas-mode .anatomy-mode-switch button strong { font-size: 15px; }
.is-atlas-mode .anatomy-mode-switch button > svg { flex: 0 0 auto; width: 23px; height: 23px; }
.is-atlas-mode .anatomy-system-tabs {
  gap: 4px;
  margin: 0 0 13px;
  padding: 5px;
  border: 1px solid #f9fbff;
  border-radius: 12px;
  background: #edf4ff;
}
.is-atlas-mode .anatomy-system-tabs button {
  flex: 1 0 auto;
  justify-content: center;
  min-height: 38px;
  padding: 0 9px;
  color: #355479;
  font-size: 13px;
}
.is-atlas-mode .anatomy-system-tabs button.active { background: #fff; color: #0f55e5; box-shadow: 0 3px 12px #275eb52b; }

.is-atlas-mode .anatomy-atlas-workbench {
  display: grid;
  grid-template-columns: minmax(177px, .9fr) minmax(0, 2.05fr) minmax(220px, 1.12fr);
  grid-template-rows: auto auto;
  align-items: stretch;
  gap: 12px;
  height: auto;
  min-height: 0;
  overflow: visible;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.is-atlas-mode .anatomy-atlas-workbench.nav-collapsed { grid-template-columns: 46px minmax(0, 2.05fr) minmax(220px, 1.12fr); }
.is-atlas-mode :is(.atlas-layer-nav, .atlas-image-lab, .atlas-detail-panel, .atlas-study-strip) {
  min-width: 0;
  border: 1px solid #fff;
  border-radius: 15px;
  background: var(--lab-panel);
  box-shadow: 0 5px 14px #193d8018;
}
.is-atlas-mode .atlas-layer-nav { grid-column: auto; display: flex; min-height: 0; overflow: hidden; }
.is-atlas-mode .atlas-layer-nav > header { flex-wrap: wrap; gap: 4px; min-height: 49px; padding: 6px 9px; border-color: var(--lab-line); }
.is-atlas-mode .atlas-layer-nav > header span { color: var(--lab-ink); font-size: 15px; white-space: nowrap; }
.is-atlas-mode .atlas-layer-nav > header :is(svg, button) { color: var(--lab-blue); }
.is-atlas-mode .atlas-layer-nav > header select {
  max-width: 100%;
  min-height: 28px;
  padding: 0 3px;
  border: 1px solid #deebff;
  border-radius: 6px;
  background: #f6faff;
  color: var(--lab-ink);
  font-size: 11px;
}
.is-atlas-mode .atlas-layer-nav > header button { width: 25px; height: 28px; background: #e7f0ff; }
.is-atlas-mode .nav-collapsed .atlas-layer-nav > header { justify-content: center; }
.is-atlas-mode .nav-collapsed .atlas-layer-nav select { display: none; }
.is-atlas-mode .atlas-layer-tree { display: grid; align-content: start; gap: 3px; max-height: 626px; }
.is-atlas-mode .atlas-layer-tree button { min-height: 47px; padding: 5px 6px; border-radius: 9px; color: #506a8f; }
.is-atlas-mode .atlas-layer-tree button:hover { background: #e9f2ff; }
.is-atlas-mode .atlas-layer-tree button.active { border-color: #c0d9ff; background: #dcecff; color: var(--lab-blue); }
.is-atlas-mode .atlas-layer-tree button strong { color: var(--lab-ink); font-size: 12px; }
.is-atlas-mode .atlas-layer-tree button small { color: var(--lab-muted); }
.is-atlas-mode .nav-collapsed .atlas-layer-tree { display: none; }

.is-atlas-mode .atlas-image-lab { grid-template-rows: auto auto minmax(0, 1fr) auto; min-height: 0; padding: 8px; gap: 8px; }
.is-atlas-mode .atlas-image-lab > header { flex-direction: row; align-items: center; justify-content: space-between; flex-wrap: wrap; min-height: 34px; gap: 5px; padding: 0 4px; border: 0; background: transparent; }
.is-atlas-mode .atlas-breadcrumb { flex-wrap: wrap; color: var(--lab-muted); }
.is-atlas-mode .atlas-breadcrumb :is(button, strong) { color: var(--lab-ink); white-space: normal; }
.is-atlas-mode .atlas-breadcrumb button:hover { color: var(--lab-blue); }
.atlas-level-chip { padding: 5px 8px; border: 1px solid #dae8fd; border-radius: 8px; background: #e7f1ff; color: #38577c; font-size: 11px; white-space: nowrap; }
.atlas-image-instruction {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 36px;
  margin: 0;
  padding: 6px 9px;
  border: 1px solid #fff;
  border-radius: 10px;
  background: #e3edfd;
  color: #304d74;
  font-size: 12px;
  text-align: center;
}
.atlas-image-instruction svg { flex: 0 0 auto; color: var(--lab-blue); }
.is-atlas-mode .atlas-image-canvas {
  min-height: 0;
  overflow: visible;
  padding: clamp(8px, 1.2vw, 17px);
  border: 1px solid #dbe8fb;
  border-radius: 13px;
  background: #fbfdff;
}
.is-atlas-mode .atlas-image-stage { width: 100%; height: auto; background: transparent; box-shadow: none; }
.is-atlas-mode .atlas-image-stage > img { position: absolute; inset: 0; object-fit: fill; }
.is-atlas-mode .atlas-hotspot > span { background: #165def; box-shadow: 0 2px 8px #1a62e85c; }
.is-atlas-mode .atlas-hotspot:is(:hover, .selected, :focus-visible) > span { background: #0841a5; outline: 2px solid #94c1ff; }
.is-atlas-mode .atlas-hotspot > span > b { max-width: min(165px, 35vw); color: #234774; white-space: normal; text-align: center; }
.is-atlas-mode .atlas-image-lab > footer { min-height: 28px; padding: 2px 4px; border: 0; background: transparent; }
.is-atlas-mode .atlas-image-lab > footer :is(span, small) { color: var(--lab-muted); }
.is-atlas-mode .atlas-image-lab > footer span { flex: 0 0 auto; }
.is-atlas-mode .atlas-image-lab > footer small { display: block; overflow-wrap: anywhere; }

.is-atlas-mode .atlas-detail-panel { padding: clamp(11px, 1.3vw, 17px); max-height: 680px; }
.is-atlas-mode .atlas-detail-panel > * { flex: 0 0 auto; }
.is-atlas-mode .atlas-detail-title { display: flex; align-items: center; gap: 8px; margin: 0 0 8px; color: var(--lab-ink); font-size: clamp(16px, 1.4vw, 22px); }
.atlas-detail-title svg { flex: 0 0 auto; }
.is-atlas-mode .atlas-detail-panel > p { color: var(--lab-muted); }
.is-atlas-mode .atlas-drilldown-list { margin-bottom: 9px; }
.is-atlas-mode .atlas-drilldown-list button {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) 16px;
  align-items: center;
  gap: 7px;
  width: 100%;
  min-height: 43px;
  padding: 5px 7px;
  border: 1px solid #d6e6fc;
  border-radius: 9px;
  background: #eef5ff;
  color: var(--lab-blue);
  text-align: left;
}
.is-atlas-mode .atlas-drilldown-list button:hover { border-color: #8fb7ff; background: #e1eeff; }
.is-atlas-mode .atlas-drilldown-list button b { color: var(--lab-ink); font-size: 12px; }
.is-atlas-mode .atlas-drilldown-list button small { color: var(--lab-muted); }
.is-atlas-mode .atlas-drilldown-list .atlas-drilldown-icon { display: grid; width: 30px; aspect-ratio: 1; place-items: center; border-radius: 9px; background: #e3eeff; }
.is-atlas-mode .atlas-empty-detail { padding: 18px 6px; border-top-color: #dbe7fb; color: var(--lab-muted); }
.is-atlas-mode .atlas-empty-detail svg, .is-atlas-mode .atlas-graph-link { color: var(--lab-blue); }
.is-atlas-mode .atlas-empty-detail strong { color: var(--lab-ink); }
.is-atlas-mode .atlas-graph-link { font-size: 13px; }

.atlas-study-strip { grid-column: 1 / -1; padding: 6px; }
.atlas-study-summary { display: grid; grid-template-columns: minmax(0, 1.5fr) auto auto minmax(0, 1.12fr); gap: 6px; }
.atlas-study-summary > :is(div, button) {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 5px;
  padding: 7px 8px;
  border-radius: 8px;
  background: #f7faff;
  color: var(--lab-ink);
  text-align: left;
}
.atlas-study-summary strong { flex: 0 0 auto; font-size: 11px; color: var(--lab-ink); }
.atlas-study-summary small { color: var(--lab-muted); font-size: 10px; white-space: normal; }
.atlas-study-summary svg { flex: 0 0 auto; color: var(--lab-blue); }
.atlas-study-summary button { justify-content: flex-start; }
.atlas-study-summary button:hover { background: #e5efff; }
.atlas-study-summary button > svg:last-child { margin-left: auto; }
.atlas-study-strip .atlas-resource-content { padding: 5px; }
.atlas-study-strip .atlas-resource-tabs { max-width: 300px; }

@media (max-width: 1120px) {
  .atlas-study-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 960px) {
  .is-atlas-mode :is(.anatomy-atlas-workbench, .anatomy-atlas-workbench.nav-collapsed) { grid-template-columns: minmax(0, 1.75fr) minmax(200px, 1fr); }
  .is-atlas-mode .atlas-layer-nav { grid-column: 1 / -1; }
  .is-atlas-mode .atlas-layer-tree { display: flex; overflow-x: auto; }
  .is-atlas-mode .atlas-layer-tree button { flex: 0 0 164px; }
  .is-atlas-mode .atlas-detail-panel { max-height: none; }
}
@media (max-width: 700px) {
  .is-atlas-mode :is(.anatomy-atlas-workbench, .anatomy-atlas-workbench.nav-collapsed) { grid-template-columns: minmax(0, 1fr); }
  .is-atlas-mode .atlas-layer-nav { order: 0; }
  .is-atlas-mode .atlas-image-lab { order: 1; }
  .is-atlas-mode .atlas-detail-panel { order: 2; min-height: 0; }
  .atlas-study-strip { order: 3; }
}
@media (max-width: 500px) {
  .is-atlas-mode .anatomy-mode-switch { gap: 5px; }
  .is-atlas-mode .anatomy-mode-switch button { justify-content: center; gap: 4px; padding-inline: 3px; }
  .is-atlas-mode .anatomy-mode-switch button > svg { width: 15px; height: 15px; }
  .is-atlas-mode .anatomy-mode-switch button strong { font-size: 11px; }
  .is-atlas-mode .anatomy-mode-switch button small { display: none; }
  .is-atlas-mode .lab-hero::before { opacity: .6; }
  .atlas-study-summary { grid-template-columns: 1fr; }
}


.is-practice-mode .anatomy-mode-switch { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); max-width: 970px; gap: 10px; }
.is-practice-mode .anatomy-mode-switch button { min-width: 0; min-height: 57px; }
.is-practice-mode .anatomy-mode-switch button > svg { flex: 0 0 auto; width: 22px; height: 22px; }
.is-practice-mode .anatomy-system-tabs {
  width: fit-content;
  max-width: 100%;
  padding: 5px;
  gap: 5px;
  border: 1px solid #f8fbff;
  border-radius: 12px;
  background: #eaf2ff;
}
.is-practice-mode .anatomy-system-tabs button { min-height: 36px; color: #355479; font-size: 13px; }
.is-practice-mode .anatomy-system-tabs button.active { color: #0f55e5; box-shadow: 0 3px 12px #275eb52b; }

.is-practice-mode .anatomy-workbench {
  display: grid;
  grid-template-columns: minmax(158px, .76fr) minmax(0, 2.35fr) minmax(252px, 1.2fr);
  grid-template-rows: minmax(0, 1fr);
  gap: 10px;
  height: clamp(550px, calc(100dvh - 305px), 760px);
  overflow: visible;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.is-practice-mode .anatomy-exercise-rail {
  display: flex;
  grid-column: auto;
  border: 1px solid #fff;
  border-radius: 15px;
  background: var(--lab-panel);
  box-shadow: 0 5px 14px #193d8018;
}
.is-practice-mode .anatomy-exercise-rail > header { min-height: 48px; padding: 0 12px; border-color: var(--lab-line); }
.is-practice-mode .anatomy-exercise-rail > header span { color: var(--lab-ink); }
.is-practice-mode .anatomy-exercise-rail > header small { color: var(--lab-muted); white-space: nowrap; }
.is-practice-mode .anatomy-exercise-rail > header svg { color: var(--lab-blue); }
.is-practice-mode .anatomy-exercise-list { display: grid; align-content: start; gap: 5px; padding: 7px; }
.is-practice-mode .anatomy-exercise-list button {
  grid-template-columns: 29px minmax(0, 1fr) 15px;
  gap: 6px;
  min-height: 51px;
  padding: 5px 6px;
  border: 1px solid #e3ecfc;
  border-radius: 10px;
  background: #f4f8ff;
  color: #2c548a;
}
.is-practice-mode .anatomy-exercise-list button:hover { background: #e3eeff; }
.is-practice-mode .anatomy-exercise-list button.active { border-color: #a4c6ff; background: #dce9ff; color: var(--lab-blue); box-shadow: none; }
.is-practice-mode .anatomy-exercise-list button > span:first-child { color: #2158b8; }
.is-practice-mode .anatomy-exercise-list strong { color: var(--lab-ink); font-size: 13px; }
.is-practice-mode .anatomy-exercise-list small { color: var(--lab-muted); font-size: 10px; }

.is-practice-mode .anatomy-visual-lab {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 0;
  overflow: hidden;
  border: 1px solid #426da4;
  border-radius: 16px;
  background: #0b2248;
  box-shadow: 0 6px 18px #142e5e32;
}
.is-practice-mode .anatomy-visual-lab:fullscreen { width: 100%; height: 100%; border-radius: 0; }
.is-practice-mode .anatomy-lab-toolbar {
  flex-wrap: wrap;
  gap: 6px 10px;
  min-height: 48px;
  padding: 7px 10px;
  border: 0;
  background: linear-gradient(110deg, #153668, #0b2248);
}
.is-practice-mode .anatomy-lab-toolbar > div { min-width: 0; gap: 5px; color: #d5e8ff; }
.is-practice-mode .anatomy-lab-toolbar > div > svg { flex: 0 0 auto; }
.is-practice-mode .anatomy-lab-toolbar strong { color: #fff; font-size: 13px; overflow-wrap: anywhere; }
.is-practice-mode .anatomy-lab-toolbar small { color: #c5d9f7; font-size: 10px; }
.practice-view-controls { margin-left: auto; }
.practice-view-controls button {
  display: grid;
  width: 29px;
  height: 29px;
  place-items: center;
  padding: 0;
  border: 1px solid #ffffff1c;
  border-radius: 7px;
  background: #264978;
  color: #edf5ff;
}
.practice-view-controls button:hover:not(:disabled) { background: #3566a7; }
.practice-view-controls button:disabled { opacity: .5; }
.is-practice-mode .anatomy-image-frame {
  display: flex;
  container-type: size;
  min-width: 0;
  overflow: auto;
  padding: 10px;
  background: #fff;
  cursor: auto;
  touch-action: pan-x pan-y;
}
.is-practice-mode .anatomy-image-frame.is-dragging { cursor: grabbing; }
.is-practice-mode .anatomy-image-stage {
  flex: 0 0 auto;
  min-width: 0;
  margin: auto;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
}
.is-practice-mode .anatomy-image-stage:disabled { opacity: 1; }
.is-practice-mode .anatomy-stage-note {
  flex-wrap: wrap;
  gap: 4px 9px;
  min-height: 35px;
  padding: 5px 10px;
  border-color: #274977;
  background: #102b53;
  color: #e6efff;
  font-size: 11px;
}
.is-practice-mode .anatomy-stage-note small { color: #bed2f0; overflow-wrap: anywhere; }

.is-practice-mode .anatomy-task-panel { gap: 7px; padding: 0; border: 0; background: transparent; }
.is-practice-mode .anatomy-task-panel > * {
  flex: 0 0 auto;
  min-width: 0;
  margin: 0;
  padding: 10px;
  border: 1px solid #fff;
  border-radius: 13px;
  background: var(--lab-panel);
}
.practice-detail-nav { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; margin-bottom: 9px; }
.practice-detail-nav > * {
  display: flex;
  min-height: 32px;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 3px;
  border: 1px solid #e3edfc;
  border-radius: 8px;
  background: #edf4ff;
  color: #234579;
  text-decoration: none;
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
}
.practice-detail-nav > * > svg { flex: 0 0 auto; }
.practice-detail-nav > *:hover { border-color: #a1c4ff; }
.practice-detail-nav [aria-pressed="true"] { border-color: #6b9fff; background: var(--ui-primary); color: #fff; }
.is-practice-mode .anatomy-task-status { margin-bottom: 5px; }
.is-practice-mode .anatomy-task-status :is(span,b) { padding: 3px 6px; background: #e5efff; color: #355886; font-size: 10px; }
.is-practice-mode .anatomy-task-panel h2 { margin: 0 0 5px; color: var(--lab-ink); font-size: clamp(16px, 1.4vw, 21px); }
.is-practice-mode .anatomy-prompt { margin: 0; color: var(--lab-muted); font-size: 12px; line-height: 1.6; }
.is-practice-mode :is(.anatomy-structure-panel > header strong, .anatomy-instructions > strong, .anatomy-video-panel summary) { color: var(--lab-ink); font-size: 13px; }
.is-practice-mode .anatomy-task-panel :is(header, summary, .anatomy-instructions > strong) > svg { color: var(--lab-blue); }
.is-practice-mode .anatomy-structure-tabs { flex-wrap: wrap; gap: 4px; margin-top: 7px; }
.is-practice-mode .anatomy-structure-tabs button { min-height: 27px; padding: 0 6px; border-color: #d1e1fa; color: #395780; font-size: 11px; }
.is-practice-mode .anatomy-structure-tabs button.active { border-color: #5891f6; background: #e3edff; color: #0c4cd8; }
.is-practice-mode .anatomy-structure-panel article { padding: 8px; border: 1px solid #d9e7fc; border-radius: 9px; background: #f5f9ff; }
.is-practice-mode .anatomy-structure-panel article > span { background: #e2edff; color: #3f6192; }
.is-practice-mode .anatomy-structure-panel article > strong { color: var(--lab-ink); }
.is-practice-mode .anatomy-instructions ol { gap: 4px; margin-top: 7px; }
.is-practice-mode .anatomy-instructions li { gap: 7px; color: var(--lab-muted); font-size: 12px; }
.is-practice-mode .anatomy-instructions li span { width: 23px; height: 23px; background: #dceaff; color: #1356df; }
.is-practice-mode .anatomy-message { margin-top: 7px; padding: 6px; font-size: 11px; }
.is-practice-mode .anatomy-message.has-point { background: #e5f0ff; color: #244f97; }
.is-practice-mode .anatomy-result { gap: 9px; }
.is-practice-mode .anatomy-actions { gap: 6px; padding: 7px; }
.is-practice-mode .anatomy-video-panel summary { display: flex; align-items: center; gap: 6px; font-weight: 750; cursor: pointer; }
.is-practice-mode .anatomy-video-panel summary svg:last-child { margin-left: auto; }
.is-practice-mode .anatomy-video-panel[open] summary svg:last-child { transform: rotate(180deg); }

@media (max-width: 1050px) {
  .is-practice-mode .anatomy-workbench { grid-template-columns: minmax(0, 1.65fr) minmax(230px, 1fr); grid-template-rows: auto 540px; height: auto; }
  .is-practice-mode .anatomy-exercise-rail { grid-column: 1 / -1; }
  .is-practice-mode .anatomy-exercise-list { display: flex; overflow-x: auto; }
  .is-practice-mode .anatomy-exercise-list button { flex: 0 0 164px; }
}
@media (max-width: 690px) {
  .is-practice-mode .anatomy-workbench { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto auto auto; }
  .is-practice-mode .anatomy-exercise-rail { order: 0; }
  .is-practice-mode .anatomy-visual-lab { order: 1; height: clamp(370px, 100vw, 530px); }
  .is-practice-mode .anatomy-task-panel { order: 2; min-height: 0; overflow: visible; }
  .is-practice-mode .anatomy-mode-switch { gap: 5px; }
  .is-practice-mode .anatomy-mode-switch button { justify-content: center; padding-inline: 3px; gap: 4px; }
  .is-practice-mode .anatomy-mode-switch button > svg { width: 15px; height: 15px; }
  .is-practice-mode .anatomy-mode-switch button strong { font-size: 11px; }
  .is-practice-mode .anatomy-mode-switch button small { display: none; }
}

</style>
