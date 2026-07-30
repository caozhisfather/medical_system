<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { BookOpenCheck, ChevronRight, Network, Search, Sparkles } from '@lucide/vue';
import { getKnowledgeGraph, searchKnowledge } from '../api';
import { mockGraph } from '../data/graph';
import type { KnowledgeEdge, KnowledgeNode } from '../types';

interface PositionedNode extends KnowledgeNode { x: number; y: number }
const route = useRoute();
const query = ref(String(route.query.q || '胸痛'));
const type = ref('全部类型');
const nodes = ref<KnowledgeNode[]>([]);
const edges = ref<KnowledgeEdge[]>([]);
const selected = ref<PositionedNode | null>(null);
const evidenceResults = ref<Array<{ kind: string; title: string; summary: string; target: string }>>([]);
const typeLabels: Record<string, string> = {
  Disease: '疾病', Symptom: '症状', Exam: '检查', Anatomy: '解剖', Case: '病例',
  Guideline: '指南', LearningObjective: '学习目标', Treatment: '处理原则'
};

const positioned = computed<PositionedNode[]>(() => {
  const q = query.value.trim().toLowerCase();
  const filtered = nodes.value.filter((node) => {
    const group = node.group || node.type || '';
    const typeMatch = type.value === '全部类型' || group === type.value;
    const text = [node.label, node.label_zh, node.label_en, node.summary, node.description_zh, ...(node.aliases_zh ?? [])].join(' ').toLowerCase();
    return typeMatch && (!q || text.includes(q) || edges.value.some((edge) => (edge.source === node.id || edge.target === node.id) && nodes.value.some((other) => other.id === (edge.source === node.id ? edge.target : edge.source) && [other.label, other.label_zh].join(' ').toLowerCase().includes(q))));
  }).slice(0, 24);
  const source = filtered.length >= 3 ? filtered : nodes.value.slice(0, 24);
  return source.map((node, index) => {
    const ring = index < 8 ? 150 : 255;
    const ringIndex = index < 8 ? index : index - 8;
    const ringCount = index < 8 ? Math.min(8, source.length) : Math.max(1, source.length - 8);
    const angle = -Math.PI / 2 + ringIndex * Math.PI * 2 / ringCount;
    return { ...node, x: 390 + Math.cos(angle) * ring, y: 300 + Math.sin(angle) * ring };
  });
});
const visibleIds = computed(() => new Set(positioned.value.map((node) => node.id)));
const visibleEdges = computed(() => edges.value.filter((edge) => visibleIds.value.has(edge.source) && visibleIds.value.has(edge.target)).slice(0, 45));
const nodeMap = computed(() => Object.fromEntries(positioned.value.map((node) => [node.id, node])));
const neighbors = computed(() => selected.value ? visibleEdges.value.filter((edge) => edge.source === selected.value?.id || edge.target === selected.value?.id).slice(0, 8) : []);

onMounted(async () => {
  try {
    const graph = await getKnowledgeGraph('zh');
    nodes.value = graph.nodes;
    edges.value = graph.edges;
  } catch {
    nodes.value = mockGraph.nodes as unknown as KnowledgeNode[];
    edges.value = mockGraph.edges as unknown as KnowledgeEdge[];
  }
  selected.value = positioned.value.find((node) => [node.label, node.label_zh].join('').includes(query.value)) ?? positioned.value[0] ?? null;
  await retrieveEvidence();
});
watch(() => route.query.q, async (value) => { if (value) { query.value = String(value); await retrieveEvidence(); } });

async function retrieveEvidence() {
  if (!query.value.trim()) return;
  try {
    const result = await searchKnowledge(query.value);
    evidenceResults.value = result.items.slice(0, 4);
  } catch {
    evidenceResults.value = [
      { kind: '指南依据', title: '急性胸痛基层诊疗指南', summary: '用于危险分层、首轮检查和转诊决策的教学证据。', target: 'chest_pain' },
      { kind: '教材章节', title: '《诊断学》胸痛问诊', summary: '覆盖疼痛部位、性质、诱因、放射和伴随症状。', target: 'diagnostics' }
    ];
  }
}

function label(node?: KnowledgeNode | null) {
  return node?.label_zh || node?.label || node?.id || '知识节点';
}

function groupLabel(node?: KnowledgeNode | null) {
  return typeLabels[node?.group || node?.type || ''] || '医学知识';
}

function relatedNode(edge: KnowledgeEdge) {
  const id = edge.source === selected.value?.id ? edge.target : edge.source;
  return nodeMap.value[id];
}
</script>

<template>
  <div class="workspace-page graph-page">
    <section class="page-title-row">
      <div><span class="section-kicker">RAG 与可追溯证据网络</span><h1>指南知识图谱</h1><p>连接症状、疾病、检查、病例、指南与学习目标，辅助医学教育检索。</p></div>
      <div class="graph-stat"><Network :size="19" /><span><strong>{{ nodes.length }} 个节点</strong><small>{{ edges.length }} 条证据关系</small></span></div>
    </section>
    <section class="graph-toolbar">
      <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="检索胸痛、急性冠脉综合征、心电图" @keydown.enter="retrieveEvidence" /></label>
      <select v-model="type"><option value="全部类型">全部类型</option><option v-for="(text, key) in typeLabels" :key="key" :value="key">{{ text }}</option></select>
      <button class="button-primary" type="button" @click="retrieveEvidence"><Sparkles :size="16" /> 检索证据</button>
    </section>
    <div class="graph-workbench">
      <section class="graph-stage">
        <div class="graph-legend"><span v-for="(text, key) in typeLabels" :key="key"><i :class="`node-${key}`"></i>{{ text }}</span></div>
        <svg viewBox="0 0 780 600" role="img" aria-label="医学教育知识网络">
          <line v-for="edge in visibleEdges" :key="`${edge.source}-${edge.target}-${edge.relation}`" :x1="nodeMap[edge.source]?.x" :y1="nodeMap[edge.source]?.y" :x2="nodeMap[edge.target]?.x" :y2="nodeMap[edge.target]?.y" />
          <g v-for="node in positioned" :key="node.id" class="kg-node" :class="{ selected: selected?.id === node.id }" tabindex="0" @click="selected = node" @keydown.enter="selected = node">
            <circle :class="`node-${node.group || node.type}`" :cx="node.x" :cy="node.y" :r="selected?.id === node.id ? 33 : 27" />
            <text :x="node.x" :y="node.y + 4" text-anchor="middle">{{ label(node).slice(0, 7) }}</text>
          </g>
        </svg>
      </section>
      <aside class="graph-detail">
        <span class="section-kicker">{{ groupLabel(selected) }}</span>
        <h2>{{ label(selected) }}</h2>
        <p>{{ selected?.description_zh || selected?.summary || '该节点用于连接病例训练、教材知识与指南证据。' }}</p>
        <div class="graph-source-tags"><span v-for="source in selected?.source_ids ?? []" :key="source"><BookOpenCheck :size="13" /> {{ source }}</span></div>
        <h3>直接关联</h3>
        <button v-for="edge in neighbors" :key="`${edge.source}-${edge.target}`" type="button" @click="selected = relatedNode(edge)">
          <span><small>{{ edge.relation_zh || edge.relation }}</small><strong>{{ label(relatedNode(edge)) }}</strong></span><ChevronRight :size="16" />
        </button>
        <h3>推荐学习路径</h3>
        <ol><li><span>1</span>症状表征与关键问诊</li><li><span>2</span>致命性鉴别诊断</li><li><span>3</span>检查证据与指南依据</li></ol>
      </aside>
    </div>
    <section class="evidence-results">
      <div class="section-heading"><div><span class="section-kicker">检索结果</span><h2>“{{ query }}”的可追溯依据</h2></div></div>
      <article v-for="item in evidenceResults" :key="item.title"><span>{{ item.kind }}</span><strong>{{ item.title }}</strong><p>{{ item.summary }}</p><button type="button">查看依据 <ChevronRight :size="15" /></button></article>
    </section>
  </div>
</template>
