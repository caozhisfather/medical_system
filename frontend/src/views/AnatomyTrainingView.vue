<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Activity, ArrowLeft, ArrowRight, BookOpenCheck, Brain, Check, ChevronDown, ChevronRight, CircleAlert, Crosshair, ExternalLink, Eye, Layers3, LoaderCircle, LocateFixed, MousePointer2, PanelLeftClose, PanelLeftOpen, RotateCcw, ScanLine, Target, Video, ZoomIn } from '@lucide/vue';
import { getAnatomyExercises, submitAnatomy } from '../api';
import anatomyImage from '../assets/medical/anatomy-organs.png';
import { mockAnatomyExercises } from '../data/anatomy';
import { anatomyAtlasNodes, anatomyAtlasSystems, type AnatomyAtlasHotspot } from '../data/anatomyAtlas';
import { anatomyImageSources, anatomyVideos } from '../data/anatomyResources';
import type { AnatomyExercise, AnatomyResult } from '../types';

interface Point { x: number; y: number }
interface Zone extends Point { width: number; height: number; shape?: 'ellipse' | 'rect'; covered?: boolean }

const route = useRoute();
const router = useRouter();
const systems = ['全部', '循环系统', '呼吸系统', '消化系统', '泌尿系统', '神经系统'];
const exercises = ref<AnatomyExercise[]>(mockAnatomyExercises.map((item) => ({ ...item, graph_node_ids: [...item.graph_node_ids] })));
const viewMode = ref<'atlas' | 'practice'>('atlas');
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

function hotspotStyle(hotspot: AnatomyAtlasHotspot) {
  return {
    left: (hotspot.x - hotspot.width / 2) + '%',
    top: (hotspot.y - hotspot.height / 2) + '%',
    width: hotspot.width + '%',
    height: hotspot.height + '%'
  };
}

function switchMode(mode: 'atlas' | 'practice') {
  viewMode.value = mode;
  if (mode === 'atlas') {
    if (!anatomyAtlasSystems.includes(activeSystem.value as typeof anatomyAtlasSystems[number])) activeSystem.value = '循环系统';
    const root = anatomyAtlasNodes.find((item) => item.system === activeSystem.value && item.level === 'system');
    if (root) chooseAtlasNode(root.id);
  } else if (!systems.includes(activeSystem.value)) {
    changeSystem('全部');
  }
}

function chooseAtlasNode(id: string, structureId = '') {
  atlasNodeId.value = id;
  atlasStructureId.value = structureId;
}

function openAtlasHotspot(hotspot: AnatomyAtlasHotspot) {
  if (hotspot.target_id) chooseAtlasNode(hotspot.target_id, hotspot.structure_id ?? '');
  else if (hotspot.structure_id) atlasStructureId.value = hotspot.structure_id;
}

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
  if (!covered.value || loading.value) return;
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  point.value = { x: ((event.clientX - rect.left) / rect.width) * 100, y: ((event.clientY - rect.top) / rect.height) * 100 };
  selectedZone.value = contains(activeZone.value, point.value) ? active.value.answer_zone : 'outside';
  result.value = null;
  message.value = '定位点已记录，提交后显示标准区域。';
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
  const requested = typeof route.query.exercise === 'string' ? route.query.exercise : '';
  if (requested && exercises.value.some((item) => item.id === requested)) choose(requested);
});
</script>

<template>
  <div class="workspace-page anatomy-page">
    <header class="page-title-row anatomy-page-heading">
      <div>
        <span class="section-kicker">基础医学 · 实验训练</span>
        <h1>分层解剖图谱与定位训练</h1>
        <p>从系统总览点击进入器官和精细结构，也可切换到定位练习完成评判。</p>
      </div>
      <div class="anatomy-summary">
        <span><strong>{{ exercises.length }}</strong><small>练习项目</small></span>
        <span><strong>{{ anatomyAtlasSystems.length }}</strong><small>人体系统</small></span>
        <span><strong>{{ completed }}</strong><small>本次完成</small></span>
      </div>
    </header>

    <div class="anatomy-mode-switch" role="tablist" aria-label="选择解剖学习模式">
      <button type="button" role="tab" :aria-selected="viewMode === 'atlas'" :class="{ active: viewMode === 'atlas' }" @click="switchMode('atlas')"><Layers3 :size="18" /><span><strong>图谱分层浏览</strong><small>系统 → 器官 → 精细结构</small></span></button>
      <button type="button" role="tab" :aria-selected="viewMode === 'practice'" :class="{ active: viewMode === 'practice' }" @click="switchMode('practice')"><Crosshair :size="18" /><span><strong>解剖定位练习</strong><small>点击定位并获得评分</small></span></button>
    </div>

    <div class="anatomy-system-tabs" role="tablist" aria-label="选择人体系统">
      <button v-for="system in visibleSystems" :key="system" type="button" role="tab" :aria-selected="activeSystem === system" :class="{ active: activeSystem === system }" @click="changeSystem(system)">
        <Brain v-if="system === '神经系统'" :size="17" /><Activity v-else :size="17" />{{ system }}
      </button>
    </div>

    <section v-if="viewMode === 'atlas'" class="anatomy-atlas-workbench" :class="{ 'nav-collapsed': atlasNavCollapsed }">
      <aside class="atlas-layer-nav">
        <header><span><Layers3 :size="18" /><b>图谱层级</b></span><div><small>{{ atlasNodesForSystem.length }} 张图</small><button type="button" :title="atlasNavCollapsed ? '展开图谱层级' : '收起图谱层级'" @click="atlasNavCollapsed = !atlasNavCollapsed"><PanelLeftOpen v-if="atlasNavCollapsed" :size="17" /><PanelLeftClose v-else :size="17" /></button></div></header>
        <div class="atlas-layer-tree">
          <button v-for="node in atlasNodesForSystem" :key="node.id" type="button" :class="[{ active: node.id === atlasNode.id }, `level-${node.level}`]" @click="chooseAtlasNode(node.id)">
            <span><Activity v-if="node.level === 'system'" :size="16" /><ZoomIn v-else :size="15" /></span><span><strong>{{ node.title }}</strong><small>{{ node.level === 'system' ? '系统总览' : '器官精细图' }}</small></span><ChevronRight :size="15" />
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
            <button v-for="(hotspot, index) in atlasNode.hotspots" :key="hotspot.id" type="button" class="atlas-hotspot" :class="{ selected: hotspot.structure_id === atlasStructureId }" :style="hotspotStyle(hotspot)" @click="openAtlasHotspot(hotspot)"><span>{{ index + 1 }}</span><b>{{ hotspot.label }}</b></button>
          </div>
        </div>
        <footer><span><MousePointer2 :size="15" />{{ atlasNode.hotspots.length }} 个可交互热点</span><small>{{ atlasNode.source_label }} · 仅用于医学教学</small></footer>
      </main>

      <aside class="atlas-detail-panel">
        <div class="atlas-level-status"><span>{{ atlasNode.system }}</span><b>{{ atlasNode.level === 'system' ? '第 1 层 · 系统总览' : '第 2 层 · 器官精细图' }}</b></div>
        <span class="section-kicker">当前图谱</span><h2>{{ atlasNode.title }}</h2><p>{{ atlasNode.description }}</p>
        <section v-if="atlasTargets.length" class="atlas-drilldown-list">
          <strong><ZoomIn :size="17" />点击下钻</strong>
          <button v-for="target in atlasTargets" :key="target.id" type="button" @click="openAtlasHotspot(target)"><span><b>{{ target.label }}</b><small>进入器官精细图</small></span><ArrowRight :size="16" /></button>
        </section>
        <section v-if="atlasNode.structures.length" class="atlas-structure-list">
          <strong><Layers3 :size="17" />本图结构</strong>
          <div><button v-for="structure in atlasNode.structures" :key="structure.id" type="button" :class="{ active: structure.id === atlasStructureId }" @click="atlasStructureId = structure.id">{{ structure.name }}</button></div>
        </section>
        <article v-if="atlasStructure" class="atlas-structure-detail">
          <span>{{ atlasStructure.category }}</span><h3>{{ atlasStructure.name }}</h3><p>{{ atlasStructure.description }}</p><div><Activity :size="16" /><small>临床关联</small><strong>{{ atlasStructure.clinical_note }}</strong></div>
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
        <div class="anatomy-image-frame">
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
  </div>
</template>
