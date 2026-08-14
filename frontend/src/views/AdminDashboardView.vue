<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { Activity, Bot, Database, FileCog, GitBranch, PlayCircle, ShieldAlert, SlidersHorizontal } from '@lucide/vue';
import { getAdminDataSources, getDailyReviewPolicy, getGraphStatus, getKnowledgeStatus, syncAdminDataSources } from '../api';
import { mockAdminData } from '../data/admin';
import { mockDailyReviewPolicy } from '../data/dailyReview';
import type { DailyReviewPolicy, DataSourceItem } from '../types';

const sources = ref<DataSourceItem[]>(mockAdminData.dataSources as DataSourceItem[]);
const policy = ref<DailyReviewPolicy>(mockDailyReviewPolicy);
const knowledgeStatus = ref<Record<string, unknown>>({ items: 85, vector_ready: 85, bilingual_items: 85 });
const graphStatus = ref<Record<string, unknown>>({ nodes: 177, edges: 162, obsidian_ready: true });
const syncing = ref(false);

const weights = computed(() => Object.entries(policy.value.score_weights));

onMounted(async () => {
  try { sources.value = await getAdminDataSources(); } catch { sources.value = mockAdminData.dataSources as DataSourceItem[]; }
  try { policy.value = await getDailyReviewPolicy(); } catch { policy.value = mockDailyReviewPolicy; }
  try { knowledgeStatus.value = await getKnowledgeStatus(); } catch { /* Keep mock status visible. */ }
  try { graphStatus.value = await getGraphStatus(); } catch { /* Keep mock status visible. */ }
});

async function syncSources() {
  if (syncing.value) return;
  syncing.value = true;
  try {
    const result = await syncAdminDataSources();
    sources.value = result.sources;
  } catch {
    sources.value = [...sources.value];
  } finally {
    syncing.value = false;
  }
}
</script>

<template>
  <div class="workspace-page admin-page">
    <section class="page-title-row admin-heading">
      <div>
        <span class="section-kicker">超级管理员控制台</span>
        <h1>数据源、知识库、图谱、Agent 与复盘策略配置</h1>
        <p>管理教学数据接入、索引状态和每日复盘生成逻辑。演示环境不包含真实 API key 和真实患者隐私数据。</p>
      </div>
      <button class="button-primary" type="button" :disabled="syncing" @click="syncSources">
        <PlayCircle :size="18" /> {{ syncing ? '正在模拟同步' : '模拟同步数据源' }}
      </button>
    </section>

    <section id="knowledge-status" class="metric-strip admin-metrics">
      <article><Database :size="19" /><span><small>数据源</small><strong>{{ sources.length }} 类</strong></span><b>Mock</b></article>
      <article data-tour="admin-knowledge"><FileCog :size="19" /><span><small>知识条目</small><strong>{{ knowledgeStatus.items }}</strong></span><b>{{ knowledgeStatus.vector_ready }} 已索引</b></article>
      <article data-tour="admin-graph"><GitBranch :size="19" /><span><small>图谱规模</small><strong>{{ graphStatus.nodes }}/{{ graphStatus.edges }}</strong></span><b>节点/关系</b></article>
      <article><Activity :size="19" /><span><small>复盘服务</small><strong>{{ policy.service_status }}</strong></span><b>{{ policy.last_generated_at }}</b></article>
    </section>

    <div class="admin-grid">
      <section class="surface-panel review-policy-panel" data-tour="admin-review-policy">
        <div class="section-heading"><div><span class="section-kicker">复盘策略配置</span><h2>每日复盘生成逻辑</h2></div><SlidersHorizontal :size="20" /></div>
        <div class="policy-form-grid">
          <label>复盘生成时间<input v-model="policy.generate_time" /></label>
          <label>推荐病例数量<input v-model.number="policy.recommended_case_count" type="number" min="1" max="5" /></label>
          <label>推荐知识点数量<input v-model.number="policy.recommended_knowledge_count" type="number" min="1" max="8" /></label>
        </div>
        <div class="policy-toggle-grid">
          <label><input v-model="policy.digital_human_review_enabled" type="checkbox" /> 启用数字人复盘</label>
          <label><input v-model="policy.teacher_alert_enabled" type="checkbox" /> 启用教师预警</label>
        </div>
        <div class="weight-list">
          <div v-for="[key, value] in weights" :key="key">
            <span><strong>{{ key }}</strong><b>{{ Math.round(value * 100) }}%</b></span>
            <i><em :style="{ width: `${value * 100}%` }"></em></i>
          </div>
        </div>
        <button class="button-secondary" type="button">生成 mock 复盘数据</button>
        <p>{{ policy.policy_note }}</p>
      </section>

      <section id="data-sources" class="surface-panel admin-source-panel" data-tour="admin-data-source">
        <div class="section-heading"><div><span class="section-kicker">数据源管理</span><h2>ModelScope / 指南 / 自建病例</h2></div><Database :size="20" /></div>
        <article v-for="source in sources.slice(0, 6)" :key="source.id">
          <span :class="{ connected: source.connected }"></span>
          <div><strong>{{ source.name }}</strong><small>{{ source.platform }} · {{ source.type }} · {{ source.index_status }}</small></div>
          <b>{{ source.connected ? '已接入' : '待审查' }}</b>
        </article>
      </section>
    </div>

    <div class="admin-grid lower">
      <section class="surface-panel admin-agent-panel" data-tour="admin-debug">
        <div class="section-heading"><div><span class="section-kicker">Agent 工作流</span><h2>接口与任务状态</h2></div><Bot :size="20" /></div>
        <ol>
          <li><span>RouterAgent</span><strong>识别复盘、病例、图谱和后台配置意图</strong></li>
          <li><span>ReviewAgent</span><strong>聚合训练记录、错题、解剖与图谱路径</strong></li>
          <li><span>SafetyAgent</span><strong>保持医学教育边界，不输出真实诊断建议</strong></li>
        </ol>
      </section>
      <section class="surface-panel admin-safety-panel">
        <div class="section-heading"><div><span class="section-kicker">系统调试</span><h2>安全与合规边界</h2></div><ShieldAlert :size="20" /></div>
        <p>当前演示只使用虚拟教学病例、公开来源元数据和本地 mock 复盘结果。真实部署前必须完成授权、隐私、伦理和教师审核流程。</p>
      </section>
    </div>
  </div>
</template>
