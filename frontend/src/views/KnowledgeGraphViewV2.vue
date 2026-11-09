<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  BarChart3,
  BookOpenCheck,
  BrainCircuit,
  ChevronRight,
  ExternalLink,
  GraduationCap,
  Layers3,
  Link2,
  List,
  LocateFixed,
  Minus,
  Network,
  Orbit,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Search,
  ScanLine
} from '@lucide/vue';
import { getDataSources, getKnowledgeGraph, searchKnowledge } from '../api';
import anatomyModel from '../assets/medical/knowledge-graph-anatomy.webp';
import AnatomyGraphIcon from '../components/AnatomyGraphIcon.vue';
import { mockGraph } from '../data/graph';
import { trainingStore } from '../stores/training';
import type { DataSourceItem, KnowledgeEdge, KnowledgeNode } from '../types';

type GraphViewMode = 'network' | 'mindmap' | 'list';
interface PositionedNode extends KnowledgeNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  depth?: number;
}

const VIEWBOX_WIDTH = 920;
const VIEWBOX_HEIGHT = 620;
const MAX_VISIBLE_NODES = 46;
const MAX_ANCHOR_NODES = 14;
const OVERVIEW_ROOT_ID = 'anatomy_root';
const OVERVIEW_SYSTEM_ORDER = [
  'endocrine', 'digestive', 'reproductive', 'urinary', 'nervous',
  'respiratory', 'locomotor', 'lymphatic', 'circulatory'
].map(id => 'anatomy_system_' + id);
const route = useRoute();
const query = ref(String(route.query.q || ''));
const type = ref(String(route.query.type || '全部类型'));
const graphMode = ref<GraphViewMode>(route.query.view === 'mindmap' || route.query.view === 'list' ? route.query.view : 'network');
const nodes = ref<KnowledgeNode[]>([]);
const edges = ref<KnowledgeEdge[]>([]);
const positionedNodes = ref<PositionedNode[]>([]);
const selected = ref<PositionedNode | null>(null);
const rootNodeId = ref('');
const focusedNodeId = ref('');
const treeParents = ref<Record<string, string>>({});
const evidenceResults = ref<Array<{ kind: string; title: string; summary: string; target: string }>>([]);
const dataSources = ref<DataSourceItem[]>([]);
const activeSource = ref<DataSourceItem | null>(null);
const isMotionPaused = ref(false);
const stageVisible = ref(true);
const zoom = ref(1);
const svgRef = ref<SVGSVGElement | null>(null);
const stageRef = ref<HTMLElement | null>(null);
const canvasScrollRef = ref<HTMLElement | null>(null);
let canvasObserver: ResizeObserver | undefined;
const draggingId = ref<string | null>(null);
let animationFrame = 0;
let previousFrame = 0;
let intersectionObserver: IntersectionObserver | null = null;

const typeLabels: Record<string, string> = {
  AnatomyRoot: '人体解剖',
  AnatomySystem: '人体系统',
  AnatomyOrgan: '器官',
  AnatomyStructure: '精细结构'
};
const sourceFallbacks: Record<string, DataSourceItem> = {
  bodyparts3d: {
    id: 'bodyparts3d',
    name: 'BodyParts3D 4.0',
    platform: 'BodyParts3D',
    type: '三维人体解剖模型',
    modules: ['三维人体', '解剖知识图谱'],
    license: 'CC BY 4.0，使用时保留来源与署名。',
    connected: true,
    index_status: 'local_ready',
    sync_status: 'bundled',
    url: 'https://lifesciencedb.jp/bp3d/',
    mapping: { system: 'anatomy_system', organ: 'curated_organ', structure: 'FMA_part' }
  },
  pmph_undergraduate_textbooks: {
    id: 'pmph_undergraduate_textbooks',
    name: '人民卫生出版社本科临床医学规划教材体系',
    platform: '教材摘要',
    type: '医学教材体系',
    modules: ['教材路径', '知识库', '桥梁课程', '临床核心'],
    license: '仅展示书目与自行整理的摘要，不复制教材原文。',
    connected: true,
    index_status: 'mock_indexed',
    sync_status: 'curated_outline',
    url: 'https://www.pmph.com/',
    mapping: { stage: 'curriculum_stage', book: 'textbook_title', topic: 'learning_objective' }
  }
};

function nodeText(node: KnowledgeNode) {
  return [node.label, node.label_zh, node.label_en, node.summary, node.description_zh, ...(node.aliases_zh ?? [])]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

function nodeGroup(node: KnowledgeNode) {
  return node.group || node.type || 'LearningObjective';
}

function hasAnatomyMedallion(node: KnowledgeNode) {
  const group = nodeGroup(node);
  return group === 'AnatomyRoot' || group === 'AnatomySystem';
}

function networkNodeRadius(node: KnowledgeNode) {
  if (nodeGroup(node) === 'AnatomyRoot') return 35;
  if (nodeGroup(node) === 'AnatomySystem') return 31;
  if (nodeGroup(node) === 'AnatomyOrgan') return 29;
  return selected.value?.id === node.id ? 34 : node.id === rootNodeId.value ? 31 : 27;
}

function branchLabelLines(node: KnowledgeNode) {
  const title = label(node);
  const name = Array.from(title);
  const limit = /\p{Script=Han}/u.test(title) ? 5 : 8;
  const lines = name.length <= limit ? [title] : [
    name.slice(0, limit).join(''),
    name.length > limit * 2 ? name.slice(limit, limit * 2 - 1).join('') + '…' : name.slice(limit).join('')
  ];
  const firstLineY = nodeGroup(node) === 'AnatomyOrgan' ? 10 : lines.length === 1 ? 0 : -5;
  return lines.map((text, index) => ({ text, y: firstLineY + index * 10 }));
}

function nodeDegree(nodeId: string) {
  return edges.value.reduce((total, edge) => total + Number(edge.source === nodeId || edge.target === nodeId), 0);
}

function rankNodes(items: KnowledgeNode[]) {
  return [...items].sort((first, second) => nodeDegree(second.id) - nodeDegree(first.id));
}

function expandNeighborhood(anchors: KnowledgeNode[], depth = 2, limit = MAX_VISIBLE_NODES) {
  const nodeLookup = new Map(nodes.value.map((node) => [node.id, node]));
  const selectedIds = new Set(anchors.map((node) => node.id));
  let frontier = new Set(selectedIds);

  for (let level = 0; level < depth && selectedIds.size < limit; level += 1) {
    const candidates = new Map<string, number>();
    edges.value.forEach((edge) => {
      const sourceActive = frontier.has(edge.source);
      const targetActive = frontier.has(edge.target);
      if (!sourceActive && !targetActive) return;
      const candidateId = sourceActive ? edge.target : edge.source;
      if (selectedIds.has(candidateId) || !nodeLookup.has(candidateId)) return;
      const anchorId = sourceActive ? edge.source : edge.target;
      const crossType = nodeGroup(nodeLookup.get(anchorId)!) !== nodeGroup(nodeLookup.get(candidateId)!);
      const score = (edge.weight ?? 0.5) * 20 + nodeDegree(candidateId) + (crossType ? 8 : 0);
      candidates.set(candidateId, Math.max(candidates.get(candidateId) ?? 0, score));
    });

    const nextFrontier = new Set<string>();
    [...candidates.entries()]
      .sort((first, second) => second[1] - first[1])
      .forEach(([candidateId]) => {
        if (selectedIds.size >= limit) return;
        selectedIds.add(candidateId);
        nextFrontier.add(candidateId);
      });
    frontier = nextFrontier;
    if (!frontier.size) break;
  }

  return [...selectedIds]
    .map((id) => nodeLookup.get(id))
    .filter((node): node is KnowledgeNode => Boolean(node));
}

const isOverview = computed(() => !query.value.trim() && type.value === '全部类型' && !focusedNodeId.value);
const graphGroups = computed(() => Object.entries(typeLabels).map(([key, title]) => ({
  key, title, count: nodes.value.filter(node => nodeGroup(node) === key).length
})));
const systemCount = computed(() => graphGroups.value.find(group => group.key === 'AnatomySystem')?.count ?? 0);
const graphTotals = computed(() => [
  { icon: Network, value: nodes.value.length, label: '节点数' },
  { icon: Link2, value: edges.value.length, label: '关联关系' },
  { icon: Layers3, value: systemCount.value, label: '覆盖系统' }
]);
const maxGroupCount = computed(() => Math.max(1, ...graphGroups.value.map(group => group.count)));
const showAllRelations = ref(false);
const learningSteps = [
  { label: '人体解剖概览', type: '全部类型', icon: BookOpenCheck },
  { label: '系统结构', type: 'AnatomySystem', icon: Layers3 },
  { label: '器官功能', type: 'AnatomyOrgan', icon: Orbit },
  { label: '精细结构', type: 'AnatomyStructure', icon: Network }
];

const sourceNodes = computed<KnowledgeNode[]>(() => {
  const keyword = query.value.trim().toLowerCase();
  if (focusedNodeId.value) {
    const focused = nodes.value.find((node) => node.id === focusedNodeId.value);
    if (focused) return expandNeighborhood([focused], 2, 52);
  }

  if (!keyword && type.value === '全部类型') {
    const root = nodes.value.find((node) => node.id === OVERVIEW_ROOT_ID);
    return root ? expandNeighborhood([root], 1) : nodes.value.slice(0, MAX_VISIBLE_NODES);
  }

  const directMatches = nodes.value.filter((node) => {
    const typeMatch = type.value === '全部类型' || nodeGroup(node) === type.value;
    return typeMatch && (!keyword || nodeText(node).includes(keyword));
  });
  const anchors = rankNodes(directMatches).slice(0, MAX_ANCHOR_NODES);
  if (anchors.length) return expandNeighborhood(anchors, 2);

  const relatedMatches = nodes.value.filter((node) => edges.value.some((edge) => {
    if (edge.source !== node.id && edge.target !== node.id) return false;
    const relatedId = edge.source === node.id ? edge.target : edge.source;
    const related = nodes.value.find((item) => item.id === relatedId);
    return related ? nodeText(related).includes(keyword) : false;
  }));
  return expandNeighborhood(rankNodes(relatedMatches).slice(0, MAX_ANCHOR_NODES), 1);
});

const sourceEdges = computed<KnowledgeEdge[]>(() => {
  const ids = new Set(sourceNodes.value.map((node) => node.id));
  const visible = edges.value.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
  return visible.slice(0, 110);
});

const sourceSignature = computed(() => sourceNodes.value.map((node) => node.id).join('|'));
const visibleIds = computed(() => new Set(positionedNodes.value.map((node) => node.id)));
const nodeMap = computed<Record<string, PositionedNode>>(() => Object.fromEntries(positionedNodes.value.map((node) => [node.id, node])));
const displayEdges = computed(() => {
  const available = sourceEdges.value.filter((edge) => visibleIds.value.has(edge.source) && visibleIds.value.has(edge.target));
  if (graphMode.value !== 'mindmap') return available;
  return available.filter((edge) => treeParents.value[edge.target] === edge.source || treeParents.value[edge.source] === edge.target);
});
const labeledEdges = computed(() => {
  const active = displayEdges.value.filter((edge) => isActiveEdge(edge));
  return active.length ? active.slice(0, 12) : displayEdges.value.filter((edge) => (edge.weight ?? 0) >= 0.9).slice(0, 8);
});
const neighbors = computed(() => {
  const id = selected.value?.id;
  return id ? edges.value.filter(edge => edge.source === id || edge.target === id) : [];
});
const visibleNeighbors = computed(() => showAllRelations.value ? neighbors.value : neighbors.value.slice(0, 4));
const nodeLookup = computed(() => new Map(nodes.value.map(node => [node.id, node])));
const degreeByNode = computed(() => {
  const counts = new Map<string, number>();
  for (const edge of edges.value) {
    counts.set(edge.source, (counts.get(edge.source) ?? 0) + 1);
    counts.set(edge.target, (counts.get(edge.target) ?? 0) + 1);
  }
  return counts;
});
watch(() => selected.value?.id, () => {
  showAllRelations.value = false;
  activeSource.value = null;
}, { flush: 'sync' });
const viewportTransform = computed(() => `translate(${VIEWBOX_WIDTH / 2} ${VIEWBOX_HEIGHT / 2}) scale(${zoom.value}) translate(${-VIEWBOX_WIDTH / 2} ${-VIEWBOX_HEIGHT / 2})`);
const graphStatus = computed(() => `${graphMode.value === 'mindmap' ? '层级脑图' : isOverview.value ? '系统总览' : isMotionPaused.value ? '动态已暂停' : '力导向运行中'} · ${sourceNodes.value.length} 节点 / ${displayEdges.value.length} 关系`);

onMounted(async () => {
  alignCanvas();
  if (canvasScrollRef.value && 'ResizeObserver' in window) {
    canvasObserver = new ResizeObserver(alignCanvas);
    canvasObserver.observe(canvasScrollRef.value);
  }
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) isMotionPaused.value = true;
  try {
    const graph = await getKnowledgeGraph('zh', 'anatomy');
    nodes.value = graph.nodes;
    edges.value = graph.edges;
  } catch {
    nodes.value = mockGraph.nodes as unknown as KnowledgeNode[];
    edges.value = mockGraph.edges as unknown as KnowledgeEdge[];
  }
  try {
    dataSources.value = await getDataSources();
  } catch {
    dataSources.value = Object.values(sourceFallbacks);
  }
  resetLayout();
  if (route.query.source) activeSource.value = sourceDetail(String(route.query.source));
  if (query.value.trim()) await retrieveEvidence();

  if (stageRef.value && 'IntersectionObserver' in window) {
    intersectionObserver = new IntersectionObserver(([entry]) => { stageVisible.value = entry.isIntersecting; }, { threshold: 0.08 });
    intersectionObserver.observe(stageRef.value);
  }
  animationFrame = requestAnimationFrame(simulate);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationFrame);
  intersectionObserver?.disconnect();
  canvasObserver?.disconnect();
});

watch(() => route.query.q, async (value) => {
  query.value = value ? String(value) : '';
  if (query.value.trim()) await retrieveEvidence();
});
watch(sourceSignature, () => resetLayout());
watch(graphMode, () => {
  resetLayout();
  alignCanvas();
});
watch([query, type], () => { focusedNodeId.value = ''; });

function alignCanvas() {
  const canvas = canvasScrollRef.value;
  if (!canvas) return;
  canvas.scrollLeft = graphMode.value === 'network' ? (canvas.scrollWidth - canvas.clientWidth) / 2 : 0;
}

function retrieveEvidence() {
  if (!query.value.trim()) {
    evidenceResults.value = [];
    return Promise.resolve();
  }
  return searchKnowledge(query.value)
    .then((result) => { evidenceResults.value = result.items.slice(0, 4); })
    .catch(() => {
      evidenceResults.value = [{
        kind: '教学知识索引（Mock）',
        title: `“${query.value}”相关证据待接入`,
        summary: '当前离线模式未返回可追溯原文，需接入合法知识来源并由教师审核。',
        target: 'mock-evidence'
      }];
    });
}

function sourceDetail(sourceId: string) {
  return dataSources.value.find((source) => source.id === sourceId) ?? sourceFallbacks[sourceId] ?? {
    id: sourceId,
    name: sourceId,
    platform: '教学知识库',
    type: '来源元数据',
    modules: ['知识图谱'],
    license: '来源说明待教师审核。',
    connected: false,
    index_status: 'metadata_only',
    sync_status: 'pending_review',
    url: '',
    mapping: {}
  };
}

function sourceName(sourceId: string) {
  return sourceDetail(sourceId).name;
}

function openSource(sourceId: string) {
  activeSource.value = sourceDetail(sourceId);
}

function label(node?: KnowledgeNode | null) {
  return node?.label_zh || node?.label || node?.id || '知识节点';
}

function groupLabel(node?: KnowledgeNode | null) {
  return typeLabels[node?.group || node?.type || ''] || '医学知识';
}

function relatedNode(edge: KnowledgeEdge) {
  const id = edge.source === selected.value?.id ? edge.target : edge.source;
  return nodeMap.value[id] ?? nodeLookup.value.get(id);
}

function selectRelated(edge: KnowledgeEdge) {
  const node = relatedNode(edge);
  if (!node) return;
  if (nodeMap.value[node.id]) selectNode(nodeMap.value[node.id]);
  else {
    focusedNodeId.value = node.id;
    rootNodeId.value = node.id;
    zoom.value = 1;
    resetLayout();
  }
}

function chooseLearningStep(step: string) {
  query.value = '';
  evidenceResults.value = [];
  type.value = step;
  clearFocus();
  stageRef.value?.scrollIntoView({ block: 'nearest' });
}

function deterministicOffset(id: string) {
  let hash = 0;
  for (let index = 0; index < id.length; index += 1) hash = (hash * 31 + id.charCodeAt(index)) >>> 0;
  return (hash % 1000) / 1000;
}

function networkLayout(source: KnowledgeNode[]) {
  const preferredRoot = source.some((node) => node.id === rootNodeId.value)
    ? rootNodeId.value
    : source.some((node) => node.id === OVERVIEW_ROOT_ID)
      ? OVERVIEW_ROOT_ID
      : selected.value?.id || source[0]?.id || '';
  rootNodeId.value = preferredRoot;
  if (isOverview.value && preferredRoot === OVERVIEW_ROOT_ID) {
    const root = source.find(node => node.id === preferredRoot)!;
    const systems = source.filter(node => node.id !== preferredRoot);
    const ordered = [
      ...OVERVIEW_SYSTEM_ORDER.flatMap(id => systems.filter(node => node.id === id)),
      ...systems.filter(node => !OVERVIEW_SYSTEM_ORDER.includes(node.id))
    ];
    return [
      { ...root, x: VIEWBOX_WIDTH / 2, y: 255, vx: 0, vy: 0 },
      ...ordered.map((node, index) => {
        const angle = index / ordered.length * 2 * Math.PI - Math.PI / 2;
        return { ...node, x: VIEWBOX_WIDTH / 2 + 331 * Math.cos(angle), y: 317 + 190 * Math.sin(angle), vx: 0, vy: 0 };
      })
    ];
  }
  return source.map((node, index) => {
    if (node.id === preferredRoot) return { ...node, x: VIEWBOX_WIDTH / 2, y: VIEWBOX_HEIGHT / 2, vx: 0, vy: 0 };
    const orbitIndex = index > 0 ? index - 1 : index;
    const ring = Math.floor(orbitIndex / 12);
    const slot = orbitIndex % 12;
    const remaining = Math.max(1, source.length - 1 - ring * 12);
    const ringCount = Math.min(12, remaining);
    const angle = slot / ringCount * Math.PI * 2 + ring * 0.34 + deterministicOffset(node.id) * 0.08;
    const radius = 108 + ring * 56;
    return {
      ...node,
      x: VIEWBOX_WIDTH / 2 + Math.cos(angle) * radius,
      y: VIEWBOX_HEIGHT / 2 + Math.sin(angle) * radius,
      vx: 0,
      vy: 0
    };
  });
}

function mindMapLayout(source: KnowledgeNode[]) {
  const ids = new Set(source.map((node) => node.id));
  const preferredRoot = ids.has(rootNodeId.value)
    ? rootNodeId.value
    : ids.has(OVERVIEW_ROOT_ID)
      ? OVERVIEW_ROOT_ID
      : selected.value?.id && ids.has(selected.value.id)
        ? selected.value.id
        : source[0]?.id || '';
  rootNodeId.value = preferredRoot;
  const adjacency = new Map<string, string[]>();
  source.forEach((node) => adjacency.set(node.id, []));
  sourceEdges.value.forEach((edge) => {
    adjacency.get(edge.source)?.push(edge.target);
    adjacency.get(edge.target)?.push(edge.source);
  });

  const depth = new Map<string, number>([[preferredRoot, 0]]);
  const parents: Record<string, string> = {};
  const queue = [preferredRoot];
  while (queue.length) {
    const current = queue.shift()!;
    const nextDepth = (depth.get(current) ?? 0) + 1;
    for (const neighbor of adjacency.get(current) ?? []) {
      if (depth.has(neighbor)) continue;
      depth.set(neighbor, nextDepth);
      parents[neighbor] = current;
      queue.push(neighbor);
    }
  }

  source.forEach((node, index) => {
    if (depth.has(node.id)) return;
    depth.set(node.id, 1 + (index % 2));
  });
  treeParents.value = parents;
  const columns = new Map<number, KnowledgeNode[]>();
  source.forEach((node) => {
    const level = Math.min(depth.get(node.id) ?? 1, 4);
    const items = columns.get(level) ?? [];
    items.push(node);
    columns.set(level, items);
  });

  return source.map((node) => {
    const level = Math.min(depth.get(node.id) ?? 1, 4);
    const peers = columns.get(level) ?? [node];
    const index = peers.findIndex((item) => item.id === node.id);
    const verticalRange = Math.min(500, Math.max(100, (peers.length - 1) * 58));
    const y = peers.length === 1 ? VIEWBOX_HEIGHT / 2 : (VIEWBOX_HEIGHT - verticalRange) / 2 + index * (verticalRange / (peers.length - 1));
    return {
      ...node,
      x: 92 + level * 195,
      y,
      vx: 0,
      vy: 0,
      depth: level
    };
  });
}

function resetLayout() {
  if (!sourceNodes.value.length) {
    positionedNodes.value = [];
    selected.value = null;
    return;
  }
  treeParents.value = {};
  const layout = graphMode.value === 'mindmap' ? mindMapLayout(sourceNodes.value) : networkLayout(sourceNodes.value);
  positionedNodes.value = layout;
  const selectedId = selected.value?.id;
  selected.value = layout.find((node) => node.id === selectedId)
    ?? layout.find((node) => node.id === rootNodeId.value)
    ?? layout[0]
    ?? null;
}

function simulate(timestamp: number) {
  animationFrame = requestAnimationFrame(simulate);
  if (graphMode.value !== 'network' || isOverview.value || isMotionPaused.value || document.hidden || !stageVisible.value || !positionedNodes.value.length) {
    previousFrame = timestamp;
    return;
  }
  const delta = Math.min(2, Math.max(0.45, (timestamp - previousFrame) / 16.67 || 1));
  previousFrame = timestamp;
  const items = positionedNodes.value;
  const lookup = new Map(items.map((node) => [node.id, node]));
  const radii = items.map(networkNodeRadius);

  for (let first = 0; first < items.length; first += 1) {
    for (let second = first + 1; second < items.length; second += 1) {
      const a = items[first];
      const b = items[second];
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      const distanceSquared = Math.max(180, dx * dx + dy * dy);
      const distance = Math.sqrt(distanceSquared);
      dx /= distance;
      dy /= distance;
      const overlap = Math.max(0, radii[first] + radii[second] + 4 - distance);
      const force = (Math.min(1.2, 1700 / distanceSquared) + overlap * 0.055) * delta;
      if (draggingId.value !== a.id) { a.vx -= dx * force; a.vy -= dy * force; }
      if (draggingId.value !== b.id) { b.vx += dx * force; b.vy += dy * force; }
    }
  }

  sourceEdges.value.forEach((edge) => {
    const source = lookup.get(edge.source);
    const target = lookup.get(edge.target);
    if (!source || !target) return;
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.max(1, Math.sqrt(dx * dx + dy * dy));
    const pull = (distance - 132) * 0.00075 * delta;
    if (draggingId.value !== source.id) { source.vx += (dx / distance) * pull; source.vy += (dy / distance) * pull; }
    if (draggingId.value !== target.id) { target.vx -= (dx / distance) * pull; target.vy -= (dy / distance) * pull; }
  });

  items.forEach((node, index) => {
    if (draggingId.value === node.id) return;
    const rootStrength = node.id === rootNodeId.value ? 0.004 : 0.00072;
    node.vx += (VIEWBOX_WIDTH / 2 - node.x) * rootStrength * delta;
    node.vy += (VIEWBOX_HEIGHT / 2 - node.y) * rootStrength * delta;
    node.vx += Math.cos(timestamp / 1750 + index * 1.7) * 0.0022;
    node.vy += Math.sin(timestamp / 1600 + index * 1.3) * 0.0022;
    node.vx *= 0.91;
    node.vy *= 0.91;
    node.x = Math.min(VIEWBOX_WIDTH - 64, Math.max(64, node.x + node.vx * delta));
    node.y = Math.min(VIEWBOX_HEIGHT - 54, Math.max(78, node.y + node.vy * delta));
  });
}

function edgePath(edge: KnowledgeEdge) {
  const source = nodeMap.value[edge.source];
  const target = nodeMap.value[edge.target];
  if (!source || !target) return '';
  if (graphMode.value === 'mindmap') {
    const middle = (source.x + target.x) / 2;
    return `M ${source.x} ${source.y} C ${middle} ${source.y}, ${middle} ${target.y}, ${target.x} ${target.y}`;
  }
  return `M ${source.x} ${source.y} L ${target.x} ${target.y}`;
}

function isActiveEdge(edge: KnowledgeEdge) {
  return Boolean(selected.value && (edge.source === selected.value.id || edge.target === selected.value.id));
}

function selectNode(node: PositionedNode) {
  selected.value = node;
}

function focusSelected() {
  if (!selected.value) return;
  focusedNodeId.value = selected.value.id;
  rootNodeId.value = selected.value.id;
  zoom.value = 1;
  resetLayout();
}

function clearFocus() {
  focusedNodeId.value = '';
  rootNodeId.value = '';
  zoom.value = 1;
  resetLayout();
}

function edgeLabelX(edge: KnowledgeEdge) {
  const source = nodeMap.value[edge.source];
  const target = nodeMap.value[edge.target];
  return source && target ? (source.x + target.x) / 2 : 0;
}

function edgeLabelY(edge: KnowledgeEdge) {
  const source = nodeMap.value[edge.source];
  const target = nodeMap.value[edge.target];
  return source && target ? (source.y + target.y) / 2 - 4 : 0;
}

function zoomBy(amount: number) {
  zoom.value = Math.min(1.45, Math.max(0.72, Number((zoom.value + amount).toFixed(2))));
}

function pointerCoordinates(event: PointerEvent) {
  const matrix = svgRef.value?.getScreenCTM();
  if (!matrix) return { x: 0, y: 0 };
  const { x, y } = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
  return {
    x: VIEWBOX_WIDTH / 2 + (x - VIEWBOX_WIDTH / 2) / zoom.value,
    y: VIEWBOX_HEIGHT / 2 + (y - VIEWBOX_HEIGHT / 2) / zoom.value
  };
}

function startDrag(event: PointerEvent, node: PositionedNode) {
  draggingId.value = node.id;
  selected.value = node;
  node.vx = 0;
  node.vy = 0;
  (event.currentTarget as SVGElement).setPointerCapture?.(event.pointerId);
}

function dragNode(event: PointerEvent) {
  if (!draggingId.value) return;
  const node = nodeMap.value[draggingId.value];
  if (!node) return;
  const point = pointerCoordinates(event);
  node.x = Math.min(VIEWBOX_WIDTH - 64, Math.max(64, point.x));
  node.y = Math.min(VIEWBOX_HEIGHT - 54, Math.max(78, point.y));
}

function endDrag() {
  draggingId.value = null;
}
</script>

<template>
  <div class="workspace-page graph-page">
    <section class="kg-banner" aria-labelledby="kg-title">
      <div class="kg-banner-copy">
        <span>知识图谱 <ChevronRight /> 系统 <ChevronRight /> 器官 <ChevronRight /> 精细结构</span>
        <h1 id="kg-title">人体解剖知识图谱</h1>
        <p>从人体系统进入器官和精细结构，建立与三维模型一致的解剖学习路径。</p>
      </div>
      <div class="kg-banner-totals" aria-label="全图概况">
        <div v-for="stat in graphTotals" :key="stat.label">
          <component :is="stat.icon" :size="23" /><strong>{{ stat.value }}</strong><small>{{ stat.label }}</small>
        </div>
      </div>
    </section>

    <form class="graph-toolbar kg-toolbar" @submit.prevent="retrieveEvidence">
      <label class="search-control">
        <Search :size="18" />
        <input v-model="query" aria-label="检索人体系统、器官或精细结构" placeholder="检索人体系统、器官或精细结构…" />
      </label>
      <select v-model="type" aria-label="筛选知识类型">
        <option value="全部类型">全部类型</option>
        <option v-for="(text, key) in typeLabels" :key="key" :value="key">{{ text }}</option>
      </select>
      <div class="graph-view-switch" role="group" aria-label="图谱视图">
        <button type="button" :class="{ active: graphMode === 'network' }" :aria-pressed="graphMode === 'network'" @click="graphMode = 'network'"><Network :size="16" />知识网络</button>
        <button type="button" :class="{ active: graphMode === 'mindmap' }" :aria-pressed="graphMode === 'mindmap'" @click="graphMode = 'mindmap'"><BrainCircuit :size="16" />脑图</button>
        <button type="button" :class="{ active: graphMode === 'list' }" :aria-pressed="graphMode === 'list'" @click="graphMode = 'list'"><List :size="16" />列表视图</button>
        <RouterLink v-if="trainingStore.state.profile.role === 'student'" class="kg-3d-link" to="/student/anatomy"><Layers3 :size="16" />三维模型</RouterLink>
      </div>
      <button class="button-primary" type="submit"><Search :size="16" />检索匹配</button>
    </form>

    <div class="graph-workbench anatomy-graph-workbench">
      <section ref="stageRef" class="graph-stage anatomy-graph-stage" data-tour="graph-stage" :class="[`mode-${graphMode}`, { 'kg-overview': isOverview && graphMode === 'network' }]">
        <div v-show="graphMode !== 'list'" class="graph-legend">
          <span v-for="(text, key) in typeLabels" :key="key"><i :class="`node-${key}`"></i>{{ text }}</span>
        </div>
        <div v-show="graphMode !== 'list'" class="graph-stage-actions">
          <span class="graph-motion-state"><i :class="{ paused: isMotionPaused }"></i>{{ graphStatus }}</span>
          <button v-if="graphMode === 'network' && !isOverview" class="icon-button" type="button" :title="isMotionPaused ? '继续动态布局' : '暂停动态布局'" :aria-label="isMotionPaused ? '继续动态布局' : '暂停动态布局'" @click="isMotionPaused = !isMotionPaused">
            <Play v-if="isMotionPaused" :size="17" /><Pause v-else :size="17" />
          </button>
          <button class="icon-button" type="button" title="放大图谱" aria-label="放大图谱" @click="zoomBy(0.1)"><Plus :size="17" /></button>
          <button class="icon-button" type="button" title="缩小图谱" aria-label="缩小图谱" @click="zoomBy(-0.1)"><Minus :size="17" /></button>
          <button class="icon-button" type="button" title="重置布局" aria-label="重置布局" @click="zoom = 1; resetLayout()"><RotateCcw :size="17" /></button>
        </div>

        <div v-show="graphMode !== 'list'" ref="canvasScrollRef" class="graph-canvas-scroll">
          <svg
            ref="svgRef"
            :viewBox="`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`"
            role="img"
            aria-label="可拖拽的医学教育知识图谱"
            @pointermove="dragNode"
            @pointerup="endDrag"
            @pointercancel="endDrag"
          >
            <g :transform="viewportTransform">
              <g v-if="isOverview && graphMode === 'network'" class="kg-overview-decoration" aria-hidden="true">
                <ellipse class="kg-orbit" cx="460" cy="317" rx="331" ry="190" />
                <image class="kg-body-model" :href="anatomyModel" x="382" y="318" width="156" height="208" />
              </g>
              <path
                v-for="edge in displayEdges"
                :key="`${edge.source}-${edge.target}-${edge.relation}`"
                class="kg-edge"
                :class="{ active: isActiveEdge(edge), virtual: edge.relation === 'learning_stage' }"
                :d="edgePath(edge)"
              />
              <template v-if="graphMode === 'network' && !isOverview">
                <text
                  v-for="edge in labeledEdges"
                :key="`label-${edge.source}-${edge.target}-${edge.relation}`"
                class="kg-edge-label"
                text-anchor="middle"
                :x="edgeLabelX(edge)"
                :y="edgeLabelY(edge)"
                >{{ edge.relation_zh || edge.relation }}</text>
              </template>
              <g
                v-for="node in positionedNodes"
                :key="node.id"
                class="kg-node"
                :class="[{ selected: selected?.id === node.id, dragging: draggingId === node.id }, `node-shape-${node.group || node.type}`]"
                :transform="`translate(${node.x} ${node.y})`"
                tabindex="0"
                role="button"
                :aria-label="`${groupLabel(node)}：${label(node)}`"
                @pointerdown="startDrag($event, node)"
                @click="selectNode(node)"
                @keydown.enter="selectNode(node)"
                @keydown.space.prevent="selectNode(node)"
              >
                <template v-if="graphMode === 'network' && (nodeGroup(node) === 'AnatomyOrgan' || nodeGroup(node) === 'AnatomyStructure')">
                  <title>{{ label(node) }}</title>
                  <circle class="kg-branch-node" :r="networkNodeRadius(node)" />
                  <AnatomyGraphIcon v-if="nodeGroup(node) === 'AnatomyOrgan'" class="kg-organ-icon" :node-id="node.id" light x="-10" y="-20" width="20" height="20" />
                  <text class="kg-node-title kg-branch-title" text-anchor="middle" :dominant-baseline="nodeGroup(node) === 'AnatomyStructure' ? 'central' : undefined">
                    <tspan v-for="line in branchLabelLines(node)" :key="line.y" x="0" :y="line.y">{{ line.text }}</tspan>
                  </text>
                </template>
                <template v-else-if="graphMode === 'network' && (isOverview || hasAnatomyMedallion(node))">
                  <circle class="kg-overview-node" :r="isOverview ? (node.id === OVERVIEW_ROOT_ID ? 61 : 50) : networkNodeRadius(node)" />
                  <AnatomyGraphIcon class="kg-overview-icon" :node-id="node.id" :x="isOverview ? -21 : -12" :y="isOverview ? -37 : -23" :width="isOverview ? 42 : 24" :height="isOverview ? 42 : 24" />
                  <text class="kg-node-title kg-medallion-title" text-anchor="middle" :y="isOverview ? 23 : 15">{{ label(node) }}</text>
                </template>
                <template v-else>
                  <circle v-if="graphMode === 'network'" :class="`node-${node.group || node.type}`" :r="networkNodeRadius(node)" />
                  <rect v-else :class="`node-${node.group || node.type}`" x="-67" y="-23" width="134" height="46" rx="8" />
                  <text class="kg-node-title" text-anchor="middle" :y="graphMode === 'mindmap' ? -2 : 4">{{ label(node).slice(0, graphMode === 'mindmap' ? 10 : 7) }}</text>
                  <text v-if="graphMode === 'mindmap'" class="kg-node-type" text-anchor="middle" y="14">{{ groupLabel(node) }}</text>
                </template>
              </g>
            </g>
          </svg>
        </div>
        <small v-show="graphMode !== 'list'" class="kg-scroll-hint">左右滑动查看图谱</small>
        <p v-if="!sourceNodes.length && graphMode !== 'list'" class="kg-empty-canvas">没有匹配的节点</p>
        <div v-if="graphMode === 'list'" class="kg-node-list">
          <header><h2><List :size="19" />列表视图</h2><span>{{ sourceNodes.length }} 个当前节点</span></header>
          <button v-for="node in positionedNodes" :key="node.id" type="button" :aria-pressed="selected?.id === node.id" @click="selectNode(node)">
            <i :class="'node-' + nodeGroup(node)"></i><strong>{{ label(node) }}</strong><span>{{ groupLabel(node) }}</span><ChevronRight :size="15" />
          </button>
          <p v-if="!positionedNodes.length">没有匹配的节点</p>
        </div>
      </section>

      <aside class="kg-side" aria-label="节点与关联详情">
        <section class="kg-card kg-summary">
          <h2><BookOpenCheck />图谱概览</h2>
          <strong class="kg-selected-name">{{ selected ? label(selected) : '未选择节点' }}</strong>
          <p>{{ selected ? (selected.description_zh || selected.summary || '该节点用于连接人体系统、器官与精细结构。') : '选择图谱中的节点以查看详情。' }}</p>
          <div class="graph-focus-actions">
            <button class="button-primary" type="button" :disabled="!selected" @click="focusSelected"><LocateFixed :size="15" />展开两跳关系</button>
            <button v-if="focusedNodeId" class="graph-back-button" type="button" @click="clearFocus"><RotateCcw :size="14" />返回筛选网络</button>
          </div>
        <div class="graph-source-tags">
          <button v-for="source in selected?.source_ids ?? []" :key="source" type="button" @click="openSource(source)">
            <BookOpenCheck :size="13" /><span>{{ sourceName(source) }}</span><ChevronRight :size="13" />
          </button>
        </div>
        <section v-if="activeSource" class="graph-source-detail" aria-live="polite">
          <small>{{ activeSource.platform }} · {{ activeSource.type }}</small>
          <strong>{{ activeSource.name }}</strong>
          <p>{{ activeSource.license }}</p>
          <div><span v-for="module in activeSource.modules" :key="module">{{ module }}</span></div>
          <a v-if="activeSource.url" :href="activeSource.url" target="_blank" rel="noreferrer">
            访问公开来源 <ExternalLink :size="14" />
          </a>
        </section>
        </section>
        <section class="kg-card kg-relations">
          <header>
            <h2><Link2 />直接关联</h2>
            <button v-if="neighbors.length > 4" class="kg-text-button" type="button" :aria-expanded="showAllRelations" @click="showAllRelations = !showAllRelations">{{ showAllRelations ? '收起' : '查看全部' }}<ChevronRight :size="15" /></button>
          </header>
          <button v-for="edge in visibleNeighbors" :key="`${edge.source}-${edge.target}-${edge.relation}`" class="kg-relation-row" type="button" @click="selectRelated(edge)">
            <span class="kg-relation-icon"><AnatomyGraphIcon :node-id="relatedNode(edge)?.id" width="27" height="27" /></span>
            <span><strong>{{ label(relatedNode(edge)) }}</strong><small>{{ edge.relation_zh || edge.relation }}<template v-if="edge.evidence_source"> · {{ sourceName(edge.evidence_source) }}</template></small></span>
            <small v-if="relatedNode(edge)" class="kg-relation-count">{{ degreeByNode.get(relatedNode(edge)?.id ?? '') }} 条</small>
            <ChevronRight :size="15" />
          </button>
          <p v-if="!neighbors.length" class="kg-quiet">暂无直接关联。</p>
        </section>
      </aside>
    </div>

    <div class="kg-lower">
      <section class="kg-card kg-statistics">
        <h2><BarChart3 />图谱统计</h2>
        <div>
          <article v-for="stat in graphTotals" :key="stat.label">
            <component :is="stat.icon" :size="21" /><strong>{{ stat.value }}</strong><small>{{ stat.label }}</small>
          </article>
        </div>
      </section>
      <section class="kg-card kg-path">
        <h2><GraduationCap />学习路径推荐</h2>
        <div>
          <button v-for="step in learningSteps" :key="step.type" type="button" @click="chooseLearningStep(step.type)">
            <component :is="step.icon" :size="22" />{{ step.label }}
          </button>
        </div>
      </section>
      <section class="kg-card kg-distribution">
        <h2><ScanLine />节点类型分布</h2>
        <ul>
          <li v-for="group in graphGroups" :key="group.key">
            <span>{{ group.title }}</span><span aria-hidden="true" class="kg-bar-track"><i :style="{ width: group.count / maxGroupCount * 100 + '%' }"></i></span><strong>{{ group.count }}</strong>
          </li>
        </ul>
      </section>
    </div>

    <section v-if="evidenceResults.length" class="evidence-results">
      <div class="section-heading">
        <div><span class="section-kicker">检索结果</span><h2>{{ query ? `“${query}”的可追溯依据` : '可追溯医学证据' }}</h2></div>
      </div>
      <article v-for="item in evidenceResults" :key="item.title">
        <span>{{ item.kind }}</span><strong>{{ item.title }}</strong><p>{{ item.summary }}</p>
      </article>
    </section>
  </div>
</template>

<style scoped src="../knowledge-graph-dashboard.css"></style>
