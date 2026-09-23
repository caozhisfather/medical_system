import type { AgentResponse, AnatomyEvidenceResponse, AnatomyExercise, AnatomyLearningRecordsResponse, AnatomyMistake, AnatomyNote, AnatomyResult, AnatomyTextbookResult, AuthResponse, CaseLibraryDeidentifyResult, CaseLibraryEntry, CaseLibraryImportReport, CaseLibraryListResponse, CaseSummary, ChatMessage, ClassroomDetail, ClassroomGuidance, ClassroomSummary, DailyReview, DailyReviewClassSummary, DailyReviewPolicy, DataSourceItem, ExamSettings, GuidelineDoc, HistoryTakingTemplate, KnowledgeEdge, KnowledgeItem, KnowledgeNode, Overview, PatientChatResponse, QuizGrade, QuizLearningRecordsResponse, QuizSet, RagResponse, TeacherCaseDraft, TeacherCaseRecommendations, TeacherDashboard, TextbookStage, TrainingAssessment, TrainingReport, TtsResponse } from './types';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
import type { SkillCall, SkillDefinition, SkillPolicy, SkillQuery, SkillResult } from './types';
import type { DigitalHumanModesResponse, DigitalHumanResponse, DigitalHumanSpeakRequest } from './types';

export function getAdminSkills() { return readJson<SkillDefinition[]>('/api/admin/skills'); }
export function getSkillCalls() { return readJson<{ items: SkillCall[] }>('/api/admin/skills/calls'); }
export async function updateSkill(id: string, policy: SkillPolicy) {
  const response = await fetch(`${baseUrl}/api/admin/skills/${encodeURIComponent(id)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(policy) });
  if (!response.ok) throw new Error(await requestError(response));
  return response.json() as Promise<SkillDefinition>;
}
export function testSkill(id: string, query: SkillQuery) { return postJson<SkillResult>(`/api/admin/skills/${encodeURIComponent(id)}/test`, query); }

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('medical_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requestError(response: Response) {
  try {
    const payload = await response.json() as { detail?: string; message?: string };
    return payload.detail || payload.message || `请求失败（${response.status}）`;
  } catch {
    return `请求失败（${response.status}）`;
  }
}

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`, { headers: authHeaders() });
  if (!response.ok) throw new Error(await requestError(response));
  return response.json() as Promise<T>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await requestError(response));
  return response.json() as Promise<T>;
}

export function getOverview() { return readJson<Overview>('/api/site/overview'); }
export function getCases() { return readJson<CaseSummary[]>('/api/cases'); }
export function searchCases(filters: { q?: string; department?: string; symptom?: string; difficulty?: string; training_goal?: string }) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value); });
  return readJson<{ count: number; items: CaseSummary[] }>(`/api/cases/search?${params.toString()}`);
}
export function getCaseVariants(caseId: string) { return readJson<{ case_id: string; core_diagnosis_locked: boolean; variants: NonNullable<CaseSummary['case_variants']> }>(`/api/cases/${encodeURIComponent(caseId)}/variants`); }
export function getRandomCase(filters: { department?: string; symptom?: string; difficulty?: string; training_goal?: string } = {}) { return postJson<CaseSummary>('/api/cases/random', filters); }
export function getCase(caseId: string) { return readJson<Record<string, unknown>>(`/api/cases/${encodeURIComponent(caseId)}`); }
export function getWorkflow() { return readJson<{ name: string; stages: Array<{ id: string; name: string; agent: string; goal: string }> }>('/api/workflow'); }
export function getGuidelines() { return readJson<GuidelineDoc[]>('/api/guidelines'); }
export function getKnowledge() { return readJson<KnowledgeItem[]>('/api/knowledge'); }
export function searchKnowledge(q: string, lang = 'zh') { return readJson<{ query: string; count: number; items: Array<{ kind: string; title: string; summary: string; target: string }> }>(`/api/knowledge/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}`); }
export function getTeacherDashboard() { return readJson<TeacherDashboard>('/api/teacher/dashboard'); }
export function getTeacherCaseDrafts() { return readJson<TeacherCaseDraft[]>('/api/teacher/case-drafts'); }
export function generateTeacherCaseDraft(payload: { title: string; department: string; chief_complaint: string; learning_goal: string; difficulty: string; suspected_diagnosis: string; source_summary: string; recommendation_id?: string }) { return postJson<TeacherCaseDraft>('/api/teacher/case-drafts/generate', payload); }
export function editTeacherCaseDraft(draftId: string, payload: { title?: string; department?: string; chief_complaint?: string; difficulty?: string; suspected_diagnosis?: string; present_illness?: string; learning_goal?: string; teacher_note?: string }) {
  return fetch(`${baseUrl}/api/teacher/case-drafts/${encodeURIComponent(draftId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  }).then(async (response) => {
    if (!response.ok) throw new Error(await requestError(response));
    return response.json() as Promise<TeacherCaseDraft>;
  });
}
export function decideTeacherCaseDraft(draftId: string, action: 'approve' | 'reject' | 'request_revision', note: string) { return postJson<TeacherCaseDraft>(`/api/teacher/case-drafts/${encodeURIComponent(draftId)}/decision`, { action, note }); }
export function getTeacherCaseRecommendations() { return readJson<TeacherCaseRecommendations>('/api/teacher/case-recommendations'); }
export function decideTeacherCaseRecommendation(recommendationId: string, action: 'accept' | 'dismiss', note = '') { return postJson<{ recommendation_id: string; decision: { action: 'accept' | 'dismiss'; note: string } }>(`/api/teacher/case-recommendations/${encodeURIComponent(recommendationId)}/decision`, { action, note }); }
export function getCaseLibrary(filters: { q?: string; category?: string } = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) params.set(key, value); });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return readJson<CaseLibraryListResponse>(`/api/teacher/case-library${suffix}`);
}
export function getTeachingKnowledge(filters: { q?: string; category?: string; knowledge_type?: string; document_type?: string } = {}, scope: 'teacher' | 'admin' = 'teacher') {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.category) params.set('category', filters.category);
  if (filters.knowledge_type) params.set('knowledge_type', filters.knowledge_type);
  if (filters.document_type) params.set('document_type', filters.document_type);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return readJson<CaseLibraryListResponse>(`/api/${scope}/teaching-knowledge${suffix}`);
}
export function createTeachingKnowledge(payload: Record<string, unknown>, scope: 'teacher' | 'admin' = 'teacher') { return postJson<CaseLibraryEntry>(`/api/${scope}/teaching-knowledge`, payload); }
export async function uploadTeachingKnowledge(file: File, documentType: 'textbook' | 'evidence' | 'case') {
  const response = await fetch(`${baseUrl}/api/admin/teaching-knowledge/upload?filename=${encodeURIComponent(file.name)}&document_type=${documentType}`, { method: 'POST', headers: { ...authHeaders(), 'Content-Type': file.type || 'application/octet-stream' }, body: file });
  if (!response.ok) throw new Error(`资料上传失败：${response.status}`);
  return response.json() as Promise<{ status: string; item: CaseLibraryEntry; filename: string; bytes: number }>;
}
export function startDocumentProcessing() { return postJson<{ status: string; pid?: number }>('/api/admin/teaching-knowledge/process', {}); }
export function getDocumentProcessingStatus() { return readJson<{ running: boolean; pid?: number; total: number; counts: Record<string, number> }>('/api/admin/teaching-knowledge/process'); }
export function startEmbeddingProcessing() { return postJson<{ status: string; pid?: number }>('/api/admin/teaching-knowledge/embeddings/process', {}); }
export function getEmbeddingProcessingStatus() { return readJson<{ running: boolean; pid?: number; total: number; counts: Record<string, number> }>('/api/admin/teaching-knowledge/embeddings/process'); }
export function updateTeachingKnowledge(entryId: string, payload: Record<string, unknown>, scope: 'teacher' | 'admin' = 'teacher') {
  return fetch(`${baseUrl}/api/${scope}/teaching-knowledge/${encodeURIComponent(entryId)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(payload) }).then(async (response) => {
    if (!response.ok) throw new Error(await requestError(response));
    return response.json() as Promise<CaseLibraryEntry>;
  });
}
export function deleteTeachingKnowledge(entryId: string, scope: 'teacher' | 'admin' = 'teacher') {
  return fetch(`${baseUrl}/api/${scope}/teaching-knowledge/${encodeURIComponent(entryId)}`, { method: 'DELETE', headers: authHeaders() }).then(async (response) => {
    if (!response.ok) throw new Error(await requestError(response));
    return response.json() as Promise<{ status: string; id: string }>;
  });
}
export function getCaseLibraryEntry(entryId: string) { return readJson<CaseLibraryEntry>(`/api/teacher/case-library/${encodeURIComponent(entryId)}`); }
export function createCaseLibraryEntry(payload: { title: string; category: string; diagnosis: string; chief_complaint: string; present_illness: string; content: string; source: string; status?: string }) { return postJson<CaseLibraryEntry>('/api/teacher/case-library', payload); }
export function updateCaseLibraryEntry(entryId: string, payload: Partial<{ title: string; category: string; diagnosis: string; chief_complaint: string; present_illness: string; content: string; source: string; status: string }>) {
  return fetch(`${baseUrl}/api/teacher/case-library/${encodeURIComponent(entryId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  }).then(async (response) => {
    if (!response.ok) throw new Error(await requestError(response));
    return response.json() as Promise<CaseLibraryEntry>;
  });
}
export function deleteCaseLibraryEntry(entryId: string) {
  return fetch(`${baseUrl}/api/teacher/case-library/${encodeURIComponent(entryId)}`, {
    method: 'DELETE',
    headers: authHeaders()
  }).then(async (response) => {
    if (!response.ok) throw new Error(await requestError(response));
    return response.json() as Promise<{ status: string; id: string }>;
  });
}
export function deidentifyCaseText(text: string) { return postJson<CaseLibraryDeidentifyResult>('/api/teacher/case-library/deidentify', { text }); }
export function importCaseLibrary(sourceDir?: string) { return postJson<CaseLibraryImportReport>('/api/teacher/case-library/import', { source_dir: sourceDir || null }); }
export function compileCaseLibraryEntries(payload: { entry_ids: string[]; title?: string; department?: string; learning_goal?: string; suspected_diagnosis?: string; difficulty?: string; publish_immediately?: boolean }) { return postJson<TeacherCaseDraft>('/api/teacher/case-library/compile', payload); }
export function getHistoryTakingTemplate(q: string) { return readJson<HistoryTakingTemplate>(`/api/teacher/history-taking?q=${encodeURIComponent(q)}`); }
export function getTrainingReport(caseId = 'emergency_chest_pain') { return readJson<TrainingReport>(`/api/training/report?case_id=${encodeURIComponent(caseId)}`); }
export function getKnowledgeGraph(lang = 'zh', scope: 'anatomy' | 'clinical' = 'anatomy') { return readJson<{ nodes: KnowledgeNode[]; edges: KnowledgeEdge[] }>(`/api/graph?lang=${encodeURIComponent(lang)}&scope=${scope}`); }
export function getDataSources() { return readJson<DataSourceItem[]>('/api/data-sources'); }
export function searchGraph(q: string, lang = 'zh', scope: 'anatomy' | 'clinical' = 'anatomy') { return readJson<{ query: string; nodes: KnowledgeNode[]; edges: KnowledgeEdge[]; learning_path: string[] }>(`/api/graph/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}&scope=${scope}`); }
export function getAnatomyExercises() { return readJson<AnatomyExercise[]>('/api/anatomy'); }
export function submitAnatomy(payload: { exercise_id: string; selected_zone: string; node_id?: string; structure_id?: string; click_x?: number; click_y?: number }) { return postJson<AnatomyResult>('/api/anatomy/submit', payload); }
export function getAnatomyRecords(limit = 80) { return readJson<AnatomyLearningRecordsResponse>(`/api/anatomy/records?limit=${limit}`); }
export function getAnatomyMistakes(limit = 80) { return readJson<{ items: AnatomyMistake[] }>(`/api/anatomy/mistakes?limit=${limit}`); }
export function getQuizRecords(limit = 80) { return readJson<QuizLearningRecordsResponse>(`/api/anatomy/quiz-records?limit=${limit}`); }
export function getQuizMistakes(limit = 80) { return readJson<{ items: QuizLearningRecordsResponse['items'] }>(`/api/anatomy/quiz-mistakes?limit=${limit}`); }
export function getAnatomyTextbook(q: string) { return readJson<AnatomyTextbookResult>(`/api/anatomy/textbook?q=${encodeURIComponent(q)}`); }
export function getAnatomyEvidence(q: string, withAnswer = true) { return readJson<AnatomyEvidenceResponse>(`/api/anatomy/evidence?q=${encodeURIComponent(q)}&with_answer=${withAnswer}`); }
export function getAnatomyNotes(documentId: string, page: number) { return readJson<AnatomyNote[]>(`/api/anatomy/notes?document_id=${encodeURIComponent(documentId)}&page=${page}`); }
export function saveAnatomyNote(note: { note_id?: string; document_id: string; page: number; line_start?: number; line_end?: number; content: string; annotations?: unknown[] }) { return fetch(`${baseUrl}/api/anatomy/notes`, { method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify(note) }).then(async response => { if (!response.ok) throw new Error(await requestError(response)); return response.json() as Promise<AnatomyNote>; }); }
export function deleteAnatomyNote(noteId: string) { return fetch(`${baseUrl}/api/anatomy/notes/${encodeURIComponent(noteId)}`, { method: 'DELETE', headers: authHeaders() }).then(async response => { if (!response.ok) throw new Error(await requestError(response)); return response.json() as Promise<{ status: string; id: string }>; }); }
export function getAnatomyGlossary() { return readJson<{ count: number; source: string; terms: Record<string, string> }>('/api/anatomy/glossary'); }
export function getExamSettings() { return readJson<ExamSettings>('/api/exam/settings'); }
export function generateQuiz(payload: { structure_en: string; structure_cn?: string; system?: string; force?: boolean }) {
  return postJson<QuizSet>('/api/exam/quiz/generate', payload);
}
export function gradeQuiz(payload: { question_id: string; quiz_id?: string; answer: unknown }) {
  return postJson<QuizGrade>('/api/exam/quiz/grade', payload);
}
export function getMyClassrooms() { return readJson<{ role: string; items: ClassroomSummary[] }>('/api/classrooms/mine'); }
export function createClassroom(payload: { name: string; description?: string }) { return postJson<ClassroomSummary>('/api/classrooms', payload); }
export function joinClassroom(code: string) { return postJson<ClassroomSummary>('/api/classrooms/join', { code }); }
export function getClassroomDetail(classId: string) { return readJson<ClassroomDetail>(`/api/classrooms/${encodeURIComponent(classId)}`); }
export function getMyClassroomGuidance(classId = '') { return readJson<{ items: ClassroomGuidance[] }>(`/api/classrooms/guidance/mine${classId ? `?class_id=${encodeURIComponent(classId)}` : ''}`); }
export function getClassroomGuidance(classId: string, studentId = '') { return readJson<{ items: ClassroomGuidance[] }>(`/api/classrooms/${encodeURIComponent(classId)}/guidance${studentId ? `?student_id=${encodeURIComponent(studentId)}` : ''}`); }
export function sendClassroomGuidance(classId: string, payload: { student_id: string; content: string; recommended_score?: number | null }) {
  return postJson<ClassroomGuidance>(`/api/classrooms/${encodeURIComponent(classId)}/guidance`, payload);
}
export function generateAiClassroomGuidance(classId: string, studentId = '') {
  return postJson<ClassroomGuidance & { performance: Record<string, unknown> }>(`/api/classrooms/${encodeURIComponent(classId)}/guidance/ai`, { student_id: studentId });
}
export async function saveExamSettings(payload: Partial<ExamSettings>) {
  const response = await fetch(`${baseUrl}/api/exam/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error(await requestError(response));
  return response.json() as Promise<ExamSettings>;
}
export function speak(text: string) { return postJson<TtsResponse>('/api/tts/speak', { text, voice: 'clinical_tutor' }); }
export function getDigitalHumanModes() { return readJson<DigitalHumanModesResponse>('/api/digital-human/modes'); }
export function speakDigitalHuman(payload: DigitalHumanSpeakRequest) {
  return postJson<DigitalHumanResponse>('/api/digital-human/speak', payload);
}

export function startTraining(caseId: string, variantId: string, difficulty: string, mode: string) {
  return postJson<{ session_id: string; case: CaseSummary; opening_statement: string }>('/api/training/start', { case_id: caseId, variant_id: variantId, difficulty, mode });
}

export async function sendPatientMessage(caseId: string, message: string, history: ChatMessage[], sessionId?: string, variantId = 'A') {
  return postJson<PatientChatResponse>('/api/training/chat', { case_id: caseId, session_id: sessionId, variant_id: variantId, message, history });
}

export function orderTrainingTest(sessionId: string, testName: string) {
  return postJson<{ available: boolean; test_name: string; result: string; ordered_tests: string[] }>('/api/training/order-test', { session_id: sessionId, test_name: testName });
}

export function submitTrainingDiagnosis(sessionId: string, payload: { preliminary_diagnosis: string; differentials: string[]; treatment_principles: string; medication_plan: string; citations: string[] }) {
  return postJson<TrainingAssessment>('/api/training/submit-diagnosis', { session_id: sessionId, ...payload });
}

export function getTodayDailyReview(studentId: string) { return readJson<DailyReview>(`/api/daily-review/today/${encodeURIComponent(studentId)}`); }
export function getDailyReviewHistory(studentId: string) { return readJson<DailyReview[]>(`/api/daily-review/history/${encodeURIComponent(studentId)}`); }
export function generateDailyReview(studentId: string) { return postJson<DailyReview>('/api/daily-review/generate', { student_id: studentId, force: true }); }
export function getDailyReviewRecommendations(studentId: string) { return readJson<Pick<DailyReview, 'student_id' | 'date' | 'recommended_cases' | 'recommended_knowledge' | 'recommended_anatomy' | 'recommended_graph_path' | 'tomorrow_plan'>>(`/api/daily-review/recommendations/${encodeURIComponent(studentId)}`); }
export function getClassDailyReview(classId = 'clinical-2023-2') { return readJson<DailyReviewClassSummary>(`/api/daily-review/class/${encodeURIComponent(classId)}`); }
export function getDailyReviewPolicy() { return readJson<DailyReviewPolicy>('/api/daily-review/admin/config'); }

export function getTrainingRecommendations(caseId: string) {
  return readJson<{ today: CaseSummary[]; retraining: CaseSummary[]; similar: CaseSummary[] }>(`/api/training/recommendations?case_id=${encodeURIComponent(caseId)}`);
}

export async function askRag(question: string, scenario: string) {
  return postJson<RagResponse>('/api/rag/query', { question, scenario });
}

export async function sendAgentMessage(message: string, role: string, activeModule: string, context?: SkillQuery) {
  return postJson<AgentResponse>('/api/agent/chat', { message, role, active_module: activeModule, context });
}

export function login(account: string, password: string, role: string) { return postJson<AuthResponse>('/api/auth/login', { account, password, role }); }
export function logout() { return postJson<{ status: string; message: string }>('/api/auth/logout', {}); }
export function getCurrentUser() { return readJson<AuthResponse['user']>('/api/auth/me'); }
export function registerAccount(payload: { account: string; name: string; email: string; password: string; role: 'student' | 'teacher' }) {
  return postJson<{ message: string }>('/api/auth/register', payload);
}
export function verifyEmail(token: string) { return postJson<{ message: string }>('/api/auth/verify-email', { token }); }
export function resendVerification(email: string) { return postJson<{ message: string }>('/api/auth/resend-verification', { email }); }
export function forgotPassword(email: string) { return postJson<{ message: string }>('/api/auth/forgot-password', { email }); }
export function resetPassword(token: string, password: string) { return postJson<{ message: string }>('/api/auth/reset-password', { token, password }); }
export function getAdminUsers() { return readJson<unknown[]>('/api/admin/users'); }
export function reviewTeacher(userId: string, approved: boolean) {
  return fetch(`${baseUrl}/api/admin/users/${encodeURIComponent(userId)}/teacher-review`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify({ approved })
  }).then(async (response) => { if (!response.ok) throw new Error(await requestError(response)); return response.json(); });
}
export function getAdminDataSources() { return readJson<DataSourceItem[]>('/api/admin/data-sources'); }
export function syncAdminDataSources() { return postJson<{ status: string; message: string; sources: DataSourceItem[] }>('/api/admin/data-sources/sync', {}); }
export function getKnowledgeStatus() { return readJson<Record<string, unknown>>('/api/admin/knowledge-status'); }
export function getGraphStatus() { return readJson<Record<string, unknown>>('/api/admin/graph-status'); }
export function getAdminAuditLogs(limit = 20) {
  return readJson<{ count: number; items: Array<{ id: string; timestamp: string; account: string; name: string; role: string; action: string; target: string; detail: string }> }>(`/api/admin/audit-logs?limit=${limit}`);
}
export function exportObsidian() { return postJson<{ status: string; message: string; note_count: number; vault_name: string; notes: Array<{ filename: string; content: string }> }>('/api/admin/obsidian/export', {}); }
export function getTextbookPathways() { return readJson<TextbookStage[]>('/api/textbook-pathways'); }

