<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import {
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  Bot,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FilePenLine,
  GitBranch,
  LoaderCircle,
  Pencil,
  Plus,
  RotateCcw,
  Save,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  X
} from '@lucide/vue';
import {
  decideTeacherCaseDraft,
  decideTeacherCaseRecommendation,
  compileCaseLibraryEntries,
  editTeacherCaseDraft,
  generateTeacherCaseDraft,
  getTeacherCaseDrafts,
  getTeacherCaseRecommendations
} from '../api';
import { trainingStore } from '../stores/training';
import type { CaseSummary, TeacherCaseDraft, TeacherCaseRecommendation, TeacherCaseRecommendations } from '../types';
import CaseKnowledgePanel from './TeacherCaseLibraryView.vue';

interface ManagedRecord {
  id: string;
  kind: 'draft' | 'published';
  status: string;
  caseData: CaseSummary;
  draft?: TeacherCaseDraft;
}

const blankBuilder = () => ({
  title: '',
  department: '急诊医学',
  chief_complaint: '',
  learning_goal: '',
  difficulty: '进阶',
  suspected_diagnosis: '',
  source_summary: '',
  recommendation_id: ''
});

const activeTab = ref<'assets' | 'recommendations' | 'knowledge'>('assets');
const route = useRoute();
const detailTab = ref<'content' | 'workflow'>('content');
const query = ref('');
const listFilter = ref<'all' | 'draft' | 'published'>('all');
const selectedId = ref('emergency_chest_pain');
const drafts = ref<TeacherCaseDraft[]>([]);
const recommendationData = ref<TeacherCaseRecommendations | null>(null);
const showBuilder = ref(false);
const builder = ref(blankBuilder());
const generating = ref(false);
const editing = ref(false);
const saving = ref(false);
const deciding = ref(false);
const compilingKnowledge = ref(false);
const decisionNote = ref('');
const notice = ref('');
const editForm = ref({ title: '', department: '', chief_complaint: '', difficulty: '进阶', suspected_diagnosis: '', present_illness: '', learning_goal: '', teacher_note: '' });

onMounted(async () => {
  if (route.query.tab === 'recommendations') activeTab.value = 'recommendations';
  else if (route.query.tab === 'knowledge') activeTab.value = 'knowledge';
  await trainingStore.loadCases();
  try {
    const [draftItems, recommendations] = await Promise.all([getTeacherCaseDrafts(), getTeacherCaseRecommendations()]);
    drafts.value = draftItems;
    recommendationData.value = recommendations;
    if (draftItems.length) selectedId.value = draftItems[0].draft_id;
  } catch {
    notice.value = '教师 AI 工作流暂时不可用，已保留已发布病例浏览功能。';
  }
});

async function compileKnowledgeEntries(payload: { entry_ids: string[]; publish_immediately: boolean }) {
  compilingKnowledge.value = true;
  try {
    const draft = await compileCaseLibraryEntries(payload);
    replaceDraft(draft);
    activeTab.value = 'assets';
    if (payload.publish_immediately) await trainingStore.refreshCases();
    notice.value = payload.publish_immediately ? 'AI 已整合知识库病例并直接发布到学生病例库。' : 'AI 已完成知识库整合草稿，等待教师编辑与最终决策。';
  } catch {
    notice.value = '知识库整合失败，请检查后端服务。';
  } finally {
    compilingKnowledge.value = false;
  }
}

const managedRecords = computed<ManagedRecord[]>(() => {
  const draftIds = new Set(drafts.value.map((item) => item.draft_id));
  const draftRecords = drafts.value.map((item) => ({ id: item.draft_id, kind: 'draft' as const, status: item.case.review_status, caseData: item.case, draft: item }));
  const publishedRecords = trainingStore.state.cases.filter((item) => !draftIds.has(item.id)).map((item) => ({ id: item.id, kind: 'published' as const, status: '已发布', caseData: item }));
  return [...draftRecords, ...publishedRecords];
});
const filteredRecords = computed(() => managedRecords.value.filter((record) => {
  const typeMatch = listFilter.value === 'all' || record.kind === listFilter.value;
  const textMatch = !query.value || [record.caseData.title, record.caseData.department, record.caseData.chief_complaint].join(' ').includes(query.value);
  return typeMatch && textMatch;
}));
const selectedRecord = computed(() => managedRecords.value.find((item) => item.id === selectedId.value) ?? managedRecords.value[0]);
const selected = computed(() => selectedRecord.value?.caseData);
const pendingCount = computed(() => drafts.value.filter((item) => ['待教师审核', '退回修改'].includes(item.case.review_status)).length);

function replaceDraft(updated: TeacherCaseDraft) {
  const index = drafts.value.findIndex((item) => item.draft_id === updated.draft_id);
  if (index >= 0) drafts.value[index] = updated;
  else drafts.value.unshift(updated);
  selectedId.value = updated.draft_id;
}

function openBuilder(prefill?: TeacherCaseRecommendation) {
  builder.value = prefill ? { ...blankBuilder(), ...prefill.suggested_case, source_summary: prefill.reason, recommendation_id: prefill.id } : blankBuilder();
  showBuilder.value = true;
  notice.value = '';
}

async function generateDraft() {
  if (!builder.value.title.trim() || !builder.value.chief_complaint.trim() || !builder.value.learning_goal.trim()) {
    notice.value = '请填写病例名称、主诉和核心学习目标。';
    return;
  }
  generating.value = true;
  try {
    const draft = await generateTeacherCaseDraft({ ...builder.value, recommendation_id: builder.value.recommendation_id || undefined });
    replaceDraft(draft);
    activeTab.value = 'assets';
    showBuilder.value = false;
    notice.value = 'AI 已完成病例草稿和 Agent 工作流，等待教师编辑与最终决策。';
  } catch {
    notice.value = '病例草稿生成失败，请检查后端服务。';
  } finally {
    generating.value = false;
  }
}

function beginEdit() {
  if (!selected.value) return;
  editForm.value = {
    title: selected.value.title,
    department: selected.value.department,
    chief_complaint: selected.value.chief_complaint,
    difficulty: selected.value.difficulty,
    suspected_diagnosis: selected.value.hidden_final_diagnosis ?? '',
    present_illness: selected.value.present_illness ?? selected.value.history?.present_illness?.join('；') ?? '',
    learning_goal: selected.value.training_goals?.[0] ?? selected.value.learning_goals?.[0] ?? '',
    teacher_note: selectedRecord.value?.draft?.case.teacher_note ?? ''
  };
  editing.value = true;
}

async function saveEdit() {
  if (!selectedRecord.value) return;
  saving.value = true;
  try {
    if (selectedRecord.value.kind === 'draft') {
      replaceDraft(await editTeacherCaseDraft(selectedRecord.value.id, editForm.value));
      notice.value = '病例草稿已保存，等待教师最终决策。';
    } else {
      const draft = await generateTeacherCaseDraft({
        title: editForm.value.title,
        department: editForm.value.department,
        chief_complaint: editForm.value.chief_complaint,
        learning_goal: editForm.value.learning_goal,
        difficulty: editForm.value.difficulty,
        suspected_diagnosis: editForm.value.suspected_diagnosis,
        source_summary: editForm.value.present_illness
      });
      replaceDraft(draft);
      notice.value = '已基于已发布病例创建修订草稿，原病例未被直接覆盖。';
    }
    editing.value = false;
  } catch {
    notice.value = '保存失败，请稍后重试。';
  } finally {
    saving.value = false;
  }
}

async function decideCase(action: 'approve' | 'reject' | 'request_revision') {
  if (!selectedRecord.value?.draft) return;
  deciding.value = true;
  try {
    const updated = await decideTeacherCaseDraft(selectedRecord.value.id, action, decisionNote.value.trim());
    replaceDraft(updated);
    decisionNote.value = '';
    if (action === 'approve') await trainingStore.refreshCases();
    notice.value = action === 'approve' ? '教师已批准，病例已加入学生病例库。' : action === 'reject' ? '病例已拒绝并保留审核记录。' : '病例已退回修改。';
  } catch {
    notice.value = '教师决策提交失败，或病例校验尚未通过。';
  } finally {
    deciding.value = false;
  }
}

async function acceptRecommendation(item: TeacherCaseRecommendation) {
  await decideTeacherCaseRecommendation(item.id, 'accept');
  item.decision = { action: 'accept', note: '' };
  openBuilder(item);
}

async function dismissRecommendation(item: TeacherCaseRecommendation) {
  await decideTeacherCaseRecommendation(item.id, 'dismiss');
  item.decision = { action: 'dismiss', note: '' };
}

function statusClass(status: string) {
  return { approved: status === '已批准' || status === '已发布', rejected: status === '已拒绝', revision: status === '退回修改', pending: status === '待教师审核' };
}
</script>

<template>
  <div class="workspace-page teacher-case-page">
    <section class="page-title-row teacher-case-heading">
      <div><span class="section-kicker">教师决策驱动 · AI 辅助生成</span><h1>病例智能工作台</h1><p>后台 Agent 分析学生训练结果并生成候选病例，教师负责编辑、复核和最终发布。</p></div>
      <button class="button-primary" type="button" @click="openBuilder()"><Plus :size="17" /> AI 辅助新建病例</button>
    </section>

    <div v-if="notice" class="teacher-case-notice"><CheckCircle2 :size="17" />{{ notice }}<button type="button" title="关闭" @click="notice = ''"><X :size="15" /></button></div>

    <nav class="teacher-case-tabs" aria-label="病例智能工作台视图">
      <button type="button" :class="{ active: activeTab === 'assets' }" @click="activeTab = 'assets'"><ClipboardCheck :size="17" />训练病例审核<span>{{ pendingCount }} 待决策</span></button>
      <button type="button" :class="{ active: activeTab === 'recommendations' }" @click="activeTab = 'recommendations'"><BarChart3 :size="17" />学情推荐<span>{{ recommendationData?.recommendations.length ?? 0 }} 条建议</span></button>
      <button type="button" :class="{ active: activeTab === 'knowledge' }" @click="activeTab = 'knowledge'"><Database :size="17" />教学知识库<span>素材沉淀 · AI 整合</span></button>
    </nav>

    <section v-if="showBuilder" class="ai-case-builder">
      <header><div><span><Bot :size="20" /></span><div><strong>AI 病例生成任务</strong><small>{{ builder.recommendation_id ? '已带入学情推荐，教师可编辑后再生成' : '填写教学意图，Agent 自动补全脚本、评分规则与安全约束' }}</small></div></div><button class="icon-button" type="button" title="关闭" @click="showBuilder = false"><X :size="18" /></button></header>
      <div class="ai-builder-layout">
        <form @submit.prevent="generateDraft">
          <div v-if="builder.recommendation_id" class="builder-prefill-note"><Sparkles :size="16" /><span><strong>AI 学情预填</strong><small>病例名称、主诉、学习目标和推荐理由已自动带入，请确认后生成。</small></span></div>
          <label>病例名称<input v-model="builder.title" placeholder="例如：突发胸背痛的高风险鉴别" /></label>
          <div><label>科室<input v-model="builder.department" /></label><label>难度<select v-model="builder.difficulty"><option>入门</option><option>进阶</option><option>高阶</option></select></label></div>
          <label>患者主诉<input v-model="builder.chief_complaint" placeholder="症状与持续时间" /></label>
          <label>核心学习目标<textarea v-model="builder.learning_goal" rows="2" placeholder="希望学生重点训练的能力" /></label>
          <label>候选诊断<input v-model="builder.suspected_diagnosis" placeholder="由教师后续确认" /></label>
          <label>病例素材摘要<textarea v-model="builder.source_summary" rows="3" placeholder="仅填写去标识化或合成教学信息，不得录入真实患者隐私" /></label>
          <button class="button-primary" type="submit" :disabled="generating"><LoaderCircle v-if="generating" class="spin" :size="17" /><Bot v-else :size="17" />{{ generating ? 'Agent 工作流运行中' : '生成候选病例' }}</button>
        </form>
        <aside>
          <div class="builder-analysis"><Sparkles :size="18" /><span><strong>学情输入</strong><small>基于 {{ recommendationData?.analysis.training_sessions ?? 0 }} 次训练、班级均分 {{ recommendationData?.analysis.class_average ?? 0 }}</small></span></div>
          <ol>
            <li><span><BarChart3 :size="15" /></span><div><strong>LearningAnalyticsAgent</strong><small>分析共性遗漏与薄弱能力</small></div></li>
            <li><span><GitBranch :size="15" /></span><div><strong>CaseDesignerAgent</strong><small>生成病例结构与教学目标</small></div></li>
            <li><span><Bot :size="15" /></span><div><strong>PatientScriptAgent</strong><small>生成受事实约束的病人脚本</small></div></li>
            <li><span><ShieldCheck :size="15" /></span><div><strong>Scoring + Safety Agent</strong><small>构建评分规则并检查安全边界</small></div></li>
            <li class="human-gate"><span><ClipboardCheck :size="15" /></span><div><strong>教师审核门</strong><small>AI 不会自动发布，最终由教师决定</small></div></li>
          </ol>
        </aside>
      </div>
    </section>

    <div v-if="activeTab === 'assets'" class="teacher-case-layout teacher-case-workspace">
      <section class="case-management-list">
        <label class="search-control"><Search :size="17" /><input v-model="query" placeholder="搜索病例或科室" /></label>
        <div class="case-list-tabs"><button type="button" :class="{ active: listFilter === 'all' }" @click="listFilter = 'all'">全部</button><button type="button" :class="{ active: listFilter === 'draft' }" @click="listFilter = 'draft'">AI 草稿</button><button type="button" :class="{ active: listFilter === 'published' }" @click="listFilter = 'published'">已发布</button></div>
        <div class="case-management-scroll">
          <button v-for="record in filteredRecords" :key="record.id" type="button" :class="{ active: selectedId === record.id }" @click="selectedId = record.id; editing = false; detailTab = 'content'">
            <span><strong>{{ record.caseData.title }}</strong><small>{{ record.caseData.department }} · {{ record.caseData.difficulty }}</small></span><b :class="statusClass(record.status)">{{ record.status }}</b>
          </button>
        </div>
      </section>

      <section v-if="selected" class="case-editor teacher-case-editor">
        <header><div><span class="section-kicker">{{ selectedRecord?.kind === 'draft' ? 'AI 候选病例' : '已发布教学病例' }}</span><h2>{{ selected.title }}</h2><p>{{ selected.department }} · {{ selected.specialty }}</p></div><div><button v-if="!editing" class="button-primary" type="button" @click="beginEdit"><FilePenLine :size="16" />{{ selectedRecord?.kind === 'draft' ? '编辑草稿' : '创建修订版' }}</button></div></header>

        <nav class="teacher-detail-tabs" aria-label="病例详情视图"><button type="button" :class="{ active: detailTab === 'content' }" @click="detailTab = 'content'"><BookOpenCheck :size="16" />病例内容</button><button type="button" :class="{ active: detailTab === 'workflow' }" :disabled="!selectedRecord?.draft" @click="detailTab = 'workflow'"><GitBranch :size="16" />AI 质控流程<span v-if="selectedRecord?.draft">{{ selectedRecord.draft.workflow.length }}</span></button></nav>

        <div v-if="selectedRecord?.draft && detailTab === 'workflow'" class="case-agent-workflow workflow-focus-view">
          <div class="section-heading"><div><span class="section-kicker">Agent 运行记录</span><h3>病例生成与审核工作流</h3></div><GitBranch :size="19" /></div>
          <ol><li v-for="step in selectedRecord.draft.workflow" :key="step.id" :class="step.status"><span><Check v-if="step.status === 'done'" :size="14" /><LoaderCircle v-else :size="14" /></span><div><strong>{{ step.name }}</strong><small>{{ step.agent }}</small><p>{{ step.detail }}</p></div></li></ol>
        </div>

        <form v-if="detailTab === 'content' && editing" class="teacher-case-edit-form" @submit.prevent="saveEdit">
          <div><label>病例名称<input v-model="editForm.title" /></label><label>科室<input v-model="editForm.department" /></label><label>难度<select v-model="editForm.difficulty"><option>入门</option><option>进阶</option><option>高阶</option></select></label></div>
          <label>主诉<input v-model="editForm.chief_complaint" /></label>
          <label>现病史<textarea v-model="editForm.present_illness" rows="3" /></label>
          <label>核心学习目标<textarea v-model="editForm.learning_goal" rows="2" /></label>
          <label>候选诊断<input v-model="editForm.suspected_diagnosis" /></label>
          <label>教师修订说明<textarea v-model="editForm.teacher_note" rows="2" /></label>
          <footer><button class="button-secondary" type="button" @click="editing = false"><X :size="16" />取消</button><button class="button-primary" type="submit" :disabled="saving"><LoaderCircle v-if="saving" class="spin" :size="16" /><Save v-else :size="16" />保存为待审核草稿</button></footer>
        </form>

        <template v-else-if="detailTab === 'content'">
          <div class="editor-section"><h3>病例基本信息</h3><dl><dt>主诉</dt><dd>{{ selected.chief_complaint }}</dd><dt>现病史</dt><dd>{{ selected.present_illness || selected.history?.present_illness?.join('；') }}</dd><dt>候选诊断</dt><dd>{{ selected.hidden_final_diagnosis }}</dd><dt>查体</dt><dd>{{ selected.physical_exam?.join('；') }}</dd></dl></div>
          <div class="editor-columns">
            <div class="editor-section"><h3><BookOpenCheck :size="17" />关键得分点</h3><p v-for="item in selected.key_scoring_points" :key="item">{{ item }}</p></div>
            <div class="editor-section risk"><h3><ShieldAlert :size="17" />高风险扣分项</h3><p v-for="item in selected.high_risk_omissions" :key="item.id">{{ item.text }}</p><p v-if="!selected.high_risk_omissions?.length">{{ selected.high_risk_misses?.join('；') }}</p></div>
          </div>
          <div class="editor-columns">
            <div class="editor-section"><h3>鉴别诊断</h3><div class="tag-cloud"><span v-for="item in selected.differential_diagnoses" :key="item">{{ item }}</span></div></div>
            <div class="editor-section"><h3>指南证据</h3><div class="tag-cloud evidence"><span v-for="item in selected.recommended_guidelines" :key="item">{{ item }}</span></div></div>
          </div>

          <section v-if="selected.history_taking_reference" class="editor-section history-reference">
            <h3><BookOpenCheck :size="17" />问诊标准参考</h3>
            <p class="history-ref-source">{{ selected.history_taking_reference.source }}</p>
            <template v-for="(text, name) in selected.history_taking_reference.sections" :key="name">
              <p v-if="name === '问诊要点' || name === '鉴别诊断问诊要点'" class="history-ref-line"><b>{{ name }}</b>{{ text }}</p>
            </template>
          </section>

          <section v-if="selectedRecord?.draft" class="teacher-decision-panel">
            <div><span><ClipboardCheck :size="19" /></span><div><strong>教师最终决策</strong><p>AI 已完成草拟和校验，但没有发布权限。请检查内容后作出决定。</p></div><b :class="statusClass(selectedRecord.status)">{{ selectedRecord.status }}</b></div>
            <textarea v-model="decisionNote" rows="2" placeholder="填写批准依据、退回要求或拒绝原因（可选）" />
            <footer><button type="button" class="decision-reject" :disabled="deciding" @click="decideCase('reject')"><ThumbsDown :size="16" />拒绝</button><button type="button" class="decision-revision" :disabled="deciding" @click="decideCase('request_revision')"><RotateCcw :size="16" />退回修改</button><button type="button" class="decision-approve" :disabled="deciding" @click="decideCase('approve')"><ThumbsUp :size="16" />批准并加入病例库</button></footer>
          </section>
        </template>
      </section>
    </div>

    <section v-else-if="activeTab === 'recommendations'" class="teacher-recommendation-workspace">
      <div class="recommendation-analysis-strip">
        <article><small>分析训练</small><strong>{{ recommendationData?.analysis.training_sessions ?? 0 }}</strong><span>次</span></article>
        <article><small>班级均分</small><strong>{{ recommendationData?.analysis.class_average ?? 0 }}</strong><span>分</span></article>
        <article><small>学生样本</small><strong>{{ recommendationData?.analysis.students_analyzed ?? 0 }}</strong><span>人</span></article>
        <article><small>共性薄弱项</small><strong>{{ recommendationData?.analysis.common_missing_points.length ?? 0 }}</strong><span>项</span></article>
      </div>
      <div class="recommendation-algorithm-note"><Bot :size="18" /><div><strong>推荐算法说明</strong><p>{{ recommendationData?.algorithm }}</p></div></div>
      <div class="teacher-recommendation-list">
        <article v-for="item in recommendationData?.recommendations" :key="item.id">
          <div class="recommendation-rank"><span>TOP {{ item.rank }}</span><strong>{{ item.score }}</strong><small>推荐分</small></div>
          <div class="recommendation-content"><span class="section-kicker">{{ item.target_students }}</span><h2>{{ item.title }}</h2><p>{{ item.reason }}</p><div class="recommendation-evidence"><span v-for="evidence in item.evidence" :key="evidence">{{ evidence }}</span></div><small>预期效果：{{ item.expected_impact }}</small></div>
          <div class="recommendation-decision">
            <template v-if="item.decision.action === 'pending'"><button class="button-primary" type="button" @click="acceptRecommendation(item)"><Sparkles :size="16" />采纳并生成病例</button><button class="button-secondary" type="button" @click="dismissRecommendation(item)">暂不采纳</button></template>
            <div v-else :class="item.decision.action"><CheckCircle2 v-if="item.decision.action === 'accept'" :size="19" /><X v-else :size="19" /><strong>{{ item.decision.action === 'accept' ? '教师已采纳' : '教师暂不采纳' }}</strong><button v-if="item.decision.action === 'accept'" type="button" @click="openBuilder(item)">继续生成 <ArrowRight :size="15" /></button></div>
          </div>
        </article>
      </div>
    </section>

    <CaseKnowledgePanel v-else :class="{ 'is-compiling': compilingKnowledge }" @compile="compileKnowledgeEntries" />
  </div>
</template>

<style scoped>
.history-reference { border-left: 3px solid #2f7d6c; background: #f4faf8; }
.history-ref-source { margin: 0 0 8px; color: #6b8290; font-size: 12px; }
.history-ref-line { margin: 0 0 8px; color: #33454f; font-size: 13px; line-height: 1.7; }
.history-ref-line b { display: inline-block; min-width: 104px; color: #18705f; }
.case-library-panel.is-compiling { opacity: .6; pointer-events: none; }
</style>
