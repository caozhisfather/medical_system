<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { BookOpenCheck, Copy, FilePenLine, Plus, Search, ShieldAlert } from '@lucide/vue';
import { trainingStore } from '../stores/training';

const query = ref('');
const selectedId = ref('emergency_chest_pain');
onMounted(() => trainingStore.loadCases());
const filtered = computed(() => trainingStore.state.cases.filter((item) => !query.value || [item.title, item.department, item.chief_complaint].join(' ').includes(query.value)));
const selected = computed(() => trainingStore.state.cases.find((item) => item.id === selectedId.value) ?? trainingStore.state.cases[0]);
</script>

<template>
  <div class="workspace-page">
    <section class="page-title-row">
      <div><span class="section-kicker">教学内容资产</span><h1>病例库管理</h1><p>检查脚本、评分规则、高风险扣分项和指南证据后发布训练。</p></div>
      <button class="button-primary" type="button"><Plus :size="17" /> 新建病例</button>
    </section>
    <div class="teacher-case-layout">
      <section class="case-management-list">
        <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="搜索病例" /></label>
        <button v-for="item in filtered" :key="item.id" type="button" :class="{ active: selectedId === item.id }" @click="selectedId = item.id">
          <span><strong>{{ item.title }}</strong><small>{{ item.department }} · {{ item.difficulty }}</small></span><b>已发布</b>
        </button>
      </section>
      <section class="case-editor">
        <header><div><span class="section-kicker">病例脚本预览</span><h2>{{ selected.title }}</h2><p>{{ selected.patient_profile_text }}</p></div><div><button class="button-secondary" type="button"><Copy :size="16" /> 复制</button><button class="button-primary" type="button"><FilePenLine :size="16" /> 编辑</button></div></header>
        <div class="editor-section"><h3>病例基本信息</h3><dl><dt>主诉</dt><dd>{{ selected.chief_complaint }}</dd><dt>现病史</dt><dd>{{ selected.present_illness }}</dd><dt>既往史</dt><dd>{{ selected.past_history }}</dd><dt>查体</dt><dd>{{ selected.physical_exam }}</dd></dl></div>
        <div class="editor-columns">
          <div class="editor-section"><h3><BookOpenCheck :size="17" /> 关键得分点</h3><p v-for="item in selected.key_scoring_points" :key="item">{{ item }}</p></div>
          <div class="editor-section risk"><h3><ShieldAlert :size="17" /> 高风险扣分项</h3><p v-for="item in selected.high_risk_omissions" :key="item.id">{{ item.text }}</p></div>
        </div>
        <div class="editor-columns">
          <div class="editor-section"><h3>鉴别诊断</h3><div class="tag-cloud"><span v-for="item in selected.differential_diagnoses" :key="item">{{ item }}</span></div></div>
          <div class="editor-section"><h3>指南证据</h3><div class="tag-cloud evidence"><span v-for="item in selected.recommended_guidelines" :key="item">{{ item }}</span></div></div>
        </div>
        <div class="editor-section"><h3>标准化病人回答约束</h3><p>患者仅根据病例脚本回答，不主动泄露最终诊断；超出脚本的信息明确表示“不清楚”。</p><small>当前脚本包含 {{ selected.script?.answers?.length ?? 0 }} 组结构化回答。</small></div>
      </section>
    </div>
  </div>
</template>

