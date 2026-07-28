<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { askRag, exportObsidian, getAdminDataSources, getAdminUsers, getAnatomyExercises, getCases, getGraphStatus, getGuidelines, getKnowledge, getKnowledgeGraph, getKnowledgeStatus, getOverview, getTeacherDashboard, getTextbookPathways, getTrainingReport, getWorkflow, login, logout, searchKnowledge, sendAgentMessage, sendPatientMessage, speak, submitAnatomy, syncAdminDataSources } from './api';
import { mockAdminData } from './data/admin';
import { mockAnatomyExercises } from './data/anatomy';
import { mockCases } from './data/cases';
import { mockGraph } from './data/graph';
import { mockKnowledge } from './data/knowledge';
import { mockTextbookPathways } from './data/textbooks';
import type { AgentResponse, AnatomyExercise, AnatomyResult, AuthUser, CaseSummary, ChatMessage, DataSourceItem, GuidelineDoc, KnowledgeEdge, KnowledgeItem, KnowledgeNode, MissingPoint, Overview, PatientChatResponse, Role, ScoreItem, TeacherDashboard, TextbookStage, TrainingReport, WorkflowStage, WorkflowTrace } from './types';

type ModuleKey = 'training' | 'knowledge' | 'anatomy' | 'graph' | 'report' | 'teacher' | 'cases' | 'admin';
type TutorState = 'idle' | 'listening' | 'speaking' | 'alert' | 'scoring';

const useBackend = Boolean(import.meta.env.VITE_API_BASE_URL);
const demoRoleFromUrl = new URLSearchParams(window.location.search).get('demo') as Role | null;
if (demoRoleFromUrl && ['student', 'teacher', 'admin'].includes(demoRoleFromUrl)) {
  const demoUser = demoRoleFromUrl === 'admin'
    ? { id: 'u_admin', name: '超级管理员', account: 'admin', role: 'super_admin', status: 'active', department: '系统管理', permissions: ['users', 'data_sources', 'knowledge', 'graph', 'rag', 'obsidian'] }
    : demoRoleFromUrl === 'teacher'
      ? { id: 'u_teacher_demo', name: '教师演示账号', account: 'teacher', role: 'teacher', status: 'active', department: '诊断学教研室', permissions: ['dashboard', 'cases', 'reports'] }
      : { id: 'u_student_demo', name: '学生演示账号', account: 'student', role: 'student', status: 'active', department: '临床医学五年制', permissions: ['training', 'knowledge', 'report'] };
  localStorage.setItem('lszx_auth', '1');
  localStorage.setItem('lszx_role', demoRoleFromUrl);
  localStorage.setItem('lszx_user', JSON.stringify(demoUser));
}
const storedAuth = localStorage.getItem('lszx_auth');
const role = ref<Role>((localStorage.getItem('lszx_role') as Role) || 'student');
const isAuthenticated = ref(storedAuth === '1');
const currentUser = ref<AuthUser | null>(localStorage.getItem('lszx_user') ? JSON.parse(localStorage.getItem('lszx_user') || 'null') : null);
const loginAccount = ref(role.value === 'admin' ? 'admin' : role.value === 'teacher' ? 'teacher' : 'student');
const loginPassword = ref(role.value === 'admin' ? 'admin123' : role.value === 'teacher' ? 'teacher123' : 'student123');
const loginRole = ref<Role>(role.value);
const loginError = ref('');
const activeModule = ref<ModuleKey>(role.value === 'admin' ? 'admin' : role.value === 'teacher' ? 'teacher' : 'training');
const activeCaseId = ref('emergency_chest_pain');
const activeExerciseId = ref('heart_position');
const trainingInput = ref('请问您胸痛是什么性质？有没有向左肩或后背放射？');
const agentInput = ref('打开腹痛病例');
const knowledgeQuery = ref('主动脉夹层');
const graphQuery = ref('黄疸');
const graphLang = ref<'zh' | 'en'>('zh');
const graphType = ref('全部');
const selectedSubject = ref('全部');
const selectedZone = ref('');
const selectedKnowledge = ref<KnowledgeItem | null>(null);
const selectedNode = ref<KnowledgeNode | null>(null);
const anatomyResult = ref<AnatomyResult | null>(null);
const tutorState = ref<TutorState>('idle');
const loading = ref(false);
const agentLoading = ref(false);
const dataLoading = ref(true);
const voiceMuted = ref(false);
const error = ref('');
const agentCards = ref<AgentResponse['result_cards']>([]);
const learningPath = ref<string[]>(['急性冠脉综合征', '心电图', '肌钙蛋白', '主动脉夹层鉴别']);
const workflowTrace = ref<WorkflowTrace[]>([]);

const overview = ref<Overview | null>(null);
const cases = ref<CaseSummary[]>([]);
const messages = ref<ChatMessage[]>([
  { role: 'patient', content: '医生，我胸口疼得厉害，大概两小时前开始的。' },
  { role: 'tutor', content: '请围绕胸痛性质、部位、持续时间、诱因、伴随症状和危险因素进行问诊。' }
]);
const scores = ref<ScoreItem[]>([]);
const missing = ref<MissingPoint[]>([]);
const citations = ref<GuidelineDoc[]>([]);
const knowledge = ref<KnowledgeItem[]>([]);
const anatomy = ref<AnatomyExercise[]>([]);
const workflow = ref<WorkflowStage[]>([]);
const dashboard = ref<TeacherDashboard | null>(null);
const report = ref<TrainingReport | null>(null);
const kgNodes = ref<KnowledgeNode[]>([]);
const kgEdges = ref<KnowledgeEdge[]>([]);
const adminUsers = ref<unknown[]>(mockAdminData.adminUsers);
const dataSources = ref<DataSourceItem[]>(mockAdminData.dataSources as DataSourceItem[]);
const textbookPathways = ref<TextbookStage[]>(mockTextbookPathways as TextbookStage[]);
const knowledgeStatus = ref<Record<string, unknown>>({ items: 85, bilingual_items: 85, vector_ready: 85 });
const graphStatus = ref<Record<string, unknown>>({ nodes: 177, edges: 162, obsidian_ready: true });
const obsidianPreview = ref<{ message: string; note_count: number; vault_name: string; notes: Array<{ filename: string; content: string }> } | null>(null);

const fallbackOverview: Overview = {
  name: '临思智训', subtitle: 'AI标准化病人临床思维训练平台', contest_track: 'AI+医学教育交叉',
  positioning: '整合多病例标准化病人、拟人数字导师、解剖定位、Hybrid RAG 和临床医学知识图谱。',
  metrics: [
    { label: '虚拟病例', value: '8个', trend: '差异化脚本' }, { label: '知识条目', value: '60条', trend: '结构化mock' },
    { label: '图谱规模', value: '95/135', trend: '节点/关系' }, { label: '解剖练习', value: '19项', trend: '五大系统' }
  ], scenarios: ['学生端', '教师端']
};
const fallbackCases = mockCases as unknown as CaseSummary[];
const fallbackKnowledge = mockKnowledge as unknown as KnowledgeItem[];
const fallbackAnatomy = mockAnatomyExercises as unknown as AnatomyExercise[];
const fallbackGraph = mockGraph as unknown as { nodes: KnowledgeNode[]; edges: KnowledgeEdge[] };
const fallbackGuidelines: GuidelineDoc[] = [
  { id: 'chest_pain_primary', title: '《急性胸痛基层诊疗指南》', source: '教学示例知识库', type: '指南', tags: ['胸痛', '急诊'], content: '急性胸痛评估应关注疼痛性质、持续时间、诱因、放射痛、伴随症状和危险因素。' },
  { id: 'acs_guideline', title: '《急性冠脉综合征诊疗指南》', source: '教学示例知识库', type: '指南', tags: ['ACS', '肌钙蛋白'], content: '急性冠脉综合征评估需要结合症状、心电图动态变化和肌钙蛋白结果。' }
];
const fallbackWorkflow: WorkflowStage[] = [
  { id: 'router', name: '意图识别', agent: 'RouterAgent', goal: '判断导航、检索、病例训练、解剖练习或报告生成。' },
  { id: 'safety', name: '医学安全检查', agent: 'SafetyAgent', goal: '确认输出仅用于虚拟教学。' },
  { id: 'patient', name: '病人脚本回复', agent: 'PatientAgent', goal: '依据当前病例脚本回答。' },
  { id: 'retrieval', name: '混合检索', agent: 'RetrievalAgent', goal: '检索知识库、embedding和图谱节点。' },
  { id: 'scoring', name: '过程评分', agent: 'ScoringAgent', goal: '按当前病例关键得分点评分。' },
  { id: 'report', name: '报告生成', agent: 'ReportAgent', goal: '生成复训建议。' }
];
const fallbackDashboard: TeacherDashboard = {
  class_average: 82, completion_rate: 76, training_sessions: 248, teacher_time_saved: '41%', citation_accuracy: '88%', intervention_needed: 6,
  improvements: [{ label: '临床推理分提升', value: 24 }, { label: '关键问诊遗漏率下降', value: 32 }, { label: '指南引用准确率提升', value: 18 }],
  common_missing_points: ['未覆盖高危鉴别', '未申请必要检查', '缺少指南依据'],
  risk_rankings: [{ label: '未排除主动脉夹层', count: 34, level: '高' }, { label: '急腹症鉴别不足', count: 27, level: '高' }, { label: '呼吸困难低氧评估不足', count: 18, level: '中' }],
  students: [{ name: '学生A', sessions: 12, average_score: 86, last_case: '急诊胸痛', weakness: '指南依据', needs_intervention: false }, { name: '学生B', sessions: 8, average_score: 71, last_case: '呼吸困难', weakness: '高危鉴别', needs_intervention: true }],
  teaching_suggestions: ['下节课建议强化多主诉高危鉴别路径', '增加解剖定位和检查选择联动练习']
};
const fallbackReport: TrainingReport = {
  case_id: 'emergency_chest_pain', diagnosis_path: ['主诉胸痛', '补全疼痛性质和放射痛', '识别ACS危险因素', '排除主动脉夹层和肺栓塞', '申请心电图和肌钙蛋白'],
  strengths: ['能围绕主诉开展问诊', '能提出至少一个重点鉴别'],
  improvements: ['需更早补全高危遗漏点', '需说明指南依据和非诊疗边界'],
  recommended_cases: ['呼吸困难', '急性腹痛', '心脏定位'],
  citations: fallbackGuidelines.map((doc) => ({ id: doc.id, title: doc.title, source: doc.source, snippet: doc.content }))
};

const navItems = computed(() => {
  if (role.value === 'admin') return [{ key: 'admin', label: '超级管理', glyph: '管' }, { key: 'knowledge', label: '知识资产', glyph: '知' }, { key: 'graph', label: '双语图谱', glyph: '图' }, { key: 'teacher', label: '教学监管', glyph: '教' }, { key: 'report', label: '报告抽查', glyph: '审' }];
  return role.value === 'student'
    ? [{ key: 'training', label: '病例训练', glyph: '训' }, { key: 'knowledge', label: '知识库', glyph: '知' }, { key: 'anatomy', label: '解剖定位', glyph: '解' }, { key: 'graph', label: '知识图谱', glyph: '图' }, { key: 'report', label: '训练报告', glyph: '报' }]
    : [{ key: 'teacher', label: '班级看板', glyph: '班' }, { key: 'cases', label: '病例管理', glyph: '例' }, { key: 'knowledge', label: '资源管理', glyph: '资' }, { key: 'graph', label: '图谱分析', glyph: '图' }, { key: 'report', label: '报告抽查', glyph: '审' }];
});
const currentOverview = computed(() => overview.value ?? fallbackOverview);
const currentDashboard = computed(() => dashboard.value ?? fallbackDashboard);
const currentReport = computed(() => report.value ?? fallbackReport);
const activeCase = computed(() => cases.value.find((item) => item.id === activeCaseId.value) ?? fallbackCases[0]);
const activeExercise = computed(() => anatomy.value.find((item) => item.id === activeExerciseId.value) ?? fallbackAnatomy[0]);
const activeCaseGuidelines = computed(() => activeCase.value.recommended_guidelines?.length ? activeCase.value.recommended_guidelines : fallbackGuidelines.map((doc) => doc.title));
const subjects = computed(() => ['全部', ...Array.from(new Set(knowledge.value.map((item) => item.subject)))]);
const filteredKnowledge = computed(() => knowledge.value.filter((item) => {
  const bySubject = selectedSubject.value === '全部' || item.subject === selectedSubject.value;
  const q = knowledgeQuery.value.trim().toLowerCase();
  const haystack = [item.id, item.title, item.title_zh, item.title_en, item.summary, item.summary_zh, item.summary_en, item.category, item.source_type, item.source_name, item.data_source, ...(item.keywords ?? []), ...(item.keywords_en ?? []), ...(item.related_diseases ?? []), ...(item.related_symptoms ?? []), ...(item.related_exams ?? []), ...(item.related_anatomy ?? [])].join(' ').toLowerCase();
  return bySubject && (!q || haystack.includes(q));
}));
const averageScore = computed(() => Math.round(scores.value.reduce((sum, item) => sum + item.score, 0) / Math.max(scores.value.length, 1)));
const graphNodes = computed(() => {
  const list = kgNodes.value.length ? kgNodes.value : fallbackGraph.nodes;
  return list.map((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(list.length, 1) - Math.PI / 2;
    const ring = 120 + (index % 4) * 34;
    return { ...node, x: 330 + Math.cos(angle) * ring, y: 235 + Math.sin(angle) * ring };
  });
});
const graphEdges = computed(() => kgEdges.value.length ? kgEdges.value : fallbackGraph.edges);
const graphTypes = computed(() => ['全部', ...Array.from(new Set(graphNodes.value.map((node) => node.group))).sort()]);
const graphNodeLabel = (node?: KnowledgeNode | null) => !node ? '' : graphLang.value === 'en' ? (node.label_en ?? node.label) : (node.label_zh ?? node.label);
const graphNodeSummary = (node?: KnowledgeNode | null) => !node ? '点击图谱节点查看关联知识、病例、指南和推荐学习路径。' : graphLang.value === 'en' ? (node.description_en ?? node.summary ?? 'Click a node to inspect related evidence and learning path.') : (node.description_zh ?? node.summary ?? '点击图谱节点查看关联知识、病例、指南和推荐学习路径。');
const edgeLabel = (edge: KnowledgeEdge) => graphLang.value === 'en' ? (edge.relation_en ?? edge.relation) : (edge.relation_zh ?? edge.relation);
const visibleGraphNodes = computed(() => {
  const q = graphQuery.value.trim();
  const filtered = graphNodes.value.filter((node) => {
    const byType = graphType.value === '全部' || node.group === graphType.value;
    const haystack = [node.id, node.label, node.label_zh, node.label_en, node.group, node.type, node.summary, node.description_zh, node.description_en, node.embedding_text, node.embedding_text_zh, node.embedding_text_en, ...(node.aliases_zh ?? []), ...(node.aliases_en ?? [])].join(' ').toLowerCase();
    return byType && (!q || haystack.includes(q.toLowerCase()));
  });
  const base = filtered.length ? filtered : graphNodes.value.slice(0, 24);
  return base.slice(0, 36).map((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(base.slice(0, 36).length, 1) - Math.PI / 2;
    const ring = index === 0 ? 0 : 125 + (index % 3) * 54;
    return { ...node, x: 330 + Math.cos(angle) * ring, y: 235 + Math.sin(angle) * ring };
  });
});
const visibleNodeIds = computed(() => new Set(visibleGraphNodes.value.map((node) => node.id)));
const visibleGraphEdges = computed(() => graphEdges.value.filter((edge) => visibleNodeIds.value.has(edge.source) || visibleNodeIds.value.has(edge.target)).slice(0, 70));
const selectedNeighbors = computed(() => {
  if (!selectedNode.value) return [];
  return graphEdges.value.filter((edge) => edge.source === selectedNode.value?.id || edge.target === selectedNode.value?.id).slice(0, 10);
});
const tutorLine = computed(() => tutorState.value === 'listening' ? '倾听学生输入' : tutorState.value === 'speaking' ? '正在讲解' : tutorState.value === 'alert' ? '发现风险遗漏' : tutorState.value === 'scoring' ? '正在评分' : '待机陪练');

function locate(id: string) { return visibleGraphNodes.value.find((node) => node.id === id) ?? graphNodes.value.find((node) => node.id === id) ?? visibleGraphNodes.value[0] ?? graphNodes.value[0]; }
function switchRole(next: Role) { role.value = next; localStorage.setItem('lszx_role', next); activeModule.value = next === 'admin' ? 'admin' : next === 'teacher' ? 'teacher' : 'training'; }
function openModule(key: string) { activeModule.value = key as ModuleKey; }
function setListening() { if (!loading.value && !agentLoading.value) tutorState.value = 'listening'; }
function cardGraphTarget(item: KnowledgeItem) { return item.graph_node_ids?.[0] ?? item.graph_node_id ?? item.id; }
function caseOpening(caseData: CaseSummary) { return caseData.opening ?? caseData.script?.opening ?? `医生您好，我是${caseData.patient_profile ?? '虚拟教学病人'}，主要不舒服是${caseData.chief_complaint}。`; }
function caseCitationDocs(caseData: CaseSummary): GuidelineDoc[] {
  const docs = activeCaseGuidelines.value.map((title, index) => ({ id: `${caseData.id}_guide_${index}`, title, source: '第三版结构化教学知识库', type: 'citation', tags: [caseData.title, caseData.department], content: `${caseData.title}训练中建议追溯${title}。` }));
  return docs.length ? docs : fallbackGuidelines;
}
function localScores(text: string, caseData: CaseSummary): ScoreItem[] {
  const combined = [text, ...messages.value.map((m) => m.content)].join(' ');
  const examHits = (caseData.available_exams ?? []).filter((item) => combined.includes(item)).length;
  const diffHits = (caseData.differential_diagnoses ?? []).filter((item) => combined.includes(item)).length;
  const pointHits = (caseData.key_scoring_points ?? []).filter((item) => combined.includes(item) || item.split('和').some((part) => part && combined.includes(part))).length;
  return [
    { name: '问诊完整性', score: Math.min(96, 52 + pointHits * 10), max_score: 100, feedback: pointHits ? `已覆盖${caseData.title}的部分关键问诊点。` : `建议先围绕${caseData.chief_complaint}补全现病史。` },
    { name: '检查选择合理性', score: Math.min(96, 45 + examHits * 12), max_score: 100, feedback: examHits ? '检查选择开始贴合当前病例。' : `可考虑：${(caseData.available_exams ?? []).slice(0, 3).join('、')}。` },
    { name: '鉴别诊断覆盖率', score: Math.min(96, 42 + diffHits * 13), max_score: 100, feedback: diffHits ? '已提出当前病例相关鉴别。' : `需要覆盖：${(caseData.differential_diagnoses ?? []).slice(0, 3).join('、')}。` },
    { name: '临床决策安全性', score: combined.includes('风险') || combined.includes('急诊') || combined.includes('复查') ? 78 : 58, max_score: 100, feedback: '注意先做风险分层，并保持教学用途边界。' },
    { name: '指南引用准确率', score: activeCaseGuidelines.value.some((item) => combined.includes(item)) || combined.includes('指南') ? 82 : 55, max_score: 100, feedback: `可引用：${activeCaseGuidelines.value.slice(0, 2).join('、')}。` },
    { name: '沟通表达评分', score: combined.includes('请') || combined.includes('担心') || combined.includes('解释') ? 80 : 68, max_score: 100, feedback: '表达清楚时也要安抚虚拟病人并说明下一步。' }
  ];
}
function localMissing(text: string, caseData: CaseSummary): MissingPoint[] {
  const combined = [text, ...messages.value.map((m) => m.content)].join(' ');
  const citation = caseCitationDocs(caseData)[0];
  return (caseData.high_risk_omissions ?? [])
    .filter((item) => !(item.keywords ?? [item.text]).some((keyword) => keyword && combined.includes(keyword)))
    .slice(0, 5)
    .map((item) => ({ id: item.id, level: item.level, text: item.text, suggestion: item.suggestion, citation: { id: citation.id, title: citation.title, source: citation.source, snippet: citation.content } }));
}
function localPatientReply(text: string): PatientChatResponse {
  const caseData = activeCase.value;
  const scriptReply = caseData.script?.answers?.find((item) => item.keywords.some((keyword) => keyword && text.includes(keyword)))?.reply;
  const fieldReply = [
    { keys: ['现病史', '多久', '开始', '诱因', '症状'], value: caseData.present_illness },
    { keys: ['既往', '病史', '用药'], value: caseData.past_history },
    { keys: ['个人史', '吸烟', '饮酒', '职业', '生活'], value: caseData.personal_history },
    { keys: ['家族', '遗传'], value: caseData.family_history },
    { keys: ['查体', '体温', '血压', '心率', '腹部', '肺部'], value: caseData.physical_exam }
  ].find((item) => item.keys.some((key) => text.includes(key)) && item.value)?.value;
  const reply = scriptReply ?? fieldReply ?? (text.includes('诊断') || text.includes('最终') ? '我不知道最终诊断，只能告诉您这个虚拟病例里的症状和已知信息。' : '这个我不太清楚，医生您能再具体问一下吗？');
  const docs = caseCitationDocs(caseData);
  return {
    patient_reply: { role: 'patient', content: reply },
    tutor_hint: `继续围绕${caseData.title}推进：${(caseData.key_scoring_points ?? []).slice(0, 3).join('、')}。`,
    scores: localScores(text, caseData),
    missing_points: localMissing(text, caseData),
    workflow_trace: fallbackWorkflow.map((stage) => ({ ...stage, status: 'done', detail: stage.goal })),
    citations: docs.map((doc) => ({ id: doc.id, title: doc.title, source: doc.source, snippet: doc.content })),
    safety_notes: ['本病例为虚拟教学病例，不含真实患者信息。', '平台反馈用于医学教学训练，不用于真实临床诊断。']
  };
}

function demoUser(nextRole: Role): AuthUser {
  if (nextRole === 'admin') return { id: 'u_admin', name: '超级管理员', account: 'admin', role: 'super_admin', status: 'active', department: '系统管理', permissions: ['users', 'data_sources', 'knowledge', 'graph', 'rag', 'obsidian'] };
  if (nextRole === 'teacher') return { id: 'u_teacher_demo', name: '教师演示账号', account: 'teacher', role: 'teacher', status: 'active', department: '诊断学教研室', permissions: ['dashboard', 'cases', 'reports'] };
  return { id: 'u_student_demo', name: '学生演示账号', account: 'student', role: 'student', status: 'active', department: '临床医学五年制', permissions: ['training', 'knowledge', 'report'] };
}
async function doLogin() {
  loginError.value = '';
  try {
    const response = useBackend ? await login(loginAccount.value, loginPassword.value, loginRole.value) : null;
    const user = response?.user ?? demoUser(loginRole.value);
    currentUser.value = user;
    role.value = user.role === 'super_admin' ? 'admin' : user.role as Role;
    localStorage.setItem('lszx_auth', '1');
    localStorage.setItem('lszx_role', role.value);
    localStorage.setItem('lszx_user', JSON.stringify(user));
    isAuthenticated.value = true;
    activeModule.value = role.value === 'admin' ? 'admin' : role.value === 'teacher' ? 'teacher' : 'training';
  } catch (err) {
    loginError.value = err instanceof Error ? '账号或密码错误，请使用演示账号。' : '登录失败，请重试。';
  }
}
async function doLogout() {
  try { if (useBackend) await logout(); } catch {}
  localStorage.removeItem('lszx_auth');
  localStorage.removeItem('lszx_user');
  isAuthenticated.value = false;
  currentUser.value = null;
  role.value = 'student';
  activeModule.value = 'training';
}
async function syncSources() {
  agentLoading.value = true;
  try {
    const result = useBackend ? await syncAdminDataSources() : { message: '已模拟提交数据源同步任务。', sources: dataSources.value };
    dataSources.value = result.sources;
    agentCards.value = result.sources.slice(0, 5).map((source) => ({ kind: source.platform, title: source.name, summary: source.type + ' · ' + source.index_status, target: source.id }));
    messages.value.push({ role: 'agent', content: result.message });
  } finally {
    agentLoading.value = false;
  }
}
async function exportGraphToObsidian() {
  agentLoading.value = true;
  tutorState.value = 'speaking';
  try {
    obsidianPreview.value = useBackend ? await exportObsidian() : { message: '已生成 Obsidian Markdown 预览。', note_count: 6, vault_name: '临思智训医学教育图谱', notes: graphNodes.value.slice(0, 6).map((node) => ({ filename: node.id + '.md', content: '# ' + graphNodeLabel(node) + '\n\n' + graphNodeSummary(node) })) };
    messages.value.push({ role: 'agent', content: obsidianPreview.value.message });
  } finally {
    agentLoading.value = false;
    window.setTimeout(() => { tutorState.value = 'idle'; }, 900);
  }
}

function selectCase(caseId: string) {
  activeCaseId.value = caseId;
  activeModule.value = 'training';
  anatomyResult.value = null;
  const caseData = cases.value.find((item) => item.id === caseId) ?? fallbackCases[0];
  messages.value = [{ role: 'patient', content: caseOpening(caseData) }, { role: 'tutor', content: `请按${caseData.title}的主诉、现病史、既往史、查体、检查和鉴别诊断完成训练。` }];
  const demo = localPatientReply('');
  scores.value = demo.scores;
  missing.value = demo.missing_points;
  citations.value = caseCitationDocs(caseData);
}
async function sendMessage() {
  const text = trainingInput.value.trim();
  if (!text) return;
  messages.value.push({ role: 'student', content: text });
  trainingInput.value = '';
  loading.value = true;
  tutorState.value = 'scoring';
  error.value = '';
  try {
    const response = useBackend ? await sendPatientMessage(activeCaseId.value, text, messages.value) : localPatientReply(text);
    messages.value.push(response.patient_reply);
    messages.value.push({ role: 'tutor', content: response.tutor_hint });
    scores.value = response.scores;
    missing.value = response.missing_points;
    workflowTrace.value = response.workflow_trace;
    citations.value = response.citations.map((item) => ({ id: item.id, title: item.title, source: item.source, type: 'citation', tags: [activeCase.value.title], content: item.snippet }));
    tutorState.value = response.missing_points.some((item) => item.level === 'danger') ? 'alert' : 'speaking';
    window.setTimeout(() => { if (tutorState.value === 'speaking') tutorState.value = 'idle'; }, 900);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '问诊请求失败，已切换为本地演示。';
    const response = localPatientReply(text);
    messages.value.push(response.patient_reply);
    scores.value = response.scores;
    missing.value = response.missing_points;
    tutorState.value = 'alert';
  } finally {
    loading.value = false;
  }
}
function localKnowledgeCards(query: string) {
  const q = query.trim();
  return knowledge.value
    .filter((item) => !q || [item.title, item.summary, ...(item.keywords ?? []), ...(item.related_diseases ?? []), ...(item.related_symptoms ?? [])].join(' ').includes(q))
    .slice(0, 5)
    .map((item) => ({ kind: item.subject, title: item.title, summary: item.summary, target: cardGraphTarget(item) }));
}
function findCaseByText(message: string) {
  const aliases: Record<string, string> = { 腹痛: 'acute_abdominal_pain', 发热: 'fever_unknown', 呼吸困难: 'dyspnea', 糖尿病: 'diabetes_education', 头痛: 'headache_case', 贫血: 'anemia_case', 黄疸: 'jaundice_case', 胸痛: 'emergency_chest_pain' };
  return cases.value.find((item) => message.includes(item.title) || message.includes(item.chief_complaint) || (item.differential_diagnoses ?? []).some((d) => message.includes(d))) ?? cases.value.find((item) => Object.entries(aliases).some(([key, id]) => message.includes(key) && item.id === id));
}
function findAnatomyByText(message: string) {
  const aliases: Record<string, string> = { 胃: 'stomach_position', 心脏: 'heart_position', 肺: 'left_lung', 肝: 'liver_position', 脑: 'brain_position', 肾: 'kidney_position', 主动脉: 'aorta_course' };
  return anatomy.value.find((item) => message.includes(item.title) || message.includes(item.target)) ?? anatomy.value.find((item) => Object.entries(aliases).some(([key, id]) => message.includes(key) && item.id === id));
}
function localAgent(message: string): AgentResponse {
  if (role.value === 'admin' && (message.toLowerCase().includes('modelscope') || message.includes('数据源') || message.includes('后台'))) return { intent: 'admin_control', action: 'open_admin_data_sources', target_module: 'admin', reply: '已定位到超级管理员数据源与 RAG 配置。', result_cards: dataSources.value.slice(0, 5).map((source) => ({ kind: source.platform, title: source.name, summary: source.type + ' · ' + source.index_status, target: source.id })), learning_path: ['数据源审查', '字段映射', 'Embedding mock', 'Milvus/ChromaDB 配置'], workflow_trace: [], safety_notes: [] };
  if (role.value === 'admin' && (message.toLowerCase().includes('obsidian') || message.includes('导出'))) return { intent: 'admin_control', action: 'obsidian_export', target_module: 'admin', reply: '已准备 Obsidian 双链 Markdown 导出预览。', result_cards: [{ kind: 'Obsidian', title: '双语医学知识图谱', summary: '节点、关系、证据来源和推荐学习路径可导出为 Markdown。', target: 'obsidian' }], learning_path: ['双语节点', 'Markdown 双链', '证据来源', '学习路径'], workflow_trace: [], safety_notes: [] };
  const cards = localKnowledgeCards(message);
  const caseMatch = findCaseByText(message);
  const anatomyMatch = findAnatomyByText(message);
  if (caseMatch && (message.includes('打开') || message.includes('病例') || message.includes('做错') || message.includes('练'))) return { intent: 'navigation', action: 'open_case', target_module: 'training', target_case_id: caseMatch.id, reply: `已为你打开${caseMatch.title}病例。`, result_cards: [{ kind: '病例', title: caseMatch.title, summary: caseMatch.chief_complaint, target: caseMatch.id }], learning_path: caseMatch.recommended_retraining ?? [], workflow_trace: [], safety_notes: [] };
  if (anatomyMatch && (message.includes('解剖') || message.includes('位置') || message.includes('定位') || message.includes('练'))) return { intent: 'navigation', action: 'open_anatomy', target_module: 'anatomy', target_exercise_id: anatomyMatch.id, reply: `已跳转到${anatomyMatch.title}。`, result_cards: [{ kind: '解剖练习', title: anatomyMatch.title, summary: anatomyMatch.prompt, target: anatomyMatch.id }], learning_path: [anatomyMatch.target, ...(anatomyMatch.graph_node_ids ?? [])], workflow_trace: [], safety_notes: [] };
  if (message.includes('教师') || message.includes('看板')) return { intent: 'navigation', action: 'navigate', target_module: 'teacher', reply: '已为你打开教师看板。', result_cards: cards, learning_path: [], workflow_trace: [], safety_notes: [] };
  if (message.includes('报告')) return { intent: 'navigation', action: 'navigate', target_module: 'report', reply: '已跳转到训练报告。', result_cards: cards, learning_path: [], workflow_trace: [], safety_notes: [] };
  if (message.includes('图谱') || message.includes('关系') || message.includes('哪些内容') || message.includes('鉴别')) return { intent: 'graph_retrieval', action: 'show_results', target_module: 'graph', reply: '已基于本地知识库和知识图谱生成学习路径。', result_cards: cards, learning_path: cards.map((card) => card.title).slice(0, 5), workflow_trace: [], safety_notes: [] };
  return { intent: 'retrieval', action: 'show_results', target_module: 'knowledge', reply: `找到 ${cards.length} 条相关知识。`, result_cards: cards, learning_path: cards.map((card) => card.title), workflow_trace: [], safety_notes: [] };
}
async function runAgent(prompt?: string) {
  const text = (prompt ?? agentInput.value).trim();
  if (!text) return;
  agentInput.value = '';
  agentLoading.value = true;
  tutorState.value = 'speaking';
  try {
    const response = useBackend ? await sendAgentMessage(text, role.value, activeModule.value) : localAgent(text);
    if (response.target_case_id) selectCase(response.target_case_id);
    if (response.target_exercise_id) { activeExerciseId.value = response.target_exercise_id; activeModule.value = 'anatomy'; anatomyResult.value = null; selectedZone.value = ''; }
    if (response.target_module && !response.target_case_id && !response.target_exercise_id) activeModule.value = response.target_module as ModuleKey;
    if (response.target_module === 'teacher') role.value = 'teacher';
    if (response.action === 'obsidian_export') await exportGraphToObsidian();
    messages.value.push({ role: 'agent', content: response.reply });
    agentCards.value = response.result_cards;
    learningPath.value = response.learning_path.length ? response.learning_path : learningPath.value;
    workflowTrace.value = response.workflow_trace.length ? response.workflow_trace : workflowTrace.value;
    if (text.includes('黄疸')) graphQuery.value = '黄疸';
    if (text.includes('腹痛')) graphQuery.value = '腹痛';
    if (text.includes('心脏')) graphQuery.value = '心脏';
  } catch {
    const response = localAgent(text);
    if (response.target_case_id) selectCase(response.target_case_id);
    if (response.target_exercise_id) { activeExerciseId.value = response.target_exercise_id; activeModule.value = 'anatomy'; anatomyResult.value = null; selectedZone.value = ''; }
    if (response.target_module && !response.target_case_id && !response.target_exercise_id) activeModule.value = response.target_module as ModuleKey;
    messages.value.push({ role: 'agent', content: response.reply });
    agentCards.value = response.result_cards;
  } finally {
    agentLoading.value = false;
    if (tutorState.value === 'speaking') window.setTimeout(() => { tutorState.value = 'idle'; }, 900);
  }
}
async function runKnowledgeSearch() {
  try {
    if (!useBackend) { agentCards.value = localKnowledgeCards(knowledgeQuery.value); return; }
    const result = await searchKnowledge(knowledgeQuery.value);
    agentCards.value = result.items;
  } catch {
    agentCards.value = localKnowledgeCards(knowledgeQuery.value);
  }
}
async function runRagQuestion(question: string) {
  tutorState.value = 'speaking';
  try {
    const response = useBackend ? await askRag(question, '知识库检索') : null;
    messages.value.push({ role: 'agent', content: response?.answer ?? '已基于本地知识库生成学习提示，请查看相关知识条目。' });
    if (response) {
      workflowTrace.value = response.workflow_trace;
      learningPath.value = response.recommended_learning_path?.length ? response.recommended_learning_path : learningPath.value;
    }
  } finally {
    window.setTimeout(() => { tutorState.value = 'idle'; }, 900);
  }
}
async function chooseZone(zone: string) {
  selectedZone.value = zone;
  tutorState.value = 'scoring';
  try {
    anatomyResult.value = useBackend ? await submitAnatomy(activeExercise.value.id, zone) : mockAnatomyResult(zone);
  } finally {
    tutorState.value = anatomyResult.value?.correct ? 'speaking' : 'alert';
    if (anatomyResult.value?.correct) window.setTimeout(() => { tutorState.value = 'idle'; }, 900);
  }
}
function mockAnatomyResult(zone: string): AnatomyResult {
  const correct = zone === activeExercise.value.answer_zone;
  return { correct, feedback: correct ? '定位正确，已关联临床学习目标。' : activeExercise.value.target === '胃' || activeExercise.value.id === 'stomach_position' ? '你的位置偏右，胃主要位于左上腹，毗邻肝左叶、脾脏和胰腺。' : '定位还不准确，建议复习体表投影和相邻结构。', explanation: activeExercise.value.explanation, clinical_link: activeExercise.value.clinical_link, score_items: [
    { name: '定位准确性', score: correct ? 92 : 54, max_score: 100, feedback: '依据选择区域评分。' },
    { name: '解剖名称掌握', score: correct ? 84 : 60, max_score: 100, feedback: '继续巩固结构名称。' },
    { name: '临床关联理解', score: correct ? 86 : 58, max_score: 100, feedback: activeExercise.value.clinical_link },
    { name: '错误原因分析', score: correct ? 88 : 66, max_score: 100, feedback: '已给出复习方向。' }
  ] };
}
async function playTutor() {
  tutorState.value = 'speaking';
  const text = missing.value[0]?.suggestion ?? '请继续完成问诊、检查选择、鉴别诊断和指南依据训练。';
  try {
    if (voiceMuted.value) { messages.value.push({ role: 'agent', content: '语音已静音，保留文字讲解。' }); return; }
    const result = useBackend ? await speak(text) : { message: '已模拟播放数字人导师讲解。' };
    messages.value.push({ role: 'agent', content: result.message });
  } finally {
    window.setTimeout(() => { tutorState.value = 'idle'; }, 900);
  }
}
function selectKnowledge(item: KnowledgeItem) {
  selectedKnowledge.value = item;
  const id = cardGraphTarget(item);
  selectedNode.value = graphNodes.value.find((node) => node.id === id) ?? null;
  graphQuery.value = graphNodeLabel(selectedNode.value) || item.title;
}
function selectGraphNode(node: KnowledgeNode) {
  selectedNode.value = node;
  activeModule.value = 'graph';
  graphQuery.value = graphNodeLabel(node);
  learningPath.value = [graphNodeLabel(node), ...selectedNeighbors.value.map((edge) => edgeLabel(edge) === '关联病例' ? '进入关联病例训练' : edgeLabel(edge)).slice(0, 4)];
}

onMounted(async () => {
  dataLoading.value = true;
  try {
    if (!useBackend) throw new Error('local mock');
    const [site, caseData, guidelineData, knowledgeData, anatomyData, workflowData, dashboardData, reportData, graphData, adminUserData, sourceData, textbookData, knowledgeStatusData, graphStatusData] = await Promise.all([
      getOverview(), getCases(), getGuidelines(), getKnowledge(), getAnatomyExercises(), getWorkflow(), getTeacherDashboard(), getTrainingReport(activeCaseId.value), getKnowledgeGraph(graphLang.value), getAdminUsers(), getAdminDataSources(), getTextbookPathways(), getKnowledgeStatus(), getGraphStatus()
    ]);
    overview.value = site; cases.value = caseData; citations.value = guidelineData; knowledge.value = knowledgeData; anatomy.value = anatomyData; workflow.value = workflowData.stages; dashboard.value = dashboardData; report.value = reportData; kgNodes.value = graphData.nodes; kgEdges.value = graphData.edges; adminUsers.value = adminUserData; dataSources.value = sourceData; textbookPathways.value = textbookData; knowledgeStatus.value = knowledgeStatusData; graphStatus.value = graphStatusData;
  } catch {
    cases.value = fallbackCases; citations.value = fallbackGuidelines; knowledge.value = fallbackKnowledge; anatomy.value = fallbackAnatomy; workflow.value = fallbackWorkflow; dashboard.value = fallbackDashboard; report.value = fallbackReport; kgNodes.value = fallbackGraph.nodes; kgEdges.value = fallbackGraph.edges;
  } finally {
    selectedKnowledge.value = knowledge.value[0] ?? null;
    selectedNode.value = kgNodes.value[0] ?? fallbackGraph.nodes[0];
    const demo = localPatientReply(trainingInput.value);
    scores.value = demo.scores;
    missing.value = demo.missing_points;
    workflowTrace.value = demo.workflow_trace;
    dataLoading.value = false;
  }
});
</script>

<template>
  <main v-if="!isAuthenticated" class="login-shell commercial-login">
    <section class="login-card panel">
      <div class="login-brand"><span>临</span><div><strong>临思智训</strong><p>AI 标准化病人临床思维训练平台</p></div></div>
      <div class="login-visual" aria-hidden="true"><div class="login-pulse"></div><div class="login-path"><span></span><span></span><span></span><span></span></div></div>
      <form class="login-form" @submit.prevent="doLogin">
        <label>角色<select v-model="loginRole" @change="loginAccount = loginRole === 'admin' ? 'admin' : loginRole === 'teacher' ? 'teacher' : 'student'; loginPassword = loginRole === 'admin' ? 'admin123' : loginRole === 'teacher' ? 'teacher123' : 'student123'"><option value="student">学生端</option><option value="teacher">教师端</option><option value="admin">超级管理员</option></select></label>
        <label>账号<input v-model="loginAccount" autocomplete="username" /></label>
        <label>密码<input v-model="loginPassword" type="password" autocomplete="current-password" /></label>
        <button class="primary-action" type="submit">进入平台</button>
        <p v-if="loginError" class="error-text">{{ loginError }}</p>
        <p class="login-demo">演示账号：admin / admin123，teacher / teacher123，student / student123</p>
      </form>
    </section>
  </main>
  <main v-else class="app-shell commercial-edition" :class="[`role-${role}`]">
    <nav class="top-nav">
      <button class="brand" type="button" @click="openModule(role === 'admin' ? 'admin' : role === 'teacher' ? 'teacher' : 'training')"><span>临</span><strong>临思智训</strong><small>{{ currentUser?.name ?? 'AI Clinical Learning Lab' }}</small></button>
      <div class="nav-command"><span>Agent 指令</span><input v-model="agentInput" placeholder="打开腹痛病例 / 练胃的位置 / 黄疸学习路径" @focus="setListening" @keydown.enter="runAgent()" /><button type="button" :disabled="agentLoading" @click="runAgent()">{{ agentLoading ? '处理中' : '执行' }}</button></div>
      <div class="nav-links"><button v-for="item in navItems" :key="item.key" :class="{ active: activeModule === item.key }" type="button" @click="openModule(item.key)">{{ item.label }}</button></div>
      <div class="role-switch" aria-label="角色切换"><button :class="{ active: role === 'student' }" type="button" @click="switchRole('student')">学生端</button><button :class="{ active: role === 'teacher' }" type="button" @click="switchRole('teacher')">教师端</button><button :class="{ active: role === 'admin' }" type="button" @click="switchRole('admin')">管理员</button><button type="button" @click="doLogout">退出</button></div>
    </nav>
    <section class="status-strip"><div class="ecg-line" aria-hidden="true"></div>
      <div><span>{{ currentOverview.contest_track }}</span><strong>AI标准化病人临床思维训练平台</strong></div>
      <div class="metric-row"><article v-for="metric in currentOverview.metrics" :key="metric.label"><b>{{ metric.value }}</b><span>{{ metric.label }}</span></article></div>
    </section>
    <section class="workspace-layout">
      <aside class="left-rail panel">
        <div class="rail-head"><span class="rail-glyph">{{ role === 'admin' ? '管' : role === 'student' ? '学' : '教' }}</span><div><strong>{{ role === 'admin' ? '超级管理区' : role === 'student' ? '学习训练区' : '教学管理区' }}</strong><p>{{ role === 'admin' ? '数据、图谱、RAG' : role === 'student' ? '学习、训练、反馈' : '班级、病例、分析' }}</p></div></div>
        <button v-for="item in navItems" :key="item.key" :class="['rail-item', { active: activeModule === item.key }]" type="button" @click="openModule(item.key)"><span>{{ item.glyph }}</span><strong>{{ item.label }}</strong></button>
        <div class="case-stack" v-if="role === 'student'"><h3>病例列表</h3><button v-for="item in cases" :key="item.id" :class="['case-item', { active: activeCaseId === item.id }]" type="button" @click="selectCase(item.id)"><strong>{{ item.title }}</strong><small>{{ item.department }} · {{ item.difficulty }}</small></button></div>
        <div class="teacher-tools" v-else-if="role === 'teacher'"><h3>教师快捷入口</h3><button type="button" @click="openModule('cases')">编辑病例脚本</button><button type="button" @click="openModule('teacher')">查看干预名单</button><button type="button" @click="runAgent('生成下一节课教学重点')">生成教学建议</button></div><div class="teacher-tools admin-tools" v-else><h3>管理员快捷入口</h3><button type="button" @click="syncSources">模拟同步数据源</button><button type="button" @click="exportGraphToObsidian">导出 Obsidian</button><button type="button" @click="runAgent('ModelScope 数据源状态')">检查数据源</button></div>
      </aside>
      <section class="main-stage" :class="[`stage-${activeModule}`]">
        <div v-if="dataLoading" class="loading-state panel"><span></span><span></span><span></span><p>正在加载教学工作台数据</p></div>
        <section v-else-if="activeModule === 'admin'" class="admin-module">
          <div class="admin-hero panel"><div><span>Super Admin Console</span><h1>知识资产与模型数据源控制台</h1><p>管理账号、ModelScope 数据源、知识库状态、双语图谱、RAG 配置和 Obsidian 导出预览。</p></div><div class="admin-status"><strong>{{ graphStatus.nodes }}</strong><span>图谱节点</span><strong>{{ knowledgeStatus.items }}</strong><span>知识条目</span></div></div>
          <div class="admin-grid">
            <section class="panel admin-panel"><h2>用户与权限</h2><div class="admin-user-list"><article v-for="user in adminUsers" :key="String((user as any).id)"><strong>{{ (user as any).name }}</strong><span>{{ (user as any).role }} · {{ (user as any).department }}</span><b>{{ (user as any).status }}</b></article></div></section>
            <section class="panel admin-panel wide"><div class="panel-title"><h2>ModelScope 与本地数据源</h2><button class="secondary-action" type="button" @click="syncSources">模拟同步</button></div><div class="source-table"><article v-for="source in dataSources" :key="source.id"><div><strong>{{ source.name }}</strong><span>{{ source.platform }} · {{ source.type }}</span></div><p>{{ source.license }}</p><b>{{ source.index_status }}</b></article></div></section>
            <section class="panel admin-panel"><h2>RAG 配置占位</h2><dl><dt>Embedding</dt><dd>mock adapter / EMBEDDING_MODEL</dd><dt>向量库</dt><dd>Milvus + ChromaDB 双配置</dd><dt>引用策略</dt><dd>citation 字段贯穿 Agent 反馈</dd><dt>安全边界</dt><dd>虚拟教学，不作真实诊断</dd></dl></section>
            <section class="panel admin-panel"><div class="panel-title"><h2>Obsidian 图谱导出</h2><button class="secondary-action" type="button" @click="exportGraphToObsidian">生成预览</button></div><p>{{ obsidianPreview?.message ?? '等待导出双语节点 Markdown 预览。' }}</p><div class="obsidian-list" v-if="obsidianPreview"><span>{{ obsidianPreview.vault_name }}</span><button v-for="note in obsidianPreview.notes.slice(0, 5)" :key="note.filename" type="button">{{ note.filename }}</button></div></section>
          </div>
        </section>
        <section v-else-if="activeModule === 'training'" class="module-grid training-module">
          <div class="panel chat-panel"><div class="module-head compact"><div><h1>{{ activeCase.title }}</h1><p>{{ activeCase.chief_complaint }} · {{ activeCase.patient_profile }} · {{ activeCase.learning_goals.join(' / ') }}</p></div><span class="safe-tag">虚拟教学病例</span></div><div class="chat-window"><article v-for="(message, index) in messages" :key="index" :class="['message', message.role]"><b>{{ message.role === 'student' ? '学生' : message.role === 'patient' ? 'AI病人' : message.role === 'agent' ? '平台Agent' : 'TutorAgent' }}</b><p>{{ message.content }}</p></article></div><div class="case-context"><span>{{ activeCase.speaking_style }}</span><span>推荐检查：{{ activeCase.available_exams?.slice(0, 4).join('、') }}</span></div><div class="chat-input"><textarea v-model="trainingInput" rows="3" placeholder="输入问诊问题、检查申请或初步诊断" @focus="setListening" /><button class="primary-action" type="button" :disabled="loading" @click="sendMessage">{{ loading ? '生成中' : '发送' }}</button></div><p v-if="error" class="error-text">{{ error }}</p></div>
          <div class="panel clinical-form"><h2>临床思维提交</h2><label>检查申请<input :value="activeCase.available_exams?.slice(0, 4).join('、')" /></label><label>初步诊断<input :value="activeCase.hidden_final_diagnosis" /></label><label>鉴别诊断<input :value="activeCase.differential_diagnoses?.slice(0, 4).join('、')" /></label><label>治疗原则<textarea rows="3">先完成风险分层和必要检查，教学中不生成真实处方。</textarea></label><button type="button" @click="runRagQuestion(`${activeCase.title}需要哪些指南依据？`)">查看依据</button><div class="guideline-stack"><span v-for="item in activeCaseGuidelines" :key="item">{{ item }}</span></div></div>
        </section>
        <section v-else-if="activeModule === 'knowledge'" class="knowledge-module"><div class="module-head"><div><h1>可追溯知识库</h1><p>按基础医学、桥梁课程、临床核心、专科拓展和实践能力组织教材与指南知识。</p></div><button class="secondary-action" type="button" @click="runKnowledgeSearch">站内检索</button></div><div class="textbook-pathway panel"><article v-for="stage in textbookPathways" :key="stage.id"><span>{{ stage.title_en }}</span><strong>{{ stage.title_zh }}</strong><p>{{ stage.goal }}</p><div><b v-for="book in stage.books.slice(0, 5)" :key="book">{{ book }}</b></div></article></div><div class="search-row panel"><input v-model="knowledgeQuery" placeholder="搜索胸痛、心电图、主动脉夹层、腹部解剖" /><select v-model="selectedSubject"><option v-for="subject in subjects" :key="subject">{{ subject }}</option></select></div><div class="knowledge-layout"><div class="knowledge-list"><button v-for="item in filteredKnowledge" :key="item.id" :class="['knowledge-item', { active: selectedKnowledge?.id === item.id }]" type="button" @click="selectKnowledge(item)"><span>{{ item.subject }} · {{ item.category ?? item.type }}</span><strong>{{ item.title }}</strong><p>{{ item.summary }}</p></button><div v-if="filteredKnowledge.length === 0" class="empty-state panel">没有匹配条目，可换一个关键词。</div></div><article class="knowledge-detail panel" v-if="selectedKnowledge"><span>{{ selectedKnowledge.source_name ?? selectedKnowledge.source }}</span><h2>{{ selectedKnowledge.title }}</h2><p>{{ selectedKnowledge.summary }}</p><div class="tag-row"><b v-for="tag in selectedKnowledge.keywords" :key="tag">{{ tag }}</b></div><dl><dt>关联疾病</dt><dd>{{ selectedKnowledge.related_diseases.join('、') }}</dd><dt>关联症状</dt><dd>{{ selectedKnowledge.related_symptoms.join('、') }}</dd><dt>关联检查</dt><dd>{{ selectedKnowledge.related_exams.join('、') }}</dd><dt>Embedding占位</dt><dd>{{ selectedKnowledge.embedding_id ?? selectedKnowledge.embedding_placeholder?.join(' / ') ?? 'mock-pending' }}</dd></dl></article></div></section>
        <section v-else-if="activeModule === 'anatomy'" class="anatomy-module"><div class="module-head"><div><h1>解剖定位训练</h1><p>用体表投影练习解剖结构定位，并关联病例推理。</p></div></div><div class="anatomy-layout"><aside class="panel anatomy-list"><button v-for="item in anatomy" :key="item.id" :class="{ active: activeExerciseId === item.id }" type="button" @click="activeExerciseId = item.id; anatomyResult = null; selectedZone = ''; tutorState = 'speaking'"><strong>{{ item.title }}</strong><span>{{ item.system }} · {{ item.prompt }}</span></button></aside><div class="panel anatomy-board"><h2>{{ activeExercise.title }}</h2><p>{{ activeExercise.prompt }}</p><svg viewBox="0 0 360 560" class="body-map" role="img" aria-label="解剖定位练习图"><defs><linearGradient id="skin" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#f4dfd3"/><stop offset="1" stop-color="#ead0c2"/></linearGradient></defs><path class="body-silhouette" d="M180 78c-34 0-62 25-62 60v39c-28 13-48 43-50 78l-10 178c-2 34 23 62 57 62h130c34 0 59-28 57-62l-10-178c-2-35-22-65-50-78v-39c0-35-28-60-62-60z"/><circle class="body-head" cx="180" cy="50" r="34"/><g class="svg-zone" @click="chooseZone('brain')"><path :class="['organ','brain',{ picked: selectedZone === 'brain' }]" d="M158 44c-4-13 8-25 23-24 14 1 25 12 23 26 8 5 8 19-1 24-11 7-31 6-44 0-9-5-10-19-1-26z"/></g><g class="svg-zone" @click="chooseZone('neck_midline')"><path :class="['organ','airway',{ picked: selectedZone === 'neck_midline' }]" d="M174 84h12v68h-12z"/></g><g class="svg-zone" @click="chooseZone('upper_mid_chest')"><path :class="['organ','pulmonary-artery',{ picked: selectedZone === 'upper_mid_chest' }]" d="M181 151c23 5 41 21 53 43l-12 9c-10-16-23-27-41-31-18 4-31 15-41 31l-12-9c12-22 30-38 53-43z"/></g><g class="svg-zone" @click="chooseZone('left_lung')"><path :class="['organ','lung',{ picked: selectedZone === 'left_lung' }]" d="M133 143c-31 18-41 72-28 121 8 28 32 41 55 26 14-10 12-41 10-74-2-37-7-61-37-73z"/></g><g class="svg-zone" @click="chooseZone('right_lung')"><path :class="['organ','lung',{ picked: selectedZone === 'right_lung' }]" d="M227 143c31 18 41 72 28 121-8 28-32 41-55 26-14-10-12-41-10-74 2-37 7-61 37-73z"/></g><g class="svg-zone" @click="chooseZone('left_chest')"><path :class="['organ','heart',{ picked: selectedZone === 'left_chest' }]" d="M171 218c-21-18-51 6-40 33 8 20 28 32 49 50 21-18 41-30 49-50 11-27-19-51-40-33-5 4-8 10-9 13-1-3-4-9-9-13z"/></g><g class="svg-zone" @click="chooseZone('midline_chest_abdomen')"><path :class="['organ','aorta',{ picked: selectedZone === 'midline_chest_abdomen' }]" d="M174 126h13c-8 60-2 119 13 177 10 39-19 58-18 100h-14c-1-41 19-67 8-101-17-55-19-114-2-176z"/></g><g class="svg-zone" @click="chooseZone('right_upper_abdomen')"><path :class="['organ','liver',{ picked: selectedZone === 'right_upper_abdomen' }]" d="M178 303c39-18 76-8 88 16-11 30-55 45-105 30-17-5-27-17-22-29 5-12 19-12 39-17z"/></g><g class="svg-zone" @click="chooseZone('left_upper_abdomen')"><path :class="['organ','stomach',{ picked: selectedZone === 'left_upper_abdomen' }]" d="M135 302c39-10 71 15 59 48-8 23-41 35-65 18-20-14-18-58 6-66z"/></g><g class="svg-zone" @click="chooseZone('epigastrium')"><path :class="['organ','pancreas',{ picked: selectedZone === 'epigastrium' }]" d="M129 354c46-22 83-20 111-3-27 13-71 19-116 10z"/></g><g class="svg-zone" @click="chooseZone('central_abdomen')"><path :class="['organ','intestine',{ picked: selectedZone === 'central_abdomen' }]" d="M128 378c35-22 70-20 103 0 14 37-3 77-51 79-48-2-65-42-52-79z"/></g><g class="svg-zone" @click="chooseZone('flank')"><path :class="['organ','kidney',{ picked: selectedZone === 'flank' }]" d="M111 360c-15 17-12 52 8 65 21-11 24-46 9-64-5-4-11-4-17-1zm121 1c-15 18-12 53 9 64 20-13 23-48 8-65-6-3-12-3-17 1z"/></g><g class="svg-zone" @click="chooseZone('pelvis_midline')"><path :class="['organ','bladder',{ picked: selectedZone === 'pelvis_midline' }]" d="M154 464c17-18 35-18 52 0 8 26-4 48-26 49-22-1-34-23-26-49z"/></g><text x="180" y="540" text-anchor="middle">选择器官或体表区域后系统会评分</text></svg></div><aside class="panel anatomy-feedback"><h2>AI评分</h2><div v-if="anatomyResult" class="result-box" :class="{ success: anatomyResult.correct }"><strong>{{ anatomyResult.correct ? '定位正确' : '需要复习' }}</strong><p>{{ anatomyResult.feedback }}</p><p>{{ anatomyResult.clinical_link }}</p></div><div v-else class="empty-state">等待学生选择解剖区域。</div><article v-for="item in anatomyResult?.score_items ?? []" :key="item.name" class="mini-score"><div><strong>{{ item.name }}</strong><span>{{ item.score }}/{{ item.max_score }}</span></div><progress :value="item.score" :max="item.max_score" /></article></aside></div></section>
        <section v-else-if="activeModule === 'graph'" class="graph-module"><div class="module-head"><div><h1>医学教育知识图谱</h1><p>融合教材、病例、症状、疾病、检查、解剖结构、指南和学习目标，支持中英文术语联查。</p></div></div><div class="search-row panel graph-controls"><input v-model="graphQuery" placeholder="搜索 黄疸 / ACS / chest pain / 心脏" /><select v-model="graphType"><option v-for="type in graphTypes" :key="type">{{ type }}</option></select><div class="graph-lang"><button :class="{ active: graphLang === 'zh' }" type="button" @click="graphLang = 'zh'">中文</button><button :class="{ active: graphLang === 'en' }" type="button" @click="graphLang = 'en'">English</button></div></div><div class="graph-layout"><svg class="knowledge-graph" viewBox="0 0 660 470" role="img" aria-label="医学教育知识图谱"><line v-for="edge in visibleGraphEdges" :key="`${edge.source}-${edge.target}-${edge.relation}`" :x1="locate(edge.source).x" :y1="locate(edge.source).y" :x2="locate(edge.target).x" :y2="locate(edge.target).y" /><g v-for="node in visibleGraphNodes" :key="node.id" class="graph-node" @click="selectGraphNode(node)"><circle :class="node.group" :cx="node.x" :cy="node.y" :r="selectedNode?.id === node.id ? 38 : node.group === 'Case' ? 32 : 27" /><text :x="node.x" :y="node.y + 4" text-anchor="middle">{{ graphNodeLabel(node) }}</text></g></svg><aside class="panel node-detail"><span>{{ selectedNode?.group }}</span><h2>{{ graphNodeLabel(selectedNode) }}</h2><p>{{ graphNodeSummary(selectedNode) }}</p><div class="tag-row"><b v-for="source in selectedNode?.source_ids ?? []" :key="source">{{ source }}</b></div><h3>一阶/二阶关联</h3><div class="neighbor-list"><button v-for="edge in selectedNeighbors" :key="`${edge.source}-${edge.target}-${edge.relation}`" type="button" @click="graphQuery = edge.source === selectedNode?.id ? edge.target : edge.source"><strong>{{ edgeLabel(edge) }}</strong><span>{{ edge.source === selectedNode?.id ? edge.target : edge.source }}</span></button></div><h3>推荐学习路径</h3><ol><li v-for="item in learningPath" :key="item">{{ item }}</li></ol></aside></div></section>
        <section v-else-if="activeModule === 'report'" class="report-module panel"><div class="module-head"><div><h1>临床思维训练报告</h1><p>展示本次诊断路径、优点、改进点、推荐复训病例和引用依据。</p></div></div><div class="report-grid"><section><h2>本次诊断路径</h2><ol><li v-for="item in currentReport.diagnosis_path" :key="item">{{ item }}</li></ol></section><section><h2>做得好的地方</h2><ul><li v-for="item in currentReport.strengths" :key="item">{{ item }}</li></ul></section><section><h2>需要改进</h2><ul><li v-for="item in currentReport.improvements" :key="item">{{ item }}</li></ul></section><section><h2>推荐复训</h2><ul><li v-for="item in currentReport.recommended_cases" :key="item">{{ item }}</li></ul></section></div></section>
        <section v-else-if="activeModule === 'teacher'" class="teacher-module"><div class="teacher-hero panel"><div><h1>教师端教学分析</h1><p>围绕班级管理、病例管理和教学分析，不与学生训练界面混用。</p></div><strong>{{ currentDashboard.class_average }}</strong></div><div class="teacher-metrics"><article class="panel"><span>训练完成率</span><strong>{{ currentDashboard.completion_rate ?? 76 }}%</strong></article><article class="panel"><span>训练次数</span><strong>{{ currentDashboard.training_sessions }}</strong></article><article class="panel"><span>需干预学生</span><strong>{{ currentDashboard.intervention_needed ?? 0 }}</strong></article><article class="panel"><span>引用准确率</span><strong>{{ currentDashboard.citation_accuracy }}</strong></article></div><div class="teacher-split"><section class="panel"><h2>学生列表</h2><table><thead><tr><th>姓名</th><th>次数</th><th>均分</th><th>病例</th><th>薄弱点</th><th>干预</th></tr></thead><tbody><tr v-for="student in currentDashboard.students" :key="student.name"><td>{{ student.name }}</td><td>{{ student.sessions }}</td><td>{{ student.average_score }}</td><td>{{ student.last_case }}</td><td>{{ student.weakness }}</td><td>{{ student.needs_intervention ? '需要' : '观察' }}</td></tr></tbody></table></section><section class="panel"><h2>高风险错误排名</h2><article v-for="item in currentDashboard.risk_rankings" :key="item.label" class="risk-row"><strong>{{ item.label }}</strong><span>{{ item.count }}次 · {{ item.level }}风险</span></article><h2>AI教学建议</h2><p v-for="item in currentDashboard.teaching_suggestions" :key="item">{{ item }}</p></section></div></section>
        <section v-else class="cases-module"><div class="module-head"><div><h1>病例管理</h1><p>教师可查看脚本、标准答案、关键得分点、高风险扣分项和推荐依据。</p></div></div><div class="case-admin-grid"><article v-for="item in cases" :key="item.id" class="panel admin-case"><span>{{ item.department }}</span><h2>{{ item.title }}</h2><p>{{ item.chief_complaint }}</p><dl><dt>关键得分点</dt><dd>{{ item.key_scoring_points?.join('、') ?? item.learning_goals.join('、') }}</dd><dt>高风险扣分项</dt><dd>{{ item.high_risk_omissions?.map((risk) => risk.text).join('、') }}</dd></dl></article></div></section>
      </section>
      <aside class="right-rail"><section class="mentor-card panel" :class="[`mentor-${tutorState}`]"><div class="mentor-figure" aria-label="AI数字人导师"><div class="mentor-halo"></div><div class="mentor-portrait"><span class="hair"></span><span class="ear left"></span><span class="ear right"></span><div class="mentor-face"><span class="brow left"></span><span class="brow right"></span><span class="eye left"></span><span class="eye right"></span><span class="nose"></span><span class="mouth"></span></div><span class="neck"></span><div class="mentor-coat"><span class="lapel left"></span><span class="lapel right"></span><span class="tie"></span><span class="stethoscope"></span></div><div class="voice-rings"><span></span><span></span><span></span></div></div></div><div><strong>AI数字人导师</strong><p>{{ tutorLine }}</p><small>{{ voiceMuted ? '语音静音' : 'TTS mock 待接入' }}</small></div><button type="button" @click="playTutor">播放讲解</button><button type="button" class="voice-toggle" @click="voiceMuted = !voiceMuted">{{ voiceMuted ? '开启语音' : '静音' }}</button></section><section class="agent-card panel"><div class="agent-head"><h2>平台 Agent 助手</h2><span>{{ agentLoading ? '处理中' : '在线' }}</span></div><div class="quick-actions"><button type="button" @click="runAgent('我想练胃的位置')">胃定位</button><button type="button" @click="runAgent('打开腹痛病例')">腹痛病例</button><button type="button" @click="runAgent('黄疸要学哪些内容？')">黄疸路径</button></div><div class="agent-input"><textarea v-model="agentInput" rows="3" placeholder="让Agent导航、检索或推荐学习路径" @focus="setListening" /><button class="primary-action" type="button" :disabled="agentLoading" @click="runAgent()">发送</button></div><div class="agent-results" v-if="agentCards.length"><article v-for="card in agentCards" :key="`${card.kind}-${card.title}`"><span>{{ card.kind }}</span><strong>{{ card.title }}</strong><p>{{ card.summary }}</p></article></div></section><section class="score-panel panel"><div class="score-total"><span>综合评分</span><strong>{{ averageScore }}</strong></div><article v-for="item in scores" :key="item.name" class="mini-score"><div><strong>{{ item.name }}</strong><span>{{ item.score }}/{{ item.max_score }}</span></div><progress :value="item.score" :max="item.max_score" /><p>{{ item.feedback }}</p></article><h3>关键遗漏提醒</h3><ul class="missing-list"><li v-for="item in missing" :key="item.id" :class="item.level"><strong>{{ item.text }}</strong><span>{{ item.suggestion }}</span></li></ul></section></aside>
    </section>
  </main>
</template>


