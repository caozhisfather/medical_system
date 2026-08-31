<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Activity, ArrowRight, Brain, ChevronDown, Dices, Droplets, Eye, HeartPulse, Microscope, RotateCcw, Search, ShieldAlert, SlidersHorizontal, Sparkles, Stethoscope, Syringe, Timer, Trophy, UsersRound, X } from '@lucide/vue';
import { getRandomCase } from '../api';
import { trainingStore } from '../stores/training';
import type { CaseSummary } from '../types';

const router = useRouter();
const query = ref('');
const activeCategory = ref('all');
const department = ref('全部科室');
const symptom = ref('全部症状');
const difficulty = ref('全部难度');
const trainingGoal = ref('全部目标');
const randomLoading = ref(false);
const expandedGroupIds = ref<string[]>(['emergency']);
const previewCase = ref<CaseSummary | null>(null);

const caseCategories = [
  { id: 'emergency', label: '急诊与危重症', description: '急性症状、风险识别与优先处置', departments: ['急诊医学'], icon: Stethoscope },
  { id: 'cardiopulmonary', label: '心肺系统', description: '循环与呼吸系统常见问题', departments: ['心血管内科', '呼吸与危重症医学科'], icon: HeartPulse },
  { id: 'digestive-infection', label: '消化与感染', description: '消化系统疾病与感染性问题', departments: ['消化内科', '感染科'], icon: Microscope },
  { id: 'neuro-metabolic', label: '神经与代谢', description: '神经、内分泌及血液系统', departments: ['神经内科', '内分泌科', '血液内科'], icon: Brain },
  { id: 'renal-urinary', label: '肾脏与泌尿', description: '肾功能、尿路感染与梗阻', departments: ['肾内科', '泌尿外科'], icon: Droplets },
  { id: 'surgery', label: '外科与骨科', description: '外科急症、围术期与运动系统', departments: ['普通外科', '外科', '骨科'], icon: Syringe },
  { id: 'comprehensive', label: '妇儿与综合', description: '妇产、儿科、老年、全科及其他专科', departments: ['儿科', '妇产科', '老年医学科', '全科医学科'], icon: UsersRound }
];

function categoryIdFor(departmentName: string) {
  return caseCategories.find((category) => category.departments.includes(departmentName))?.id ?? 'comprehensive';
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') previewCase.value = null;
}

onMounted(() => {
  trainingStore.loadCases();
  window.addEventListener('keydown', handleKeydown);
});
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown));

const departments = computed(() => ['全部科室', ...new Set(trainingStore.state.cases.map((item) => item.department))]);
const symptoms = computed(() => ['全部症状', ...new Set(trainingStore.state.cases.flatMap((item) => item.symptom_tags ?? []))]);
const goals = computed(() => ['全部目标', ...new Set(trainingStore.state.cases.flatMap((item) => item.training_goals ?? []).slice(0, 24))]);
const filteredByControls = computed(() => trainingStore.state.cases.filter((item) => {
  const textMatch = !query.value || [item.title, item.title_en, item.chief_complaint, item.department, ...(item.symptom_tags ?? [])].join(' ').toLowerCase().includes(query.value.toLowerCase());
  const departmentMatch = department.value === '全部科室' || item.department === department.value;
  const symptomMatch = symptom.value === '全部症状' || item.symptom_tags?.includes(symptom.value);
  const difficultyMatch = difficulty.value === '全部难度' || item.difficulty === difficulty.value;
  const goalMatch = trainingGoal.value === '全部目标' || item.training_goals?.includes(trainingGoal.value);
  return textMatch && departmentMatch && symptomMatch && difficultyMatch && goalMatch;
}));
const filtered = computed(() => activeCategory.value === 'all'
  ? filteredByControls.value
  : filteredByControls.value.filter((item) => categoryIdFor(item.department) === activeCategory.value)
);
const categoryCounts = computed(() => Object.fromEntries(caseCategories.map((category) => [
  category.id,
  filteredByControls.value.filter((item) => categoryIdFor(item.department) === category.id).length
])));
const groupedCases = computed(() => caseCategories
  .filter((category) => activeCategory.value === 'all' || category.id === activeCategory.value)
  .map((category) => ({ ...category, items: filtered.value.filter((item) => categoryIdFor(item.department) === category.id) }))
  .filter((category) => category.items.length)
);
const caseProgressById = computed(() => Object.fromEntries(trainingStore.state.cases.map((item) => {
  const reports = trainingStore.state.history.filter((report) => report.caseId === item.id);
  const bestScore = reports.length ? Math.max(...reports.map((report) => report.score)) : null;
  const latest = reports[0];
  if (trainingStore.state.session?.caseId === item.id) {
    return [item.id, { label: '训练中', tone: 'active', attempts: reports.length, bestScore }];
  }
  if (!latest) return [item.id, { label: '未训练', tone: 'new', attempts: 0, bestScore: null }];
  if (latest.score < 80) return [item.id, { label: '建议复训', tone: 'review', attempts: reports.length, bestScore }];
  return [item.id, { label: '已完成', tone: 'done', attempts: reports.length, bestScore }];
})));

function progressFor(caseId: string) {
  return caseProgressById.value[caseId] ?? { label: '未训练', tone: 'new', attempts: 0, bestScore: null };
}

function completedCount(items: CaseSummary[]) {
  return items.filter((item) => progressFor(item.id).attempts > 0).length;
}

function isGroupExpanded(groupId: string) {
  return expandedGroupIds.value.includes(groupId);
}

function toggleGroup(groupId: string) {
  expandedGroupIds.value = isGroupExpanded(groupId) ? [] : [groupId];
}

function selectCategory(categoryId: string) {
  activeCategory.value = categoryId;
  if (categoryId !== 'all' && !isGroupExpanded(categoryId)) {
    expandedGroupIds.value = [categoryId];
  }
}

function startCase(item: CaseSummary) {
  previewCase.value = null;
  return router.push({ path: '/student/case/new', query: { case: item.id } });
}

watch(groupedCases, (groups) => {
  if (groups.length && !groups.some((group) => isGroupExpanded(group.id))) {
    expandedGroupIds.value = [groups[0].id];
  }
}, { immediate: true });
const todayCases = computed(() => trainingStore.state.cases.filter((_, index) => index % 11 === 0).slice(0, 3));
const retrainingCases = computed(() => trainingStore.state.history.slice(0, 3).map((report) => trainingStore.state.cases.find((item) => item.id === report.caseId)).filter(Boolean));
const similarCases = computed(() => {
  const active = filtered.value[0] ?? trainingStore.state.cases[0];
  return trainingStore.state.cases.filter((item) => item.id !== active?.id && (item.department === active?.department || item.symptom_tags?.some((tag) => active?.symptom_tags?.includes(tag)))).slice(0, 3);
});
const recommendationShortcuts = computed(() => {
  const candidates = [
    ...todayCases.value.slice(0, 1).map((item) => ({ item, label: '今日推荐' })),
    ...retrainingCases.value.slice(0, 1).map((item) => ({ item: item!, label: '错题复训' })),
    ...similarCases.value.slice(0, 1).map((item) => ({ item, label: '相似病例' }))
  ];
  return candidates.filter((entry, index) => candidates.findIndex((candidate) => candidate.item.id === entry.item.id) === index);
});

function resetFilters() {
  query.value = '';
  activeCategory.value = 'all';
  department.value = '全部科室';
  symptom.value = '全部症状';
  difficulty.value = '全部难度';
  trainingGoal.value = '全部目标';
  expandedGroupIds.value = ['emergency'];
}

async function randomCase() {
  if (randomLoading.value) return;
  randomLoading.value = true;
  if (activeCategory.value !== 'all') {
    const item = filtered.value[Math.floor(Math.random() * filtered.value.length)];
    randomLoading.value = false;
    if (item) await router.push({ path: '/student/case/new', query: { case: item.id, variant: 'A' } });
    return;
  }
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
      <div><span class="section-kicker">{{ trainingStore.state.cases.length }} 个合成虚拟教学病例</span><h1>病例训练库</h1><p>按临床系统选择病例，训练问诊、危险鉴别、检查选择和证据引用。</p></div>
      <button class="button-primary" type="button" :disabled="randomLoading" @click="randomCase"><Dices :size="18" /> {{ randomLoading ? '正在抽取' : '随机病例训练' }}</button>
    </section>

    <section class="recommendation-strip" aria-label="病例推荐">
      <span><Sparkles :size="16" />训练建议</span>
      <button v-for="entry in recommendationShortcuts" :key="entry.item.id" type="button" @click="router.push({ path: '/student/case/new', query: { case: entry.item.id } })"><small>{{ entry.label }}</small><strong>{{ entry.item.title }}</strong><ArrowRight :size="15" /></button>
    </section>

    <nav class="case-category-nav" aria-label="病例临床大类">
      <button type="button" :class="{ active: activeCategory === 'all' }" @click="selectCategory('all')"><Activity :size="18" /><span><strong>全部病例</strong><small>{{ filteredByControls.length }} 例</small></span></button>
      <button v-for="category in caseCategories" :key="category.id" type="button" :class="{ active: activeCategory === category.id }" :disabled="!categoryCounts[category.id]" @click="selectCategory(category.id)"><component :is="category.icon" :size="18" /><span><strong>{{ category.label }}</strong><small>{{ categoryCounts[category.id] }} 例</small></span></button>
    </nav>

    <section class="filter-workbench">
      <label class="search-control"><Search :size="18" /><input v-model="query" placeholder="搜索症状、病例、科室或英文名称" /></label>
       <label><Stethoscope :size="17" /><select v-model="department" aria-label="按科室筛选"><option v-for="item in departments" :key="item">{{ item }}</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="symptom" aria-label="按症状筛选"><option v-for="item in symptoms" :key="item">{{ item }}</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="difficulty" aria-label="按难度筛选"><option>全部难度</option><option>入门</option><option>进阶</option><option>高阶</option></select></label>
      <label><SlidersHorizontal :size="17" /><select v-model="trainingGoal" aria-label="按训练目标筛选"><option v-for="item in goals" :key="item">{{ item }}</option></select></label>
      <button class="filter-reset" type="button" title="重置筛选" @click="resetFilters"><RotateCcw :size="17" /></button>
      <strong>{{ filtered.length }} / {{ trainingStore.state.cases.length }} 例</strong>
    </section>

    <div class="case-category-sections">
      <section v-for="group in groupedCases" :key="group.id" class="case-category-section" :class="{ collapsed: !isGroupExpanded(group.id) }">
        <header>
          <button class="case-category-toggle" type="button" :aria-expanded="isGroupExpanded(group.id)" :aria-controls="`case-group-${group.id}`" @click="toggleGroup(group.id)">
            <div class="case-category-title"><span><component :is="group.icon" :size="20" /></span><div><h2>{{ group.label }}</h2><p>{{ group.description }} · {{ group.departments.join('、') }}</p></div></div>
            <span class="case-category-count"><strong>{{ group.items.length }} 例</strong><small>已训练 {{ completedCount(group.items) }} 例</small><small>{{ isGroupExpanded(group.id) ? '收起' : '展开' }}</small><ChevronDown :size="18" /></span>
          </button>
        </header>
        <div v-show="isGroupExpanded(group.id)" :id="`case-group-${group.id}`" class="case-category-grid">
          <article v-for="item in group.items" :key="item.id" class="case-compact-card">
            <div class="case-compact-meta"><span>{{ item.department }}</span><small>{{ item.difficulty }} · <Timer :size="13" />{{ item.recommended_minutes ?? 20 }} 分钟</small></div>
            <div class="case-card-progress"><span :class="`status-${progressFor(item.id).tone}`">{{ progressFor(item.id).label }}</span><small v-if="progressFor(item.id).bestScore !== null"><Trophy :size="12" />最高 {{ progressFor(item.id).bestScore }} 分</small></div>
            <h3>{{ item.title }}</h3>
            <p class="case-chief-complaint"><b>主诉</b>{{ item.chief_complaint }}</p>
            <footer><button class="case-preview-button" type="button" @click="previewCase = item"><Eye :size="15" />快速预览</button><button class="case-start-button" type="button" @click="startCase(item)">{{ progressFor(item.id).attempts ? '再次训练' : '开始训练' }}<ArrowRight :size="16" /></button></footer>
          </article>
        </div>
      </section>
      <div v-if="!filtered.length" class="empty-state"><strong>没有匹配病例</strong><span>调整临床大类、科室、症状或训练目标后重试。</span><button type="button" @click="resetFilters">清除筛选</button></div>
    </div>

    <Teleport to="body">
      <div v-if="previewCase" class="case-preview-backdrop" @click.self="previewCase = null">
        <aside class="case-preview-drawer" role="dialog" aria-modal="true" :aria-labelledby="`preview-title-${previewCase.id}`">
          <header>
            <div><span class="section-kicker">病例快速预览</span><h2 :id="`preview-title-${previewCase.id}`">{{ previewCase.title }}</h2><p v-if="previewCase.title_en">{{ previewCase.title_en }}</p></div>
            <button type="button" aria-label="关闭病例预览" @click="previewCase = null"><X :size="20" /></button>
          </header>
          <div class="case-preview-body">
            <div class="case-preview-status">
              <span :class="`status-${progressFor(previewCase.id).tone}`">{{ progressFor(previewCase.id).label }}</span>
              <strong v-if="progressFor(previewCase.id).bestScore !== null"><Trophy :size="16" />历史最高 {{ progressFor(previewCase.id).bestScore }} 分</strong>
              <small>{{ progressFor(previewCase.id).attempts }} 次完成记录</small>
            </div>
            <dl class="case-preview-facts">
              <div><dt>所属科室</dt><dd>{{ previewCase.department }}</dd></div>
              <div><dt>训练难度</dt><dd>{{ previewCase.difficulty }}</dd></div>
              <div><dt>建议时长</dt><dd>{{ previewCase.recommended_minutes ?? 20 }} 分钟</dd></div>
              <div><dt>病例变体</dt><dd>{{ previewCase.case_variants?.length ?? 1 }} 个</dd></div>
            </dl>
            <section><h3>患者主诉</h3><p>{{ previewCase.chief_complaint }}</p></section>
            <section><h3>训练重点</h3><div class="case-preview-tags"><span v-for="goal in (previewCase.training_goals ?? previewCase.key_scoring_points ?? []).slice(0, 5)" :key="goal">{{ goal }}</span></div></section>
            <section class="case-preview-risk"><h3><ShieldAlert :size="17" />风险训练</h3><p>本病例包含 {{ previewCase.high_risk_misses?.length ?? previewCase.high_risk_omissions?.length ?? 0 }} 个高风险漏诊检查点，训练过程中不会提前显示诊断答案。</p></section>
          </div>
          <footer><button type="button" class="button-secondary" @click="previewCase = null">继续浏览</button><button type="button" class="button-primary" @click="startCase(previewCase)">{{ progressFor(previewCase.id).attempts ? '开始复训' : '开始训练' }}<ArrowRight :size="17" /></button></footer>
        </aside>
      </div>
    </Teleport>
  </div>
</template>
