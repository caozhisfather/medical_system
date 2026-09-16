<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, ClipboardList, Crosshair, Layers3, ScanLine, Sparkles, TriangleAlert } from '@lucide/vue';
import { getAnatomyGlossary } from '../api';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';

type ArchiveTab = 'records' | 'mistakes';

const route = useRoute();
const router = useRouter();
const activeTab = ref<ArchiveTab>(route.query.tab === 'mistakes' ? 'mistakes' : 'records');
const termCount = ref(0);
const structureCount = ref(0);

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

onMounted(async () => {
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
        <p>汇总空间定位测验的作答记录与错题，用于安排下一次复习。</p>
      </div>
      <span class="archive-summary"><Sparkles :size="18" /><strong>探索—测验—复习</strong><small>形成连续学习闭环</small></span>
    </section>

    <section class="archive-coverage">
      <article><Layers3 :size="19" /><span><small>教学系统</small><strong>{{ ANATOMY_SYSTEMS_3D.length }}</strong></span></article>
      <article><ScanLine :size="19" /><span><small>可探索结构</small><strong>{{ structureCount || '—' }}</strong></span></article>
      <article><BookOpenCheck :size="19" /><span><small>中文解剖名</small><strong>{{ termCount || '—' }}</strong></span></article>
    </section>

    <nav class="archive-tabs" aria-label="学习档案分类">
      <button type="button" :class="{ active: activeTab === 'records' }" @click="selectTab('records')">
        <ClipboardList :size="18" /><span><strong>测验记录</strong><small>每次作答的题型、得分与用时</small></span>
      </button>
      <button type="button" :class="{ active: activeTab === 'mistakes' }" @click="selectTab('mistakes')">
        <TriangleAlert :size="18" /><span><strong>错题本</strong><small>按系统汇总易混淆的结构</small></span>
      </button>
    </nav>

    <section class="archive-content">
      <div class="archive-empty">
        <Crosshair :size="30" />
        <strong>{{ activeTab === 'records' ? '还没有测验记录' : '错题本还是空的' }}</strong>
        <p>{{ activeTab === 'records' ? '到虚拟解剖室选中一个结构，切换到空间定位测验即可开始作答，记录会自动汇总到这里。' : '答错的题目会自动收进错题本，并按所属系统归类，方便集中复习。' }}</p>
        <button class="button-primary" type="button" @click="startQuiz">开始空间定位测验 <ArrowRight :size="17" /></button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.archive-coverage { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.archive-coverage article { display: flex; align-items: center; gap: 10px; padding: 14px; border-radius: 8px; background: #eef6f4; color: var(--teal-dark); }
.archive-coverage span { display: grid; gap: 2px; }
.archive-coverage small { color: #6d8a8d; font-size: 11px; }
.archive-coverage strong { color: #21484e; font-size: 20px; }
.archive-empty { display: grid; justify-items: center; gap: 8px; padding: 46px 24px; border-radius: 8px; background: #fbfdfd; box-shadow: 0 10px 30px rgba(23,63,72,.06); color: #6d8a8d; text-align: center; }
.archive-empty strong { color: #21484e; font-size: 16px; }
.archive-empty p { max-width: 520px; margin: 0; font-size: 13px; line-height: 1.65; }
.archive-empty button { margin-top: 6px; }
@media (max-width: 760px) { .archive-coverage { grid-template-columns: 1fr; } }
</style>
