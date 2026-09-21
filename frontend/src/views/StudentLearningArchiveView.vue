<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, ClipboardList, Crosshair, Layers3, RefreshCw, ScanLine, Sparkles, TriangleAlert } from '@lucide/vue';
import { getAnatomyGlossary, getAnatomyMistakes, getAnatomyRecords } from '../api';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';
import type { AnatomyAttempt, AnatomyLearningSummary, AnatomyMistake } from '../types';

type ArchiveTab = 'records' | 'mistakes';

const route = useRoute();
const router = useRouter();
const activeTab = ref<ArchiveTab>(route.query.tab === 'mistakes' ? 'mistakes' : 'records');
const termCount = ref(0);
const structureCount = ref(0);
const loading = ref(false);
const records = ref<AnatomyAttempt[]>([]);
const mistakes = ref<AnatomyMistake[]>([]);
const summary = ref<AnatomyLearningSummary>({ total: 0, correct: 0, accuracy: 0, average_score: 0 });
const loadError = ref('');

const activeItems = computed(() => activeTab.value === 'records' ? records.value : mistakes.value);

watch(() => route.query.tab, (tab) => {
  activeTab.value = tab === 'mistakes' ? 'mistakes' : 'records';
});

function selectTab(tab: ArchiveTab) {
  activeTab.value = tab;
  void router.replace({ path: '/student/archive', query: { tab } });
}

function startQuiz() {
  router.push({ path: '/student/anatomy', query: { mode: 'practice' } });
}

function formatTime(value: string) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function loadArchive() {
  loading.value = true;
  loadError.value = '';
  const [recordResult, mistakeResult] = await Promise.allSettled([
    getAnatomyRecords(),
    getAnatomyMistakes()
  ]);
  if (recordResult.status === 'fulfilled') {
    records.value = recordResult.value.items;
    summary.value = recordResult.value.summary;
  } else {
    loadError.value = '测验记录暂时无法读取。';
  }
  if (mistakeResult.status === 'fulfilled') {
    mistakes.value = mistakeResult.value.items;
  } else {
    loadError.value = '错题本暂时无法读取。';
  }
  loading.value = false;
}

onMounted(async () => {
  await loadArchive();
  try {
    termCount.value = (await getAnatomyGlossary()).count;
  } catch {
    termCount.value = 0;
  }
  try {
    const manifest = await fetch('/anatomy/atlas.json').then((response) => response.json());
    structureCount.value = manifest.parts?.length ?? 0;
  } catch {
    structureCount.value = 0;
  }
});
</script>

<template>
  <div class="workspace-page learning-archive-page">
    <section class="archive-heading">
      <div>
        <span class="section-kicker">学习沉淀与持续改进</span>
        <h1>学习档案</h1>
        <p>汇总二维器官与精细结构定位测验的作答记录、得分和错题，用于安排下一次复习。</p>
      </div>
      <span class="archive-summary"><Sparkles :size="18" /><strong>探索—测验—复习</strong><small>形成连续学习闭环</small></span>
    </section>

    <section class="archive-coverage">
      <article><Layers3 :size="19" /><span><small>教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong></span></article>
      <article><ScanLine :size="19" /><span><small>可探索结构</small><strong>{{ structureCount || '—' }}</strong></span></article>
      <article><ClipboardList :size="19" /><span><small>已答题目</small><strong>{{ summary.total }}</strong></span></article>
      <article><BookOpenCheck :size="19" /><span><small>中文解剖名</small><strong>{{ termCount || '—' }}</strong></span></article>
    </section>

    <nav class="archive-tabs" aria-label="学习档案分类">
      <button type="button" :class="{ active: activeTab === 'records' }" @click="selectTab('records')">
        <ClipboardList :size="18" /><span><strong>测验记录</strong><small>{{ records.length }} 次作答 · 平均 {{ summary.average_score }} 分</small></span>
      </button>
      <button type="button" :class="{ active: activeTab === 'mistakes' }" @click="selectTab('mistakes')">
        <TriangleAlert :size="18" /><span><strong>错题本</strong><small>{{ mistakes.length }} 个待复习结构</small></span>
      </button>
      <button class="archive-refresh" type="button" :disabled="loading" @click="loadArchive">
        <RefreshCw :size="17" :class="{ spin: loading }" />刷新
      </button>
    </nav>

    <section class="archive-content">
      <div v-if="loading" class="archive-state"><RefreshCw class="spin" :size="24" />正在读取学习记录</div>
      <div v-else-if="loadError" class="archive-state is-error"><TriangleAlert :size="24" />{{ loadError }}</div>

      <template v-else-if="activeTab === 'records' && records.length">
        <div class="archive-scoreboard">
          <article><small>累计作答</small><strong>{{ summary.total }}</strong><span>次</span></article>
          <article><small>定位正确</small><strong>{{ summary.correct }}</strong><span>次</span></article>
          <article><small>正确率</small><strong>{{ summary.accuracy }}</strong><span>%</span></article>
          <article><small>平均得分</small><strong>{{ summary.average_score }}</strong><span>分</span></article>
        </div>
        <div class="archive-record-list">
          <article v-for="item in records" :key="item.id" class="archive-record-item">
            <header>
              <span>{{ item.system }}<template v-if="item.organ"> · {{ item.organ }}</template></span>
              <b :class="item.correct ? 'is-correct' : 'is-wrong'">{{ item.correct ? '定位正确' : '需要复习' }}</b>
            </header>
            <div>
              <h3>{{ item.title }}</h3>
              <p>{{ item.feedback }}</p>
            </div>
            <footer>
              <span>{{ formatTime(item.created_at) }} · 目标 {{ item.target }}</span>
              <strong>{{ item.score }} 分</strong>
            </footer>
          </article>
        </div>
      </template>

      <template v-else-if="activeTab === 'mistakes' && mistakes.length">
        <div class="archive-mistake-list">
          <article v-for="item in mistakes" :key="item.exercise_id" class="archive-mistake-item">
            <header><span>{{ item.system }}<template v-if="item.organ"> · {{ item.organ }}</template></span><b>错误 {{ item.attempt_count }} 次</b></header>
            <h3>{{ item.title }} · {{ item.target }}</h3>
            <p>{{ item.explanation }}</p>
            <small>{{ item.clinical_link }}</small>
            <footer><span>最近作答 {{ formatTime(item.latest_at) }}</span><strong>最高 {{ item.best_score }} 分</strong></footer>
          </article>
        </div>
      </template>

      <div v-else class="archive-empty">
        <Crosshair :size="30" />
        <strong>{{ activeTab === 'records' ? '还没有测验记录' : '错题本还是空的' }}</strong>
        <p>{{ activeTab === 'records' ? '进入虚拟解剖室，在二维器官或精细结构图中完成定位并提交，记录会自动汇总到这里。' : '答错的题目会自动收进错题本，并按所属系统归类，方便集中复习。' }}</p>
        <button class="button-primary" type="button" @click="startQuiz">开始空间定位测验 <ArrowRight :size="17" /></button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.archive-coverage { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.archive-coverage article { display: flex; align-items: center; gap: 10px; padding: 14px; border-radius: 8px; background: #eef6f4; color: var(--teal-dark); }
.archive-coverage span { display: grid; gap: 2px; }
.archive-coverage small { color: #6d8a8d; font-size: 11px; }
.archive-coverage strong { color: #21484e; font-size: 20px; }
.archive-tabs .archive-refresh { margin-left: auto; display: inline-flex; min-height: 40px; align-items: center; gap: 6px; padding: 0 12px; border: 1px solid #cbdada; border-radius: 7px; background: #fff; color: #4c6a70; cursor: pointer; }
.archive-state { display: flex; min-height: 180px; align-items: center; justify-content: center; gap: 9px; color: #607a80; }
.archive-state.is-error { color: #a24c43; }
.archive-scoreboard { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.archive-scoreboard article { padding: 14px; border: 1px solid #d9e6e4; border-radius: 8px; background: #f8fbfa; }
.archive-scoreboard small { display: block; margin-bottom: 5px; color: #698286; font-size: 11px; }
.archive-scoreboard strong { color: #174f4a; font-size: 26px; font-variant-numeric: tabular-nums; }
.archive-scoreboard span { margin-left: 4px; color: #728b8e; font-size: 11px; }
.archive-record-list, .archive-mistake-list { display: grid; gap: 10px; }
.archive-record-item, .archive-mistake-item { display: grid; gap: 10px; padding: 15px 16px; border: 1px solid #dce7e6; border-radius: 8px; background: #fff; }
.archive-record-item header, .archive-mistake-item header, .archive-record-item footer, .archive-mistake-item footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.archive-record-item header span, .archive-mistake-item header span { color: #6a8287; font-size: 11px; }
.archive-record-item header b, .archive-mistake-item header b { padding: 3px 8px; border-radius: 999px; font-size: 10px; }
.archive-record-item header b.is-correct { background: #e5f4ef; color: #137162; }
.archive-record-item header b.is-wrong, .archive-mistake-item header b { background: #fae9e6; color: #a34d43; }
.archive-record-item h3, .archive-mistake-item h3 { margin: 0; color: #21484e; font-size: 15px; }
.archive-record-item p, .archive-mistake-item p { margin: 5px 0 0; color: #526d72; font-size: 12px; line-height: 1.65; }
.archive-mistake-item small { color: #8a6c34; font-size: 11px; line-height: 1.55; }
.archive-record-item footer span, .archive-mistake-item footer span { color: #84979a; font-size: 10px; }
.archive-record-item footer strong, .archive-mistake-item footer strong { color: #176b5d; font-size: 13px; }
.archive-empty { display: grid; justify-items: center; gap: 8px; padding: 46px 24px; border-radius: 8px; background: #fbfdfd; box-shadow: 0 10px 30px rgba(23,63,72,.06); color: #6d8a8d; text-align: center; }
.archive-empty strong { color: #21484e; font-size: 16px; }
.archive-empty p { max-width: 520px; margin: 0; font-size: 13px; line-height: 1.65; }
.archive-empty button { margin-top: 6px; }
@media (max-width: 900px) {
  .archive-coverage, .archive-scoreboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .archive-tabs { flex-wrap: wrap; }
  .archive-tabs .archive-refresh { margin-left: 0; }
}
@media (max-width: 620px) {
  .archive-coverage, .archive-scoreboard { grid-template-columns: 1fr; }
}
</style>
