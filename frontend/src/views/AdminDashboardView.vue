<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import consoleBanner from '../assets/medical/admin-console-banner.webp';
import { ArrowRight, BookOpen, Box, ShieldCheck, ClipboardCheck, Network } from '@lucide/vue';
import AccessAuditPanel from '../components/admin/AccessAuditPanel.vue';
import { useRoute } from 'vue-router';
import { Activity, Bot, Database, FileClock, FileCog, GitBranch, PlayCircle, ShieldAlert, SlidersHorizontal } from '@lucide/vue';
import { getAdminAuditLogs, getAdminDataSources, getAdminUsers, getDailyReviewPolicy, getGraphStatus, getKnowledgeStatus, reviewTeacher, syncAdminDataSources } from '../api';
import { mockDailyReviewPolicy } from '../data/dailyReview';
import type { DailyReviewPolicy, DataSourceItem } from '../types';

const sources = ref<DataSourceItem[]>([]);
const policy = ref<DailyReviewPolicy>(mockDailyReviewPolicy);
const knowledgeStatus = ref<Record<string, unknown>>({});
const graphStatus = ref<Record<string, unknown>>({});
const syncing = ref(false);
const loadWarning = ref('');
const syncMessage = ref('');
const auditLogs = ref<Array<{ id: string; timestamp: string; account: string; name: string; role: string; action: string; target: string; detail: string }>>([]);
type AdminUser = { id: string; account: string; name: string; email: string; role: string; status: string };
const users = ref<AdminUser[]>([]);
const reviewingUserId = ref('');
const route = useRoute();

const systemHealthy=ref<boolean|null>(null);
const sourceColors=['#0788ff','#43bdff','#718aff','#ad86ff','#3cc9c3','#82ace0'];
const distribution=computed(()=>Object.entries((knowledgeStatus.value.source_counts||{}) as Record<string,number>).map(([id,count],i)=>({id,count,color:sourceColors[i%sourceColors.length],name:sources.value.find(s=>s.id===id)?.name||id,share:Number(knowledgeStatus.value.items)?Math.round(count/Number(knowledgeStatus.value.items)*100):0})));
const donut=computed(()=>{let at=0;return {background:distribution.value.length?'conic-gradient('+distribution.value.map(s=>{const start=at;at+=s.count/Number(knowledgeStatus.value.items)*100;return `${s.color} ${start}% ${at}%`;}).join(',')+')':'#e6eefb'};});
const policyReady=ref(false);
const weights = computed(() => policyReady.value ? Object.entries(policy.value.score_weights) : []);

function scrollToSection() {
  if(!route.hash)return;
  const id=route.hash.replace(/^#/,'');
  nextTick(()=>{const target=document.getElementById(id);const details=target?.closest('details');if(details)details.open=true;target?.scrollIntoView({behavior:'smooth',block:'start'});});
}

let auditTimer: ReturnType<typeof setInterval> | undefined;
let auditRefreshing=false;
onUnmounted(()=>{if(auditTimer)clearInterval(auditTimer);});
onMounted(async () => {
  auditTimer=setInterval(async()=>{if(auditRefreshing||document.visibilityState!=='visible')return;auditRefreshing=true;try{auditLogs.value=(await getAdminAuditLogs()).items;}catch{}finally{auditRefreshing=false;}},5000);
  const failures: string[] = [];
  try { sources.value = await getAdminDataSources(); } catch { failures.push('数据源'); }
  try { policy.value = await getDailyReviewPolicy(); policyReady.value=true; } catch { failures.push('复盘策略'); }
  try { knowledgeStatus.value = await getKnowledgeStatus(); } catch { failures.push('知识库'); }
  try { graphStatus.value = await getGraphStatus(); } catch { failures.push('知识图谱'); }
  try { auditLogs.value = (await getAdminAuditLogs()).items; } catch { failures.push('审计日志'); }
  try { users.value = await getAdminUsers() as AdminUser[]; } catch { failures.push('用户管理'); }
  try{systemHealthy.value=(await fetch(`${import.meta.env.VITE_API_BASE_URL||''}/api/health`)).ok;}catch{systemHealthy.value=false;}
  if (failures.length) loadWarning.value = `${failures.join('、')}暂未连接，请刷新重试。`;
  scrollToSection();
});
watch(() => route.hash, scrollToSection);

async function syncSources() {
  if (syncing.value) return;
  syncing.value = true;
  syncMessage.value = '';
  try {
    const result = await syncAdminDataSources();
    sources.value = result.sources;
    syncMessage.value = result.message;
    auditLogs.value = (await getAdminAuditLogs()).items;
  } catch (error) {
    syncMessage.value = error instanceof Error ? error.message : '同步请求失败，请检查后端服务。';
  } finally {
    syncing.value = false;
  }
}

async function decideTeacher(userId: string, approved: boolean) {
  reviewingUserId.value = userId;
  try {
    await reviewTeacher(userId, approved);
    users.value = await getAdminUsers() as AdminUser[];
    auditLogs.value = (await getAdminAuditLogs()).items;
  } catch (error) {
    syncMessage.value = error instanceof Error ? error.message : '教师审核失败。';
  } finally {
    reviewingUserId.value = '';
  }
}
</script>

<template>
  <div class="system-console">
    <section id="admin-console" class="console-hero" data-tour="admin-console" :style="{'--console-banner':`url(${consoleBanner})`}"><h1>系统控制台</h1><p>数据源、知识库、图谱、Agent 与复盘策略统一配置与运行监控</p></section>
    <p v-if="loadWarning" class="console-notice" role="alert">{{loadWarning}}</p><p v-if="syncMessage" class="console-notice" role="status">{{syncMessage}}</p>
    <section id="knowledge-status" class="console-metrics" aria-label="系统状态总览"><article><i><Database :size="29"/></i><div><small>数据源</small><strong>{{sources.length}} <em>类</em></strong></div></article><article data-tour="admin-knowledge"><i><BookOpen :size="29"/></i><div><small>知识条目</small><strong>{{knowledgeStatus.items ?? '—'}}</strong></div></article><article data-tour="admin-graph"><i><GitBranch :size="29"/></i><div><small>图谱规模</small><strong>{{graphStatus.nodes ?? '—'}} / {{graphStatus.edges ?? '—'}} <em>节点 / 关系</em></strong></div></article><article><i><Box :size="29"/></i><div><small>复盘服务</small><strong>{{policyReady?policy.service_status:'—'}}</strong></div></article><article><i><ShieldCheck :size="29"/></i><div><small>系统状态</small><strong class="health"><b :class="{down:systemHealthy===false}"/>{{systemHealthy===null?'检测中':systemHealthy?'服务可用':'连接异常'}}</strong></div></article></section>
    <div class="console-middle">
     <section class="console-card policy-card" data-tour="admin-review-policy"><header><i><ClipboardCheck :size="22"/></i><div><small>复盘策略配置</small><h2>每日复盘生成逻辑</h2></div></header><div v-if="policyReady" class="console-policy-fields"><label>复盘生成时间<input :value="policy.generate_time" type="time" readonly title="当前复盘接口提供只读演示配置"/></label><label>推荐知识点数量<input :value="policy.recommended_knowledge_count" type="number" readonly title="当前复盘接口提供只读演示配置"/></label></div><p v-else class="quiet">复盘配置暂不可用</p><label v-if="policyReady" class="console-toggle" title="当前复盘接口提供只读演示配置"><input type="checkbox" :checked="policy.teacher_alert_enabled" disabled/><span/>启用教师预警</label></section>
     <section class="console-card distribution-card"><header><i><FileCog :size="22"/></i><h2>知识库来源分布</h2></header><div class="distribution-content"><div class="console-donut" :style="donut"><span><strong>{{knowledgeStatus.items ?? '—'}}</strong><small>知识条目</small></span></div><ul><li v-for="d in distribution" :key="d.id"><i :style="{background:d.color}"/><span :title="d.name">{{d.name}}</span><b>{{d.share}}%</b></li><li v-if="!distribution.length" class="quiet">暂无来源数据</li></ul></div></section>
     <section class="console-card workflow-card" data-tour="admin-debug"><header><i><Network :size="22"/></i><h2>Agent 工作流</h2></header><RouterLink to="/admin/skills"><i><Bot :size="19"/></i><strong>AnatomyTutor</strong><small>本地有界工具编排</small><ArrowRight :size="18"/></RouterLink><RouterLink to="/admin/skills"><i><GitBranch :size="19"/></i><strong>Skill Registry</strong><small>服务端角色校验与小时额度</small><ArrowRight :size="18"/></RouterLink><RouterLink to="/admin/skills"><i><ClipboardCheck :size="19"/></i><strong>调用审计</strong><small>记录成功、拒绝与失败</small><ArrowRight :size="18"/></RouterLink></section>
    </div>
    <AccessAuditPanel />
    <details class="console-more"><summary>数据源、用户审核与复盘策略详情</summary>
     <section id="data-sources" class="console-card" data-tour="admin-data-source"><header><h2>数据源管理</h2><button :disabled="syncing" @click="syncSources">{{syncing?'正在模拟同步':'模拟同步数据源'}}</button></header><div class="source-record" v-for="source in sources" :key="source.id"><strong>{{source.name}}</strong><span>{{source.platform}} · {{source.type}} · {{source.index_status}}</span><b>{{source.connected?'已接入':'待审查'}}</b></div></section>
     <section class="console-card"><h2>复盘策略详情（当前接口只读）</h2><p class="quiet">{{policyReady?policy.policy_note:'配置暂不可用'}}</p><p v-for="[key,value] in weights" :key="key">{{key}} · {{Math.round(value*100)}}%</p></section>
    <section class="surface-panel admin-user-panel">
      <div class="section-heading"><div><span class="section-kicker">账号与权限</span><h2>注册用户与教师审核</h2></div><ShieldAlert :size="20" /></div>
      <div class="admin-user-list">
        <article v-for="user in users" :key="user.id">
          <span><strong>{{ user.name }}</strong><small>{{ user.account }} · {{ user.email || '演示账号' }}</small></span>
          <b>{{ user.role }} · {{ user.status }}</b>
          <div v-if="user.role === 'teacher' && user.status === 'pending_review'">
            <button type="button" :disabled="reviewingUserId === user.id" @click="decideTeacher(user.id, false)">拒绝</button>
            <button class="approve" type="button" :disabled="reviewingUserId === user.id" @click="decideTeacher(user.id, true)">批准</button>
          </div>
        </article>
      </div>
    </section>

    <details class="surface-panel admin-audit-panel">
      <summary>
        <span><FileClock :size="19" /><span><small>操作审计</small><strong>最近 {{ auditLogs.length }} 条教师与管理员操作</strong></span></span>
        <b>{{ auditLogs.length ? '展开记录' : '暂无记录' }}</b>
      </summary>
      <div v-if="auditLogs.length" class="audit-log-list">
        <article v-for="item in auditLogs" :key="item.id">
          <time>{{ new Date(item.timestamp).toLocaleString('zh-CN', { hour12: false }) }}</time>
          <span><strong>{{ item.name }}</strong><small>{{ item.account }} · {{ item.role }}</small></span>
          <span><strong>{{ item.action }}</strong><small>{{ item.target }}{{ item.detail ? ` · ${item.detail}` : '' }}</small></span>
        </article>
      </div>
      <p v-else>教师审核、推荐决策、数据源同步和索引操作将在这里留下可追溯记录。</p>
    </details>
    </details>
  </div>
</template>

<style scoped>
.system-console{padding:8px 16px 22px;width:100%;max-width:1700px;margin:0 auto;display:grid;gap:10px;color:#0c2555;font-size:13px}.system-console *{box-sizing:border-box}.console-hero{height:119px;padding:17px 56px;border-radius:17px;overflow:hidden;color:#fff;background-color:#1389ec;background-image:linear-gradient(90deg,#0076df 0%,#1885ef 45%,#168cf000 72%),var(--console-banner);background-size:100% 100%,auto 260%;background-position:center,right center;background-repeat:no-repeat;box-shadow:0 4px 12px #24559910}.console-hero h1{font-size:42px;line-height:1.2;margin:0 0 7px;color:white;font-weight:800;letter-spacing:1px}.console-hero p{margin:0;color:white;font-size:15px;line-height:1.8;max-width:65%}.console-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.console-metrics article{display:flex;align-items:center;gap:12px;height:73px;padding:10px 16px;border:1px solid white;border-radius:17px;background:linear-gradient(130deg,#fff,#f1f6ff);box-shadow:0 4px 10px #2455990b;min-width:0}.console-metrics article>i{display:grid;place-items:center;flex-shrink:0;width:51px;height:51px;background:linear-gradient(140deg,#e6edff,#def4ff);border-radius:17px;color:#0058ff}.console-metrics small{font-size:12px;color:#4a638b;display:block}.console-metrics strong{font-size:25px;line-height:1.4;color:#0048ff;white-space:nowrap;font-weight:800}.console-metrics em{font-size:10px;font-style:normal;font-weight:500}.health{display:flex;align-items:center;gap:10px;font-size:22px!important}.health b{width:13px;height:13px;background:#10bd24;border-radius:50%;box-shadow:0 0 0 3px #ddfae8}.health b.down{background:#ef4444;box-shadow:0 0 0 3px #ffe5e5}.console-middle{display:grid;grid-template-columns:1fr .95fr 1.02fr;gap:12px}.console-card{border-radius:18px;padding:16px 18px;border:1px solid #fff;background:linear-gradient(130deg,#fff,#f3f7ff);min-width:0;box-shadow:0 4px 12px #24559909}.console-middle>.console-card{height:198px}.console-card header{display:flex;align-items:center;gap:10px;margin-bottom:14px}.console-card header>i{color:#0058ff;display:grid;place-items:center;background:#e7f1ff;border-radius:10px;width:34px;height:34px;flex-shrink:0}.console-card header small{display:block;font-size:13px;color:#15376d;font-weight:700;margin-bottom:3px}.console-card h2{font-size:17px;margin:0;line-height:1.4;font-weight:800}.console-policy-fields{display:grid;grid-template-columns:1fr 1fr;gap:28px;padding:0 20px}.console-policy-fields label{display:grid;gap:7px;font-size:12px;color:#4a638b}.console-policy-fields input{font:inherit;font-weight:700;color:#173868;border:1px solid #d4e3ff;border-radius:7px;background:#fbfdff;padding:9px 12px;width:100%;min-width:0}.console-toggle{display:flex;align-items:center;gap:10px;font-size:14px;font-weight:700;margin:15px 4px 0}.console-toggle input{position:absolute;opacity:0}.console-toggle span{width:39px;height:23px;background:#d6e4fa;border-radius:20px;position:relative}.console-toggle span:after{content:'';position:absolute;width:18px;height:18px;border-radius:50%;background:white;top:2px;left:3px;box-shadow:0 1px 5px #24559922}.console-toggle input:checked+span{background:#0068ff}.console-toggle input:checked+span:after{left:18px}.distribution-card header{margin-bottom:8px}.distribution-content{display:flex;align-items:center;gap:28px;justify-content:center}.console-donut{width:144px;height:144px;border-radius:50%;position:relative;flex-shrink:0;display:grid;place-items:center}.console-donut>span{width:98px;height:98px;border-radius:50%;background:#f8fbff;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:2px}.console-donut strong{font-size:27px;color:#003bdf}.console-donut small{font-size:13px;font-weight:700}.distribution-content ul{list-style:none;margin:0;padding:0;min-width:0;flex:1;max-height:145px;overflow:auto}.distribution-content li{display:flex;align-items:center;gap:9px;margin:11px 0;font-size:12px}.distribution-content li i{width:9px;height:9px;border-radius:50%;flex-shrink:0}.distribution-content li span{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.distribution-content li b{font-weight:750}.workflow-card header{margin-bottom:8px}.workflow-card>a{display:flex;align-items:center;gap:10px;padding:9px 5px;border-bottom:1px solid #e4ecfa;color:#173769;text-decoration:none}.workflow-card>a:last-child{border-bottom:0}.workflow-card>a i{display:grid;place-items:center;width:29px;height:29px;border-radius:9px;background:#e1edff;color:#0055ff;flex-shrink:0}.workflow-card>a strong{font-size:14px;flex-shrink:0;min-width:110px}.workflow-card>a small{font-size:11px;color:#49668e;flex:1}.workflow-card>a>svg{flex-shrink:0}.console-notice{padding:10px 15px;background:#fff3e5;color:#965715;margin:0;border-radius:12px}.quiet{font-size:12px;color:#64748b;line-height:1.8}.console-more{border:1px solid #e0eaff;border-radius:15px;padding:14px;background:#f8fbff}.console-more>summary{color:#2c5692;font-weight:700;cursor:pointer}.console-more .console-card,.console-more .surface-panel{margin-top:15px}.source-record{display:flex;gap:15px;padding:12px;border-bottom:1px solid #e0eaff}.source-record span{flex:1;color:#64748b}.system-console button{border:1px solid #cddfff;background:#f5f9ff;color:#155eef;border-radius:9px;padding:7px 12px;cursor:pointer}.source-record b{font-size:12px}
@media(max-width:1400px){.console-metrics article{gap:8px;padding:10px}.console-metrics article>i{width:38px;height:38px}.console-metrics strong{font-size:21px}.health{font-size:18px!important}.console-middle{grid-template-columns:1fr 1fr}.workflow-card{grid-column:1/-1;height:auto!important}.workflow-card>a{display:inline-flex;width:33%;border-bottom:0}.workflow-card>a small{display:none}.distribution-content{gap:20px}.console-hero{padding:20px 32px}.console-hero h1{font-size:36px}.console-hero p{font-size:13px}}
@media(max-width:900px){.console-metrics{grid-template-columns:repeat(3,minmax(0,1fr))}.console-hero p{max-width:70%}.console-policy-fields{padding:0;gap:15px}.console-card{padding:16px}.workflow-card>a{width:100%}.workflow-card>a small{display:block}.distribution-content{gap:12px}.console-donut{width:120px;height:120px}.console-donut>span{width:82px;height:82px}}
@media(max-width:650px){.system-console{padding:12px}.console-hero{height:auto;min-height:140px;padding:23px;background-image:linear-gradient(90deg,#0076e6,#238cf0d9 65%,#c7e4ff66),var(--console-banner)}.console-hero h1{font-size:30px}.console-hero p{font-size:12px;max-width:92%}.console-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.console-metrics article:last-child{grid-column:1/-1}.console-middle{grid-template-columns:1fr}.workflow-card{grid-column:auto}.source-record{flex-wrap:wrap}.console-more{padding:10px}}
</style>
<style>
@media(min-width:1200px){.product-shell:has(.system-console){grid-template-columns:230px minmax(0,1fr);grid-template-rows:60px minmax(calc(100vh - 60px),auto)}.product-shell:has(.system-console) .product-topbar{min-height:60px;height:60px}.product-shell:has(.system-console) .product-topbar>div:first-child>strong{font-size:24px}}
</style>
