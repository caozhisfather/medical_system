import type { AgentResponse, AnatomyExercise, AnatomyResult, AuthResponse, CaseSummary, ChatMessage, DailyReview, DailyReviewClassSummary, DailyReviewPolicy, DataSourceItem, GuidelineDoc, KnowledgeEdge, KnowledgeItem, KnowledgeNode, Overview, PatientChatResponse, RagResponse, TeacherDashboard, TextbookStage, TrainingReport, TtsResponse } from './types';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

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
export function getDataSources() { return readJson<DataSourceItem[]>('/api/data-sources'); }
export function searchKnowledge(q: string, lang = 'zh') { return readJson<{ query: string; count: number; items: Array<{ kind: string; title: string; summary: string; target: string }> }>(`/api/knowledge/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}`); }
export function getTeacherDashboard() { return readJson<TeacherDashboard>('/api/teacher/dashboard'); }
export function getTrainingReport(caseId = 'emergency_chest_pain') { return readJson<TrainingReport>(`/api/training/report?case_id=${encodeURIComponent(caseId)}`); }
export function getKnowledgeGraph(lang = 'zh') { return readJson<{ nodes: KnowledgeNode[]; edges: KnowledgeEdge[] }>(`/api/graph?lang=${encodeURIComponent(lang)}`); }
export function searchGraph(q: string, lang = 'zh') { return readJson<{ query: string; nodes: KnowledgeNode[]; edges: KnowledgeEdge[]; learning_path: string[] }>(`/api/graph/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}`); }
export function getAnatomyExercises() { return readJson<AnatomyExercise[]>('/api/anatomy'); }
export function submitAnatomy(exerciseId: string, selectedZone: string) { return postJson<AnatomyResult>('/api/anatomy/submit', { exercise_id: exerciseId, selected_zone: selectedZone }); }
export function speak(text: string) { return postJson<TtsResponse>('/api/tts/speak', { text, voice: 'clinical_tutor' }); }

export function startTraining(caseId: string, variantId: string, difficulty: string, mode: string) {
  return postJson<{ session_id: string; case: CaseSummary; opening_statement: string }>('/api/training/start', { case_id: caseId, variant_id: variantId, difficulty, mode });
}

export async function sendPatientMessage(caseId: string, message: string, history: ChatMessage[], sessionId?: string, variantId = 'A') {
  return postJson<PatientChatResponse>('/api/training/chat', { case_id: caseId, session_id: sessionId, variant_id: variantId, message, history });
}

export function orderTrainingTest(sessionId: string, testName: string) {
  return postJson<{ available: boolean; test_name: string; result: string; ordered_tests: string[] }>('/api/training/order-test', { session_id: sessionId, test_name: testName });
}

export function submitTrainingDiagnosis(sessionId: string, payload: { preliminary_diagnosis: string; differentials: string[]; treatment_principles: string; citations: string[] }) {
  return postJson<Record<string, unknown>>('/api/training/submit-diagnosis', { session_id: sessionId, ...payload });
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

export async function sendAgentMessage(message: string, role: string, activeModule: string) {
  return postJson<AgentResponse>('/api/agent/chat', { message, role, active_module: activeModule });
}

export function login(account: string, password: string, role: string) { return postJson<AuthResponse>('/api/auth/login', { account, password, role }); }
export function logout() { return postJson<{ status: string; message: string }>('/api/auth/logout', {}); }
export function getAdminUsers() { return readJson<unknown[]>('/api/admin/users'); }
export function getAdminDataSources() { return readJson<DataSourceItem[]>('/api/admin/data-sources'); }
export function syncAdminDataSources() { return postJson<{ status: string; message: string; sources: DataSourceItem[] }>('/api/admin/data-sources/sync', {}); }
export function getKnowledgeStatus() { return readJson<Record<string, unknown>>('/api/admin/knowledge-status'); }
export function getGraphStatus() { return readJson<Record<string, unknown>>('/api/admin/graph-status'); }
export function exportObsidian() { return postJson<{ status: string; message: string; note_count: number; vault_name: string; notes: Array<{ filename: string; content: string }> }>('/api/admin/obsidian/export', {}); }
export function getTextbookPathways() { return readJson<TextbookStage[]>('/api/textbook-pathways'); }


