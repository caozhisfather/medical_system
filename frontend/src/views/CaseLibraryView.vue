<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight, Dices, Filter, RotateCcw, Search, ShieldAlert, SlidersHorizontal, Sparkles, Timer } from '@lucide/vue';
import { getRandomCase } from '../api';
import { trainingStore } from '../stores/training';

const router = useRouter();
const query = ref('');
const department = ref('全部科室');
const symptom = ref('全部症状');
const difficulty = ref('全部难度');
const trainingGoal = ref('全部目标');
const randomLoading = ref(false);

onMounted(() => trainingStore.loadCases());

const departments = computed(() => ['全部科室', ...new Set(trainingStore.state.cases.map((item) => item.department))]);
const symptoms = computed(() => ['全部症状', ...new Set(trainingStore.state.cases.flatMap((item) => item.symptom_tags ?? []))]);
const goals = computed(() => ['全部目标', ...new Set(trainingStore.state.cases.flatMap((item) => item.training_goals ?? []).slice(0, 24))]);
const filtered = computed(() => trainingStore.state.cases.filter((item) => {
  const textMatch = !query.value || [item.title, item.title_en, item.chief_complaint, item.department, ...(item.symptom_tags ?? [])].join(' ').toLowerCase().includes(query.value.toLowerCase());
  const departmentMatch = department.value === '全部科室' || item.department === department.value;
  const symptomMatch = symptom.value === '全部症状' || item.symptom_tags?.includes(symptom.value);
  const difficultyMatch = difficulty.value === '全部难度' || item.difficulty === difficulty.value;
  const goalMatch = trainingGoal.value === '全部目标' || item.training_goals?.includes(trainingGoal.value);
  return textMatch && departmentMatch && symptomMatch && difficultyMatch && goalMatch;
}));
const todayCases = computed(() => trainingStore.state.cases.filter((_, index) => index % 11 === 0).slice(0, 3));
const retrainingCases = computed(() => trainingStore.state.history.slice(0, 3).map((report) => trainingStore.state.cases.find((item) => item.id === report.caseId)).filter(Boolean));
const similarCases = computed(() => {
  const active = filtered.value[0] ?? trainingStore.state.cases[0];
  return trainingStore.state.cases.filter((item) => item.id !== active?.id && (item.department === active?.department || item.symptom_tags?.some((tag) => active?.symptom_tags?.includes(tag)))).slice(0, 3);
});

function resetFilters() {
  query.value = '';
  department.value = '全部科室';
  symptom.value = '全部症状';
  difficulty.value = '全部难度';
  trainingGoal.value = '全部目标';
}

async function randomCase() {
  if (randomLoading.value) return;
  randomLoading.value = true;
  try {
    const item = await getRandomCase({
      department: department.value === '全部科室' ? '' : department.value,
      symptom: symptom.value === '全部症状' ? '' : symptom.value,
      difficulty: difficulty.value === '全部难度' ? '' : difficulty.value,
      training_goal: trainingGoal.value === '全部目标' ? '' : trainingGoal.value
    });
    await router.push({ path: '/student/case/new', query: { case: item.id, variant: item.active_variant ?? 'A' } });
  } catch {
    const candidates = filtered.value.length ? filtered.value : trainingStore.state.cases;
    const item = candidates[Math.floor(Math.random() * candidates.length)];
    if (item) await router.push({ path: '/student/case/new', query: { case: item.id, variant: 'A' } });
  } finally {
    randomLoading.value = false;
  }
}
</script>

<template>
  <div class="workspace-page case-library-page">
    <section class="page-title-row case-library-heading">
      <div><span class="section-kicker">41 个合成虚拟教学病例</span><h1>病例训练库</h1><p>从症状切入，训练问诊、危险鉴别、检查选择和证据引用。每例均有独立脚本与评分规则。</p></div>
      <button class="button-primary" type="button" :disabled="randomLoading" @click="randomCase"><Dices :size="18" /> {{ randomLoading ? '正在抽取' : '随机病例训练' }}</button>
    </section>

    <section class="recommendation-band" aria-label="病例推荐">
      <div>
        <span><Sparkles :size="16" /> 今日推荐</span>
        <button v-for="item in todayCases" :key="item.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: item.id } })">{{ item.title }}<small>{{ item.department }}</small></button>
      </div>
      <div>
        <span><RotateCcw :size="16" /> 错题复训</span>
        <button v-for="item in retrainingCases" :key="item!.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: item!.id } })">{{ item!.title }}<small>根据历史训练推荐</small></button>
      </div>
      <div>
        <span><ArrowRight :size="16" /> 相似病例</span>
        <button v-for="item in similarCases" :key="item.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: item.id } })">{{ item.title }}<small>{{ item.specialty }}</small></button>
      </div>
    </section>

    <section class="filter-workbench">
      <label class="search-control"><Search :size="18" /><input v-model="query" placeholder="搜索症状、病例、科室或英文名称" /></label>
      <label><Filter :size="17" /><select v-model="department" aria-label="按科室筛选"><option v-for="item in departments" :key="item">{{ item }}</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="symptom" aria-label="按症状筛选"><option v-for="item in symptoms" :key="item">{{ item }}</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="difficulty" aria-label="按难度筛选"><option>全部难度</option><option>入门</option><option>进阶</option><option>高阶</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="trainingGoal" aria-label="按训练目标筛选"><option v-for="item in goals" :key="item">{{ item }}</option></select></label>
      <button class="filter-reset" type="button" title="重置筛选" @click="resetFilters"><RotateCcw :size="17" /></button>
      <strong>{{ filtered.length }} / {{ trainingStore.state.cases.length }} 例</strong>
    </section>

    <section class="case-library-grid">
      <article v-for="(item, index) in filtered" :key="item.id" class="case-library-card">
        <div class="case-card-visual" :class="`clinical-tone-${index % 4}`">
          <span>{{ item.department }} · {{ item.specialty }}</span>
          <b>{{ String(index + 1).padStart(2, '0') }}</b>
          <div class="ecg-line"></div>
        </div>
        <div class="case-card-body">
          <div class="case-card-meta"><span>{{ item.difficulty }}</span><span><Timer :size="14" /> {{ item.recommended_minutes ?? 20 }} 分钟</span></div>
          <h2>{{ item.title }}</h2>
          <p>{{ item.patient_profile_text }}</p>
          <dl><dt>主诉</dt><dd>{{ item.chief_complaint }}</dd><dt>训练重点</dt><dd>{{ (item.training_goals ?? item.key_scoring_points ?? []).slice(0, 2).join('、') }}</dd></dl>
          <div class="case-risk-row"><span><ShieldAlert :size="15" /> {{ item.high_risk_misses?.length ?? item.high_risk_omissions?.length ?? 0 }} 个高风险点</span><span>{{ item.completion_status ?? '未训练' }}</span></div>
          <button type="button" @click="router.push({ path: '/student/case/new', query: { case: item.id } })">选择病例与变体 <ArrowRight :size="17" /></button>
        </div>
      </article>
      <div v-if="!filtered.length" class="empty-state"><strong>没有匹配病例</strong><span>调整科室、症状或训练目标后重试。</span><button type="button" @click="resetFilters">清除筛选</button></div>
    </section>
  </div>
</template>
