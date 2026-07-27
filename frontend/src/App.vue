<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { getCases, getGuidelines, getKnowledgeGraph, getOverview, getTeacherDashboard, getTrainingReport, getWorkflow, sendPatientMessage } from './api';
import type { CaseSummary, ChatMessage, GuidelineDoc, KnowledgeEdge, KnowledgeNode, MissingPoint, Overview, PatientChatResponse, ScoreItem, TeacherDashboard, TrainingReport, WorkflowStage } from './types';

const useBackend = Boolean(import.meta.env.VITE_API_BASE_URL);
const role = ref<'student' | 'teacher'>('student');
const activeCaseId = ref('emergency_chest_pain');
const input = ref('请问您胸痛是什么性质？有没有向左肩或后背放射？');
const loading = ref(false);
const error = ref('');
const overview = ref<Overview | null>(null);
const cases = ref<CaseSummary[]>([]);
const messages = ref<ChatMessage[]>([
  { role: 'patient', content: '医生，我胸口疼得厉害，大概两小时前开始的。' },
  { role: 'tutor', content: '请先围绕胸痛性质、部位、持续时间、诱因、伴随症状和危险因素进行开放式问诊。' }
]);
const scores = ref<ScoreItem[]>([]);
const missing = ref<MissingPoint[]>([]);
const citations = ref<GuidelineDoc[]>([]);
const workflow = ref<WorkflowStage[]>([]);
const dashboard = ref<TeacherDashboard | null>(null);
const report = ref<TrainingReport | null>(null);
const kgNodes = ref<KnowledgeNode[]>([]);
const kgEdges = ref<KnowledgeEdge[]>([]);

const fallbackOverview: Overview = {
  name: '临思智训',
  subtitle: '面向医学教育的 AI 标准化病人临床思维训练平台',
  contest_track: 'AI+医学学科交叉',
  positioning: '通过 AI 标准化病人、RAG 指南依据、过程性评分和教师反馈闭环训练医学生临床思维。',
  metrics: [
    { label: '虚拟病例', value: '5个', trend: '可扩展病例库' },
    { label: '评分维度', value: '6项', trend: '过程性评价' },
    { label: 'Agent节点', value: '6个', trend: '工作流编排' },
    { label: '知识来源', value: '3类', trend: '指南教材共识' }
  ],
  scenarios: ['学生端', '教师端']
};

const fallbackCases: CaseSummary[] = [
  { id: 'emergency_chest_pain', title: '急诊胸痛', department: '急诊医学', chief_complaint: '胸痛2小时', difficulty: '中级', learning_goals: ['胸痛问诊结构', '急性冠脉综合征识别', '危重鉴别诊断', '检查选择'] },
  { id: 'acute_abdominal_pain', title: '急性腹痛', department: '消化与急诊', chief_complaint: '右下腹痛6小时', difficulty: '初中级', learning_goals: ['腹痛定位', '外科急腹症识别'] },
  { id: 'fever_unknown', title: '发热待查', department: '感染与内科', chief_complaint: '反复发热3天', difficulty: '中级', learning_goals: ['热型问诊', '感染灶定位'] },
  { id: 'dyspnea', title: '呼吸困难', department: '呼吸与急诊', chief_complaint: '活动后气促加重', difficulty: '中级', learning_goals: ['呼吸困难分层', '心肺鉴别'] },
  { id: 'diabetes_education', title: '糖尿病健康宣教', department: '全科医学', chief_complaint: '血糖控制不佳', difficulty: '初级', learning_goals: ['健康宣教', '用药依从性'] }
];

const fallbackGuidelines: GuidelineDoc[] = [
  { id: 'chest_pain_primary', title: '《急性胸痛基层诊疗指南》', source: '教学示例知识库', type: '指南', tags: ['胸痛', '急诊', '心电图'], content: '急性胸痛评估应关注胸痛性质、持续时间、诱因、放射痛、伴随症状和危险因素。' },
  { id: 'acs_guideline', title: '《急性冠脉综合征诊疗指南》', source: '教学示例知识库', type: '指南', tags: ['ACS', '肌钙蛋白'], content: '急性冠脉综合征评估需要结合症状、心电图动态变化和肌钙蛋白结果。' },
  { id: 'diagnostics_chest_pain', title: '《临床诊断学》胸痛章节', source: '教学示例教材', type: '教材', tags: ['问诊', '胸痛性质'], content: '胸痛问诊包括部位、性质、程度、持续时间、诱发缓解因素、放射部位和伴随症状。' }
];

const fallbackWorkflow: WorkflowStage[] = [
  { id: 'patient', name: '病人回复生成', agent: 'PatientAgent', goal: '仅根据病例脚本模拟标准化病人回答。' },
  { id: 'retrieval', name: 'RAG检索指南依据', agent: 'RetrievalAgent', goal: '检索指南、教材和专家共识片段并返回citation。' },
  { id: 'scoring', name: '临床思维评分', agent: 'ScoringAgent', goal: '对六个临床思维维度评分。' },
  { id: 'safety', name: '医学安全边界', agent: 'SafetyAgent', goal: '避免诊断泄露和真实诊疗误用。' },
  { id: 'report', name: '训练报告生成', agent: 'ReportAgent', goal: '生成改进建议和复训病例。' }
];

const fallbackDashboard: TeacherDashboard = {
  class_average: 82,
  training_sessions: 248,
  teacher_time_saved: '41%',
  citation_accuracy: '88%',
  improvements: [
    { label: '临床推理分提升', value: 24 },
    { label: '关键问诊遗漏率下降', value: 32 },
    { label: '指南引用准确率提升', value: 18 }
  ],
  common_missing_points: ['尚未询问胸痛性质', '尚未排除主动脉夹层', '建议申请心电图和肌钙蛋白', '未记录危险因素']
};

const fallbackReport: TrainingReport = {
  case_id: 'emergency_chest_pain',
  diagnosis_path: ['主诉胸痛', '识别ACS危险因素', '补充高危鉴别', '申请心电图和肌钙蛋白', '根据证据更新诊断路径'],
  strengths: ['能关注胸痛持续时间和活动诱因', '能提出急性冠脉综合征作为重点鉴别'],
  improvements: ['需更早询问胸痛性质和放射痛', '需主动排除主动脉夹层和肺栓塞', '需说明指南依据和非诊疗边界'],
  recommended_cases: ['呼吸困难', '急性腹痛', '发热待查'],
  citations: fallbackGuidelines.map((doc) => ({ id: doc.id, title: doc.title, source: doc.source, snippet: doc.content }))
};

const fallbackGraph = {
  nodes: [
    { id: 'chest_pain', label: '胸痛', group: 'symptom' },
    { id: 'acs', label: '急性冠脉综合征', group: 'disease' },
    { id: 'aortic_dissection', label: '主动脉夹层', group: 'differential' },
    { id: 'pulmonary_embolism', label: '肺栓塞', group: 'differential' },
    { id: 'ecg', label: '心电图', group: 'exam' },
    { id: 'troponin', label: '肌钙蛋白', group: 'exam' },
    { id: 'guideline', label: '指南依据', group: 'guideline' },
    { id: 'learning_goal', label: '学习目标', group: 'learning' }
  ],
  edges: [
    { source: 'chest_pain', target: 'acs', relation: '可能提示' },
    { source: 'acs', target: 'ecg', relation: '需要检查' },
    { source: 'acs', target: 'troponin', relation: '需要检查' },
    { source: 'chest_pain', target: 'aortic_dissection', relation: '需要鉴别' },
    { source: 'chest_pain', target: 'pulmonary_embolism', relation: '需要鉴别' },
    { source: 'guideline', target: 'learning_goal', relation: '支撑' }
  ]
};

const activeCase = computed(() => cases.value.find((item) => item.id === activeCaseId.value) ?? fallbackCases[0]);
const currentOverview = computed(() => overview.value ?? fallbackOverview);
const currentDashboard = computed(() => dashboard.value ?? fallbackDashboard);
const currentReport = computed(() => report.value ?? fallbackReport);

const graphNodes = computed(() => {
  const list = kgNodes.value.length ? kgNodes.value : fallbackGraph.nodes;
  return list.map((node, index) => {
    const angle = (Math.PI * 2 * index) / list.length - Math.PI / 2;
    const radius = node.id === 'chest_pain' ? 0 : 170;
    return { ...node, x: 300 + Math.cos(angle) * radius, y: 210 + Math.sin(angle) * radius };
  });
});
const graphEdges = computed(() => kgEdges.value.length ? kgEdges.value : fallbackGraph.edges);

function locate(id: string) {
  return graphNodes.value.find((node) => node.id === id) ?? graphNodes.value[0];
}

function localPatientReply(text: string): PatientChatResponse {
  const reply = text.includes('性质') || text.includes('怎么疼')
    ? '像被重物压住一样，不太像针扎，疼的时候有点喘不过气。'
    : text.includes('放射') || text.includes('左肩')
      ? '主要在胸骨后面，刚才左肩和左臂也有点酸痛。'
      : text.includes('高血压') || text.includes('吸烟') || text.includes('既往')
        ? '我有高血压，平时吃药不规律，抽烟二十多年。'
        : '我只能根据这个虚拟教学病例回答你的问诊问题，目前主要是不舒服和担心。';
  return {
    patient_reply: { role: 'patient', content: reply },
    tutor_hint: '继续补充高危鉴别诊断，并尽早提出心电图和肌钙蛋白检查。',
    scores: [
      { name: '病史采集', score: text.includes('性质') ? 78 : 56, max_score: 100, feedback: '继续补充疼痛性质、放射痛和伴随症状。' },
      { name: '检查选择', score: text.includes('心电图') || text.includes('肌钙蛋白') ? 82 : 48, max_score: 100, feedback: '疑似ACS时应尽早提出心电图和肌钙蛋白。' },
      { name: '鉴别诊断', score: text.includes('主动脉夹层') || text.includes('肺栓塞') ? 76 : 44, max_score: 100, feedback: '需主动排除主动脉夹层、肺栓塞和气胸。' },
      { name: '临床决策', score: 66, max_score: 100, feedback: '建议明确急诊监护和复查路径。' },
      { name: '指南依据', score: 58, max_score: 100, feedback: '需要引用指南或教材依据。' },
      { name: '沟通表达', score: 72, max_score: 100, feedback: '表达较清楚，注意安抚患者并说明教学场景。' }
    ],
    missing_points: [
      { id: 'quality', level: 'warning', text: '尚未询问胸痛性质', suggestion: '追问压榨样、撕裂样、针刺样等疼痛特征。' },
      { id: 'dissection', level: 'danger', text: '尚未排除主动脉夹层', suggestion: '询问撕裂样胸背痛、血压差、神经系统症状。' },
      { id: 'ecg', level: 'warning', text: '建议申请心电图和肌钙蛋白', suggestion: '疑似ACS时应尽早完成心电图和心肌损伤标志物评估。' }
    ].filter((item) => !text.includes(item.text.slice(2, 6))),
    workflow_trace: fallbackWorkflow.map((stage) => ({ ...stage, status: 'done', detail: stage.goal })),
    citations: fallbackGuidelines.map((doc) => ({ id: doc.id, title: doc.title, source: doc.source, snippet: doc.content })),
    safety_notes: ['本病例为虚拟教学病例，不含真实患者信息。', '平台反馈用于医学教学训练，不用于真实临床诊断。']
  };
}

function selectCase(caseId: string) {
  activeCaseId.value = caseId;
  messages.value = [{ role: 'patient', content: caseId === 'emergency_chest_pain' ? '医生，我胸口疼得厉害，大概两小时前开始的。' : '老师好，这是一个虚拟教学病例，请开始问诊。' }];
  const demo = localPatientReply('');
  scores.value = demo.scores;
  missing.value = demo.missing_points;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  messages.value.push({ role: 'student', content: text });
  input.value = '';
  loading.value = true;
  error.value = '';
  try {
    const response = useBackend ? await sendPatientMessage(activeCaseId.value, text, messages.value) : localPatientReply(text);
    messages.value.push(response.patient_reply);
    messages.value.push({ role: 'tutor', content: response.tutor_hint });
    scores.value = response.scores;
    missing.value = response.missing_points;
  } catch (err) {
    error.value = err instanceof Error ? err.message : '问诊请求失败，已切换为本地演示。';
    const response = localPatientReply(text);
    messages.value.push(response.patient_reply);
    scores.value = response.scores;
    missing.value = response.missing_points;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (useBackend) {
    try {
      const [site, caseData, guidelineData, workflowData, dashboardData, reportData, graphData] = await Promise.all([
        getOverview(), getCases(), getGuidelines(), getWorkflow(), getTeacherDashboard(), getTrainingReport(activeCaseId.value), getKnowledgeGraph()
      ]);
      overview.value = site;
      cases.value = caseData;
      citations.value = guidelineData;
      workflow.value = workflowData.stages;
      dashboard.value = dashboardData;
      report.value = reportData;
      kgNodes.value = graphData.nodes;
      kgEdges.value = graphData.edges;
    } catch {
      cases.value = fallbackCases;
      citations.value = fallbackGuidelines;
      workflow.value = fallbackWorkflow;
      dashboard.value = fallbackDashboard;
      report.value = fallbackReport;
      kgNodes.value = fallbackGraph.nodes;
      kgEdges.value = fallbackGraph.edges;
    }
  } else {
    cases.value = fallbackCases;
    citations.value = fallbackGuidelines;
    workflow.value = fallbackWorkflow;
    dashboard.value = fallbackDashboard;
    report.value = fallbackReport;
    kgNodes.value = fallbackGraph.nodes;
    kgEdges.value = fallbackGraph.edges;
  }
  const demo = localPatientReply(input.value);
  scores.value = demo.scores;
  missing.value = demo.missing_points;
});
</script>

<template>
  <main class="app-shell">
    <nav class="top-nav">
      <a class="brand" href="#training"><span>临</span><strong>临思智训</strong></a>
      <div class="nav-links">
        <a href="#training">病例训练</a>
        <a href="#guidelines">指南知识库</a>
        <a href="#teacher">教师看板</a>
        <a href="#report">训练报告</a>
      </div>
      <div class="role-switch" aria-label="角色切换">
        <button :class="{ active: role === 'student' }" type="button" @click="role = 'student'">学生端</button>
        <button :class="{ active: role === 'teacher' }" type="button" @click="role = 'teacher'">教师端</button>
      </div>
    </nav>

    <section class="hero-band">
      <div>
        <p class="kicker">{{ currentOverview.contest_track }}</p>
        <h1>{{ currentOverview.subtitle }}</h1>
        <p class="hero-copy">{{ currentOverview.positioning }} 平台仅用于虚拟医学教学病例，不用于真实临床诊断。</p>
      </div>
      <div class="metric-grid">
        <article v-for="metric in currentOverview.metrics" :key="metric.label">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <p>{{ metric.trend }}</p>
        </article>
      </div>
    </section>

    <section id="training" class="training-grid">
      <aside class="case-list panel">
        <h2>病例列表</h2>
        <button v-for="item in cases" :key="item.id" :class="['case-item', { active: activeCaseId === item.id }]" type="button" @click="selectCase(item.id)">
          <strong>{{ item.title }}</strong>
          <span>{{ item.department }} · {{ item.difficulty }}</span>
          <small>{{ item.chief_complaint }}</small>
        </button>
      </aside>

      <section class="chat-panel panel">
        <div class="case-header">
          <div>
            <p class="kicker">AI标准化病人训练</p>
            <h2>{{ activeCase.title }}</h2>
            <p>{{ activeCase.learning_goals.join(' / ') }}</p>
          </div>
          <span>虚拟教学病例</span>
        </div>
        <div class="chat-window">
          <article v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
            <b>{{ message.role === 'student' ? '学生' : message.role === 'patient' ? 'AI病人' : 'TutorAgent' }}</b>
            <p>{{ message.content }}</p>
          </article>
        </div>
        <div class="chat-input">
          <textarea v-model="input" rows="3" placeholder="输入问诊问题，例如：胸痛是什么性质？是否放射到左肩？" />
          <button class="primary-action" type="button" :disabled="loading" @click="sendMessage">{{ loading ? '生成中' : '发送问诊' }}</button>
        </div>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <aside class="score-panel panel">
        <h2>临床思维评分</h2>
        <div class="score-list">
          <article v-for="item in scores" :key="item.name">
            <div><strong>{{ item.name }}</strong><span>{{ item.score }}/{{ item.max_score }}</span></div>
            <progress :value="item.score" :max="item.max_score" />
            <p>{{ item.feedback }}</p>
          </article>
        </div>
        <h3>关键遗漏提醒</h3>
        <ul class="missing-list">
          <li v-for="item in missing" :key="item.id" :class="item.level">
            <strong>{{ item.text }}</strong>
            <span>{{ item.suggestion }}</span>
          </li>
        </ul>
      </aside>
    </section>

    <section id="guidelines" class="knowledge-section">
      <div class="section-head"><h2>可追溯指南知识库</h2><p>每条AI反馈预留citation字段，后续可替换为真实指南、教材、专家共识和院校课程资料。</p></div>
      <div class="guideline-grid">
        <article v-for="doc in citations" :key="doc.id" class="panel guideline-card">
          <span>{{ doc.type }}</span>
          <h3>{{ doc.title }}</h3>
          <p>{{ doc.content }}</p>
          <button type="button">查看依据</button>
        </article>
      </div>
    </section>

    <section class="workflow-section">
      <div class="section-head"><h2>Agent + Workflow 工作流</h2><p>学生输入后，系统按病例上下文、安全边界、病人回复、RAG检索、评分、遗漏检测和报告生成推进。</p></div>
      <div class="workflow-rail">
        <article v-for="stage in workflow" :key="stage.id" class="panel workflow-card">
          <strong>{{ stage.agent }}</strong>
          <h3>{{ stage.name }}</h3>
          <p>{{ stage.goal }}</p>
        </article>
      </div>
    </section>

    <section id="teacher" class="teacher-section">
      <div class="section-head"><h2>教师看板</h2><p>帮助教师发现班级共性遗漏点，减少人工批改时间，形成教学反馈闭环。</p></div>
      <div class="teacher-grid">
        <article class="panel dashboard-number"><span>班级平均分</span><strong>{{ currentDashboard.class_average }}</strong></article>
        <article class="panel dashboard-number"><span>学生训练次数</span><strong>{{ currentDashboard.training_sessions }}</strong></article>
        <article class="panel dashboard-number"><span>批改时间减少</span><strong>{{ currentDashboard.teacher_time_saved }}</strong></article>
        <article class="panel dashboard-number"><span>指南引用准确率</span><strong>{{ currentDashboard.citation_accuracy }}</strong></article>
      </div>
      <div class="improvement-grid">
        <article v-for="item in currentDashboard.improvements" :key="item.label" class="panel">
          <div><strong>{{ item.label }}</strong><span>{{ item.value }}%</span></div>
          <progress :value="item.value" max="100" />
        </article>
      </div>
    </section>

    <section id="report" class="report-section">
      <div class="panel report-card">
        <h2>训练报告</h2>
        <div class="report-columns">
          <section><h3>本次诊断路径</h3><ol><li v-for="item in currentReport.diagnosis_path" :key="item">{{ item }}</li></ol></section>
          <section><h3>做得好的地方</h3><ul><li v-for="item in currentReport.strengths" :key="item">{{ item }}</li></ul></section>
          <section><h3>需要改进</h3><ul><li v-for="item in currentReport.improvements" :key="item">{{ item }}</li></ul></section>
          <section><h3>推荐复训病例</h3><ul><li v-for="item in currentReport.recommended_cases" :key="item">{{ item }}</li></ul></section>
        </div>
      </div>
    </section>

    <section class="graph-section">
      <div class="section-head"><h2>医学教育知识图谱</h2><p>覆盖疾病、症状、体征、检查、诊断、鉴别诊断、治疗原则、指南依据和学习目标。</p></div>
      <svg class="knowledge-graph" viewBox="0 0 600 420" role="img" aria-label="医学教育知识图谱">
        <line v-for="edge in graphEdges" :key="`${edge.source}-${edge.target}`" :x1="locate(edge.source).x" :y1="locate(edge.source).y" :x2="locate(edge.target).x" :y2="locate(edge.target).y" />
        <g v-for="node in graphNodes" :key="node.id">
          <circle :cx="node.x" :cy="node.y" :r="node.id === 'chest_pain' ? 38 : 28" />
          <text :x="node.x" :y="node.y + 4" text-anchor="middle">{{ node.label }}</text>
        </g>
      </svg>
    </section>
  </main>
</template>
