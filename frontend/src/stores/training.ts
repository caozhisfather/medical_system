import { computed, reactive } from 'vue';
import { getCases, login, orderTrainingTest, sendPatientMessage, startTraining, submitTrainingDiagnosis } from '../api';
import { mockCases } from '../data/cases';
import type { CaseSummary, ChatMessage, Citation, MissingPoint, ScoreItem } from '../types';

export type WorkspaceRole = 'student' | 'teacher' | 'admin';

export interface UserProfile {
  role: WorkspaceRole;
  name: string;
  school: string;
  grade: string;
  specialty: string;
  className: string;
  direction: string;
  completed: boolean;
}

export interface ClinicalDraft {
  hypotheses: string[];
  finalDiagnosis: string;
  differentials: string;
  examinations: string;
  plan: string;
  medicationPlan: string;
  evidence: string;
}

export interface ReportDimension {
  label: string;
  score: number;
  feedback: string;
}

export interface TrainingReportRecord {
  id: string;
  caseId: string;
  caseTitle: string;
  completedAt: string;
  duration: string;
  score: number;
  status: '待教师复核' | '教师已复核';
  dimensions: ReportDimension[];
  strengths: string[];
  improvements: string[];
  highRiskMisses: string[];
  citations: Citation[];
  learningPath: string[];
  diagnosisPath: string[];
  transcript?: ChatMessage[];
  clinicalDecision?: { diagnosis: string; differentials: string; examinations: string; treatment: string; medicationPlan: string; evidence: string };
  assessmentSource?: 'backend-ai' | 'offline-fallback';
  teacherComment?: string;
}

export interface TrainingSession {
  id: string;
  backendSessionId?: string;
  caseId: string;
  variantId: string;
  difficulty: string;
  mode: string;
  patientMode: 'text' | 'digital';
  focus?: string;
  startedAt: number;
  messages: ChatMessage[];
  scores: ScoreItem[];
  missingPoints: MissingPoint[];
  citations: Citation[];
  unlockedExams: string[];
  draft: ClinicalDraft;
  patientState: { stage: string; completed: string[]; progress: number; lastCollected?: string };
}

const defaultProfile: UserProfile = {
  role: 'student',
  name: '陈同学',
  school: '东部医科大学',
  grade: '临床医学四年级',
  specialty: '临床医学',
  className: '临床医学 2023-2 班',
  direction: '急诊与内科临床思维',
  completed: false
};

const initialHistory: TrainingReportRecord[] = [
  {
    id: 'TR-260728-01',
    caseId: 'emergency_chest_pain',
    caseTitle: '急诊胸痛',
    completedAt: '2026-07-28 14:32',
    duration: '18 分 24 秒',
    score: 86,
    status: '教师已复核',
    dimensions: [
      { label: '问诊完整性', score: 88, feedback: '现病史结构完整。' },
      { label: '关键信息捕捉', score: 90, feedback: '识别出活动诱发与出汗。' },
      { label: '鉴别诊断覆盖', score: 82, feedback: '需进一步强化肺栓塞排查。' },
      { label: '临床推理逻辑', score: 86, feedback: '证据链基本连贯。' },
      { label: '检查处理合理性', score: 89, feedback: '及时选择心电图和肌钙蛋白。' },
      { label: '医患沟通', score: 84, feedback: '表达清楚，可增加安抚。' },
      { label: '证据引用准确率', score: 83, feedback: '引用与结论基本匹配。' }
    ],
    strengths: ['能迅速识别急性冠脉综合征高危线索', '检查选择有明确优先级'],
    improvements: ['补充撕裂样疼痛及背部放射追问', '说明肺栓塞风险分层依据'],
    highRiskMisses: ['主动脉夹层相关追问略晚'],
    citations: [
      { id: 'CP-G01', title: '急性胸痛基层诊疗指南', source: '指南知识库', snippet: '胸痛患者应尽早完成危险分层与心电图评估。' },
      { id: 'CP-G02', title: '急性冠脉综合征诊疗指南', source: '指南知识库', snippet: '肌钙蛋白应结合动态变化进行判断。' }
    ],
    learningPath: ['胸痛高危鉴别', '心电图动态改变', '肺栓塞风险分层'],
    diagnosisPath: ['活动后胸骨后压榨痛', '识别心血管危险因素', '提出急性冠脉综合征假设', '排除致命性胸痛', '用检查证据修正判断'],
    teacherComment: '推理主线清楚，下次训练重点提前处理致命性鉴别。'
  },
  {
    id: 'TR-260726-02',
    caseId: 'dyspnea',
    caseTitle: '呼吸困难',
    completedAt: '2026-07-26 19:08',
    duration: '21 分 07 秒',
    score: 74,
    status: '待教师复核',
    dimensions: [],
    strengths: ['注意到静息血氧偏低'],
    improvements: ['补充端坐呼吸和夜间阵发性呼吸困难', '区分心衰和慢阻肺急性加重'],
    highRiskMisses: ['未及时评估肺栓塞风险'],
    citations: [],
    learningPath: ['动脉血气分析', '心源性与肺源性呼吸困难', '肺栓塞风险'],
    diagnosisPath: ['活动后气促', '低氧评估', '心肺鉴别']
  },
  {
    id: 'TR-260724-04',
    caseId: 'emergency_chest_pain',
    caseTitle: '急诊胸痛',
    completedAt: '2026-07-24 10:06',
    duration: '22 分 18 秒',
    score: 76,
    status: '教师已复核',
    dimensions: [
      { label: '问诊完整性', score: 78, feedback: '基础问诊完成，但高危线索追问偏晚。' },
      { label: '关键信息捕捉', score: 80, feedback: '识别胸痛，但危险因素整合不足。' },
      { label: '鉴别诊断覆盖', score: 68, feedback: '未充分覆盖主动脉夹层和肺栓塞。' },
      { label: '临床推理逻辑', score: 74, feedback: '诊断假设与检查依据连接不够紧密。' },
      { label: '检查处理合理性', score: 79, feedback: '心电图选择合理，检查优先级仍需调整。' },
      { label: '医患沟通', score: 77, feedback: '沟通清楚，但风险解释不足。' },
      { label: '证据引用准确率', score: 72, feedback: '指南证据与结论匹配度不足。' }
    ],
    strengths: ['能够识别胸痛需要紧急评估'],
    improvements: ['补充撕裂样疼痛及背部放射追问', '说明肺栓塞风险分层依据', '明确心电图与肌钙蛋白检查优先级'],
    highRiskMisses: ['未及时排除主动脉夹层', '未系统评估肺栓塞风险'],
    citations: [],
    learningPath: ['胸痛高危鉴别', '心电图动态改变', '肺栓塞风险分层'],
    diagnosisPath: ['胸骨后疼痛', '考虑急性冠脉综合征', '安排心电图', '补充鉴别诊断'],
    teacherComment: '建议完成同病例复训，重点训练致命性胸痛排除顺序。'
  },
  {
    id: 'TR-260723-03',
    caseId: 'acute_abdominal_pain',
    caseTitle: '急性腹痛',
    completedAt: '2026-07-23 16:16',
    duration: '16 分 40 秒',
    score: 81,
    status: '教师已复核',
    dimensions: [],
    strengths: ['识别转移性右下腹痛'],
    improvements: ['完善育龄期女性妊娠相关风险排查'],
    highRiskMisses: ['腹膜刺激征记录不完整'],
    citations: [],
    learningPath: ['急腹症查体', '育龄期女性腹痛', '影像选择'],
    diagnosisPath: ['脐周痛转移右下腹', '腹膜刺激征', '外科急腹症鉴别']
  }
];

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : fallback;
  } catch {
    return fallback;
  }
}

function persist(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value));
}

function hasStoredSession() {
  return Boolean(localStorage.getItem('medical_auth_token')) || readStored('medical_auth', false);
}

function readHistory() {
  const stored = readStored<TrainingReportRecord[]>('medical_history', initialHistory);
  const demoBaseline = initialHistory.find((item) => item.id === 'TR-260724-04');
  if (demoBaseline && !stored.some((item) => item.id === demoBaseline.id)) return [...stored, demoBaseline];
  return stored;
}

const state = reactive({
  authenticated: hasStoredSession(),
  profile: readStored<UserProfile>('medical_profile', defaultProfile),
  cases: mockCases as unknown as CaseSummary[],
  casesLoaded: false,
  session: null as TrainingSession | null,
  history: readHistory()
});

function caseById(caseId: string) {
  return state.cases.find((item) => item.id === caseId) ?? state.cases[0];
}

function variantFor(caseData: CaseSummary, variantId: string) {
  return caseData.case_variants?.find((item) => item.variant_id === variantId) ?? caseData.case_variants?.[0];
}

function openingFor(caseData: CaseSummary, variantId = 'A') {
  return variantFor(caseData, variantId)?.opening_statement ?? caseData.opening_statement ?? caseData.opening ?? caseData.script?.opening ?? `医生您好，我主要不舒服是${caseData.chief_complaint}。`;
}

function citationsFor(caseData: CaseSummary): Citation[] {
  return (caseData.recommended_guidelines ?? []).map((title, index) => ({
    id: `${caseData.id}-E${index + 1}`,
    title,
    source: '可追溯医学教育知识库',
    snippet: `${caseData.title}训练依据，提交临床思维后可查看完整证据片段。`
  }));
}

function localReply(caseData: CaseSummary, question: string): ChatMessage {
  if (/诊断|什么病|最终结果|病名/.test(question)) {
    return { role: 'patient', content: '我不知道最终诊断，只能把我经历的症状和已知情况告诉您。' };
  }
  const matched = caseData.script?.answers?.find((answer) =>
    answer.keywords.some((keyword) => question.includes(keyword))
  );
  if (matched) return { role: 'patient', content: matched.reply };
  return { role: 'patient', content: caseData.patient_answer_rules?.unknown_answer ?? '这个我不太清楚，医生您能再具体问一下吗？' };
}
function localScores(caseData: CaseSummary, transcript: string): ScoreItem[] {
  const pointHits = (caseData.key_scoring_points ?? []).filter((point) =>
    point.split(/[、和与]/).some((part) => part.length > 1 && transcript.includes(part))
  ).length;
  const examHits = (caseData.available_exams ?? []).filter((exam) => transcript.includes(exam)).length;
  const diffHits = (caseData.differential_diagnoses ?? []).filter((diagnosis) => transcript.includes(diagnosis)).length;
  return [
    { name: '病史采集', score: Math.min(94, 58 + pointHits * 9), max_score: 100, feedback: '根据病例关键追问点动态更新。' },
    { name: '检查选择', score: Math.min(94, 52 + examHits * 8), max_score: 100, feedback: '根据已提出检查项目更新。' },
    { name: '鉴别诊断', score: Math.min(94, 48 + diffHits * 11), max_score: 100, feedback: '根据鉴别诊断覆盖度更新。' }
  ];
}

function localMissing(caseData: CaseSummary, transcript: string): MissingPoint[] {
  return (caseData.high_risk_omissions ?? []).filter((item) =>
    !(item.keywords ?? []).some((keyword) => transcript.includes(keyword.replace(/询问|排除|申请|评估|安排|鉴别|追问|查/, '')))
  ).map((item) => ({ ...item, citation: citationsFor(caseData)[0] ?? null }));
}

export const trainingStore = {
  state,
  activeCase: computed(() => caseById(state.session?.caseId ?? 'emergency_chest_pain')),
  lastReport: computed(() => state.history[0]),

  async loadCases() {
    if (state.casesLoaded) return;
    try {
      const remote = await getCases();
      if (remote.length >= 4) state.cases = remote;
    } catch {
      state.cases = mockCases as unknown as CaseSummary[];
    } finally {
      state.casesLoaded = true;
    }
  },

  async refreshCases() {
    const remote = await getCases();
    if (remote.length) state.cases = remote;
    state.casesLoaded = true;
  },

  signIn(role: WorkspaceRole) {
    state.authenticated = true;
    state.profile = { ...state.profile, role };
    if (import.meta.env.DEV) {
      const demoTokens: Record<WorkspaceRole, string> = {
        student: 'mock-student-student01-token',
        teacher: 'mock-teacher-teacher01-token',
        admin: 'mock-super_admin-admin-token'
      };
      localStorage.setItem('medical_auth_token', demoTokens[role]);
    }
    persist('medical_auth', true);
    persist('medical_profile', state.profile);
  },

  async authenticate(account: string, password: string, role: WorkspaceRole, rememberAccount = true) {
    let response;
    try {
      response = await login(account, password, role);
    } catch (error) {
      if (error instanceof TypeError) throw new Error('登录服务暂时无法连接，请确认后端服务已启动。');
      throw error;
    }
    const responseRole: WorkspaceRole = response.user.role === 'super_admin' ? 'admin' : response.user.role as WorkspaceRole;
    if (responseRole !== role) throw new Error('该账号不属于当前选择的身份，请切换身份后重试。');
    const roleProfile = role === 'teacher'
      ? { grade: response.user.department || '诊断学教研室', specialty: '诊断学与临床技能', className: '临床医学 2023-2 班', direction: '诊断学与临床技能' }
      : role === 'admin'
        ? { grade: response.user.department || '系统管理中心', specialty: '平台运维与知识工程', className: '全校医学教学空间', direction: '数据源与复盘策略' }
        : { grade: response.user.department || '临床医学四年级', specialty: '临床医学', className: '临床医学 2023-2 班', direction: '急诊与内科临床思维' };
    state.authenticated = true;
    state.profile = { ...state.profile, ...roleProfile, role, name: response.user.name, completed: true };
    localStorage.setItem('medical_auth_token', response.token);
    persist('medical_auth', true);
    persist('medical_profile', state.profile);
    if (rememberAccount) localStorage.setItem(`medical_login_account_${role}`, account);
    else localStorage.removeItem(`medical_login_account_${role}`);
    return response;
  },

  signOut() {
    state.authenticated = false;
    localStorage.removeItem('medical_auth_token');
    persist('medical_auth', false);
  },

  saveProfile(profile: Partial<UserProfile>) {
    state.profile = { ...state.profile, ...profile, completed: true };
    persist('medical_profile', state.profile);
  },

  startSession(caseId: string, difficulty = '标准', mode = '完整训练', variantId = 'A', focus = '', patientMode: 'text' | 'digital' = 'text') {
    const caseData = caseById(caseId);
    const session: TrainingSession = {
      id: `S-${Date.now()}`,
      caseId,
      variantId,
      difficulty,
      mode,
      patientMode,
      focus,
      startedAt: Date.now(),
      messages: [
        { role: 'patient', content: openingFor(caseData, variantId) },
        { role: 'tutor', content: `当前为${variantFor(caseData, variantId)?.label ?? `病例变体 ${variantId}`}。请围绕“${caseData.chief_complaint}”完成结构化问诊，患者不会主动泄露诊断。${focus ? `本次专项复训重点：${focus}。` : ''}` }
      ],
      scores: localScores(caseData, ''),
      missingPoints: localMissing(caseData, ''),
      citations: citationsFor(caseData),
      unlockedExams: [],
      draft: { hypotheses: [], finalDiagnosis: '', differentials: '', examinations: '', plan: '', medicationPlan: '', evidence: '' }
      ,patientState: { stage: 'chief_complaint', completed: [], progress: 0 }
    };
    state.session = session;
    void startTraining(caseId, variantId, difficulty, mode).then((result) => {
      if (state.session?.id === session.id) state.session.backendSessionId = result.session_id;
    }).catch(() => undefined);
    return session;
  },

  ensureSession(caseId: string) {
    if (!state.session || state.session.caseId !== caseId) return this.startSession(caseId);
    return state.session;
  },

  async askPatient(question: string) {
    if (!state.session) return;
    const session = state.session;
    const caseData = caseById(session.caseId);
    session.messages.push({ role: 'student', content: question });
    try {
      const response = await sendPatientMessage(caseData.id, question, session.messages, session.backendSessionId, session.variantId);
      session.messages.push(response.patient_reply);
      session.messages.push({ role: 'tutor', content: response.tutor_hint, citations: response.citations });
      session.scores = response.scores;
      session.missingPoints = response.missing_points;
      session.citations = response.citations;
      if (response.patient_state) session.patientState = { stage: response.patient_state.stage, completed: response.patient_state.completed, progress: response.patient_state.progress, lastCollected: response.patient_state.last_collected };
    } catch {
      session.messages.push(localReply(caseData, question));
      const transcript = session.messages.map((item) => item.content).join(' ');
      session.scores = localScores(caseData, transcript);
      session.missingPoints = localMissing(caseData, transcript);
    }
  },

  async unlockExam(exam: string) {
    if (!state.session || state.session.unlockedExams.includes(exam)) return;
    const session = state.session;
    if (session.backendSessionId) {
      try {
        const result = await orderTrainingTest(session.backendSessionId, exam);
        if (!result.available) return;
      } catch {
        // The local case result keeps the prototype usable offline.
      }
    }
    session.unlockedExams.push(exam);
  },

  async submitSession() {
    if (!state.session) return null;
    const session = state.session;
    const caseData = caseById(session.caseId);
    const transcript = session.messages.map((item) => item.content).join(' ');
    const draft = Object.values(session.draft).flat().join(' ');
    const combined = `${transcript} ${draft}`;
    const pointHits = (caseData.key_scoring_points ?? []).filter((point) =>
      point.split(/[、和与]/).some((part) => part.length > 1 && combined.includes(part))
    ).length;
    const diffHits = (caseData.differential_diagnoses ?? []).filter((item) => combined.includes(item)).length;
    const examHits = (caseData.available_exams ?? []).filter((item) => combined.includes(item)).length;
    let dimensions: ReportDimension[] = [
      { label: '问诊完整性', score: Math.min(96, 62 + pointHits * 8), feedback: '依据病史结构和病例关键追问点评分。' },
      { label: '关键信息捕捉', score: Math.min(95, 60 + pointHits * 9), feedback: '评估主诉、高危线索与危险因素识别。' },
      { label: '鉴别诊断覆盖', score: Math.min(94, 55 + diffHits * 10), feedback: '评估核心诊断与致命性鉴别覆盖。' },
      { label: '临床推理逻辑', score: Math.min(93, 66 + pointHits * 5 + diffHits * 3), feedback: '评估证据、假设与决策之间的连贯性。' },
      { label: '检查处理合理性', score: Math.min(95, 58 + examHits * 8), feedback: '评估检查优先级与处理原则。' },
      { label: '教学用药与安全', score: session.draft.medicationPlan ? 78 : 40, feedback: session.draft.medicationPlan ? '已提交教学用药方案，评估药物要素与安全监测。' : '未提交教学用药方案。' },
      { label: '医患沟通能力', score: Math.min(92, 72 + Math.min(16, session.messages.length)), feedback: '评估表达、倾听与风险沟通。' },
      { label: '指南证据引用准确率', score: session.draft.evidence ? 88 : 62, feedback: '评估引用与临床判断的匹配程度。' }
    ];
    let score = Math.round(dimensions.reduce((sum, item) => sum + item.score, 0) / dimensions.length);
    let assessmentSource: TrainingReportRecord['assessmentSource'] = 'offline-fallback';
    if (session.backendSessionId) {
      try {
        const assessment = await submitTrainingDiagnosis(session.backendSessionId, {
          preliminary_diagnosis: session.draft.finalDiagnosis || session.draft.hypotheses[0] || '',
          differentials: session.draft.differentials.split(/[、，,；;]/).filter(Boolean),
          treatment_principles: session.draft.plan,
          medication_plan: session.draft.medicationPlan,
          citations: session.draft.evidence ? [session.draft.evidence] : []
        });
        dimensions = assessment.scores.map((item) => ({ label: item.name, score: item.score, feedback: item.feedback }));
        score = assessment.total_score;
        session.missingPoints = assessment.missing_points;
        assessmentSource = 'backend-ai';
      } catch {
        assessmentSource = 'offline-fallback';
      }
    }
    const report: TrainingReportRecord = {
      id: `TR-${Date.now()}`,
      caseId: caseData.id,
      caseTitle: caseData.title,
      completedAt: new Date().toLocaleString('zh-CN', { hour12: false }),
      duration: `${Math.max(6, Math.round((Date.now() - session.startedAt) / 60000))} 分钟`,
      score,
      status: '待教师复核',
      dimensions,
      strengths: [
        `能围绕“${caseData.chief_complaint}”建立初步问题表征`,
        examHits > 0 ? '检查选择与当前临床假设存在对应关系' : '能够维持结构化问诊节奏'
      ],
      improvements: session.missingPoints.slice(0, 3).map((item) => item.suggestion),
      highRiskMisses: session.missingPoints.filter((item) => item.level === 'danger').map((item) => item.text),
      citations: session.citations,
      learningPath: caseData.recommended_retraining ?? [],
      transcript: session.messages.map((item) => ({ ...item, citations: item.citations ? [...item.citations] : undefined })),
      clinicalDecision: {
        diagnosis: session.draft.finalDiagnosis || session.draft.hypotheses[0] || '未提交',
        differentials: session.draft.differentials || '未提交',
        examinations: session.draft.examinations || session.unlockedExams.join('、') || '未提交',
        treatment: session.draft.plan || '未提交',
        medicationPlan: session.draft.medicationPlan || '未提交',
        evidence: session.draft.evidence || '未提交'
      },
      assessmentSource,
      diagnosisPath: [
        caseData.chief_complaint,
        '补充现病史与危险因素',
        `形成假设：${session.draft.hypotheses.join('、') || '待完善'}`,
        `提交诊断：${session.draft.finalDiagnosis || '待完善'}`,
        `提出鉴别：${session.draft.differentials || (caseData.differential_diagnoses ?? []).slice(0, 3).join('、')}`,
        `检查验证：${session.draft.examinations || session.unlockedExams.join('、') || '待完善'}`,
        `教学用药：${session.draft.medicationPlan || '待完善'}`,
        '结合指南证据完成后台评估'
      ]
    };
    state.history = [report, ...state.history];
    persist('medical_history', state.history);
    return report;
  },

  reportById(id: string) {
    return state.history.find((item) => item.id === id) ?? state.history[0];
  }
};



