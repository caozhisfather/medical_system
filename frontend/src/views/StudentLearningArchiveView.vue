<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { CalendarCheck2, History, Sparkles } from '@lucide/vue';
import DailyReviewView from './DailyReviewView.vue';
import HistoryView from './HistoryView.vue';

type ArchiveTab = 'review' | 'history';

const route = useRoute();
const router = useRouter();
const activeTab = ref<ArchiveTab>(route.query.tab === 'history' ? 'history' : 'review');

watch(() => route.query.tab, (tab) => {
  activeTab.value = tab === 'history' ? 'history' : 'review';
});

function selectTab(tab: ArchiveTab) {
  activeTab.value = tab;
  void router.replace({ path: '/student/archive', query: { tab } });
}
</script>

<template>
  <div class="workspace-page learning-archive-page">
    <section class="archive-heading">
      <div>
        <span class="section-kicker">学习沉淀与持续改进</span>
        <h1>学习档案</h1>
        <p>在同一个页面查看今日 AI 复盘、历史训练轨迹、教师反馈和下一步学习计划。</p>
      </div>
      <span class="archive-summary"><Sparkles :size="18" /><strong>训练—复盘—再训练</strong><small>形成连续学习闭环</small></span>
    </section>

    <nav class="archive-tabs" aria-label="学习档案分类">
      <button type="button" :class="{ active: activeTab === 'review' }" @click="selectTab('review')">
        <CalendarCheck2 :size="18" /><span><strong>今日复盘</strong><small>能力画像 · 薄弱点 · 明日计划</small></span>
      </button>
      <button type="button" :class="{ active: activeTab === 'history' }" @click="selectTab('history')">
        <History :size="18" /><span><strong>历史训练</strong><small>训练报告 · 教师反馈 · 再次训练</small></span>
      </button>
    </nav>

    <section class="archive-content">
      <DailyReviewView v-if="activeTab === 'review'" />
      <HistoryView v-else />
    </section>
  </div>
</template>

