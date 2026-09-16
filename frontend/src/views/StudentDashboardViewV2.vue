<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, BookOpenCheck, ChartNetwork, Crosshair, History, Layers3, ScanLine, Target } from '@lucide/vue';
import { getAnatomyGlossary } from '../api';
import { ANATOMY_SYSTEMS_3D } from '../data/anatomy3d';
import { trainingStore } from '../stores/training';

const router = useRouter();
const termCount = ref(0);
const totalStructures = ref(0);

const systems = ANATOMY_SYSTEMS_3D;

onMounted(async () => {
  try {
    const response = await getAnatomyGlossary();
    termCount.value = response.count;
  } catch {
    termCount.value = 0;
  }
  try {
    const manifest = await fetch('/anatomy/atlas.json').then((response) => response.json());
    totalStructures.value = manifest.parts?.length ?? 0;
  } catch {
    totalStructures.value = 0;
  }
});

function openSystem(systemId: string) {
  router.push({ path: '/student/anatomy', query: { system: systemId } });
}
</script>

<template>
  <div class="workspace-page student-home-page">
    <section class="dashboard-hero" data-tour="today-task">
      <div class="dashboard-hero-copy">
        <span class="section-kicker">今日学习任务 · 虚拟解剖实验室</span>
        <h1>{{ trainingStore.state.profile.name }}，从三维结构开始今天的训练</h1>
        <p>按“整体人体 → 系统 → 器官 → 精细结构”逐层深入，点击任意结构查看中文解剖名、教材依据与临床应用。</p>
        <div class="hero-action-row">
          <button class="button-primary" type="button" @click="router.push('/student/anatomy')">
            进入虚拟解剖室 <ScanLine :size="18" />
          </button>
          <button class="button-secondary" type="button" @click="router.push({ path: '/student/anatomy', query: { mode: 'practice' } })">
            <Crosshair :size="17" /> 空间定位测验
          </button>
        </div>
        <div class="demo-flow-hint"><span>学习路径</span><b>整体人体</b><i>→</i><b>系统</b><i>→</i><b>器官</b><i>→</i><b>精细结构</b><i>→</i><b>定位测验</b></div>
      </div>
      <div class="hero-progress">
        <strong>{{ totalStructures || '—' }}</strong><span>可探索结构</span>
        <div><i style="width: 100%"></i></div>
        <small>覆盖 {{ systems.length }} 个教学系统</small>
      </div>
    </section>

    <section class="metric-strip">
      <article><Layers3 :size="19" /><span><small>教学系统</small><strong>{{ systems.length }} 个</strong></span><b>分层浏览</b></article>
      <article><ScanLine :size="19" /><span><small>可探索结构</small><strong>{{ totalStructures || '—' }}</strong></span><b>三维模型</b></article>
      <article><BookOpenCheck :size="19" /><span><small>中文对照</small><strong>{{ termCount || '—' }}</strong></span><b>规范解剖名</b></article>
      <article data-tour="evidence"><Target :size="19" /><span><small>空间定位测验</small><strong>三种题型</strong></span><b>教师可配置</b></article>
    </section>

    <section class="dashboard-card-grid dashboard-loop-cards" aria-label="学习闭环">
      <details class="dashboard-fold-card" open><summary><span class="fold-icon"><ScanLine :size="17" /></span><span><small>今日主任务</small><strong>探索循环系统与心脏结构</strong></span><i>展开</i></summary><p>先从整体人体进入循环系统，再下钻到心脏与各心腔，逐个结构查看教材讲解。</p><button class="text-button" type="button" @click="openSystem('circulatory')">打开循环系统 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card"><summary><span class="fold-icon"><Crosshair :size="17" /></span><span><small>空间定位测验</small><strong>选择题 · 判断题 · 简答题</strong></span><i>展开</i></summary><p>围绕当前结构作答，系统即时判分并给出错因。题型与难度由教师在后台设定。</p><button class="text-button" type="button" @click="router.push({ path: '/student/anatomy', query: { mode: 'practice' } })">开始测验 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card"><summary><span class="fold-icon"><BookOpenCheck :size="17" /></span><span><small>结构讲解</small><strong>教材依据可追溯</strong></span><i>展开</i></summary><p>选中结构后由 AnatomyAgent 结合教材索引讲解，命中时给出书名、章节与页码。</p><button class="text-button" type="button" @click="router.push('/student/anatomy')">查看讲解 <ArrowRight :size="15" /></button></details>
      <details class="dashboard-fold-card" data-tour="knowledge-graph"><summary><span class="fold-icon"><ChartNetwork :size="17" /></span><span><small>知识图谱</small><strong>从结构延伸到疾病与检查</strong></span><i>展开</i></summary><p>查看结构在知识网络中的上下游关系，串起解剖、功能与临床联系。</p><button class="text-button" type="button" @click="router.push('/knowledge-graph')">打开图谱 <ArrowRight :size="15" /></button></details>
    </section>

    <div class="dashboard-card-grid dashboard-content-cards">
      <details class="dashboard-fold-card dashboard-wide-card" open>
        <summary><span class="fold-icon"><Layers3 :size="17" /></span><span><small>八大系统</small><strong>按系统进入三维视图</strong></span><i>展开</i></summary>
        <div class="recommended-cases system-entry-list">
          <button v-for="(system, index) in systems" :key="system.id" type="button" @click="openSystem(system.id)">
            <span class="case-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="case-accent" :style="{ background: system.color }"></span>
            <span class="case-copy"><small>{{ system.members.length > 1 ? '含心与血管' : '独立三维模型' }}</small><strong>{{ system.name }}</strong><p>{{ system.summary }}</p></span>
            <ArrowRight :size="18" />
          </button>
        </div>
      </details>

      <details class="dashboard-fold-card">
        <summary><span class="fold-icon"><History :size="17" /></span><span><small>学习档案</small><strong>测验记录与错题</strong></span><i>展开</i></summary>
        <p>定位测验的作答记录与错因分析会汇总在学习档案中，用于安排下一次复习。</p>
        <button class="text-button" type="button" @click="router.push('/student/archive')">查看学习档案 <ArrowRight :size="15" /></button>
      </details>
    </div>
  </div>
</template>

<style scoped>
.system-entry-list button { align-items: center; }
.case-accent { width: 6px; border-radius: 3px; align-self: stretch; min-height: 34px; }
</style>
