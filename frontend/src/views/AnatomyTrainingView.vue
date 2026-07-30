<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Activity, ArrowRight, BookOpenCheck, Brain, Check, CircleAlert, Crosshair, LoaderCircle, LocateFixed, RotateCcw, ScanLine, Target } from '@lucide/vue';
import { getAnatomyExercises, submitAnatomy } from '../api';
import anatomyImage from '../assets/medical/anatomy-organs.png';
import { mockAnatomyExercises } from '../data/anatomy';
import type { AnatomyExercise, AnatomyResult } from '../types';

interface Point { x: number; y: number }
interface Zone extends Point { width: number; height: number; shape?: 'ellipse' | 'rect'; covered?: boolean }

const route = useRoute();
const router = useRouter();
const systems = ['全部', '循环系统', '呼吸系统', '消化系统', '泌尿系统', '神经系统'];
const exercises = ref<AnatomyExercise[]>(mockAnatomyExercises.map((item) => ({ ...item, graph_node_ids: [...item.graph_node_ids] })));
const activeSystem = ref('全部');
const activeId = ref(exercises.value[0].id);
const point = ref<Point | null>(null);
const selectedZone = ref('');
const result = ref<AnatomyResult | null>(null);
const loading = ref(false);
const message = ref('');
const completed = ref(0);

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

function choose(id: string) {
  activeId.value = id;
  point.value = null;
  selectedZone.value = '';
  result.value = null;
  message.value = '';
}

function changeSystem(system: string) {
  activeSystem.value = system;
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
        <h1>解剖定位训练</h1>
        <p>在真实器官图上完成结构定位，获得解剖解释、错误分析与病例学习关联。</p>
      </div>
      <div class="anatomy-summary">
        <span><strong>{{ exercises.length }}</strong><small>练习项目</small></span>
        <span><strong>{{ systems.length - 1 }}</strong><small>人体系统</small></span>
        <span><strong>{{ completed }}</strong><small>本次完成</small></span>
      </div>
    </header>

    <div class="anatomy-system-tabs" role="tablist" aria-label="选择人体系统">
      <button v-for="system in systems" :key="system" type="button" role="tab" :aria-selected="activeSystem === system" :class="{ active: activeSystem === system }" @click="changeSystem(system)">
        <Brain v-if="system === '神经系统'" :size="17" /><Activity v-else :size="17" />{{ system }}
      </button>
    </div>

    <section class="anatomy-workbench">
      <aside class="anatomy-exercise-rail">
        <header><span><ScanLine :size="18" />定位任务</span><small>{{ filtered.length }} 项</small></header>
        <div class="anatomy-exercise-list">
          <button v-for="(exercise, index) in filtered" :key="exercise.id" type="button" :class="{ active: exercise.id === active.id }" @click="choose(exercise.id)">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <span><strong>{{ exercise.title }}</strong><small>{{ exercise.system }}</small></span>
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
        <div class="anatomy-actions">
          <button v-if="!result" class="button-primary" type="button" :disabled="loading || !covered" @click="submit"><LoaderCircle v-if="loading" class="spin" :size="18" /><Target v-else :size="18" />{{ loading ? '正在评判' : '提交定位' }}</button>
          <template v-else><button class="button-secondary" type="button" @click="choose(active.id)"><RotateCcw :size="17" />重新练习</button><button class="button-primary" type="button" @click="next">下一题<ArrowRight :size="17" /></button></template>
          <button class="text-button" type="button" @click="router.push({ path: '/knowledge-graph', query: { q: active.target } })">查看相关知识图谱</button>
        </div>
      </aside>
    </section>
  </div>
</template>