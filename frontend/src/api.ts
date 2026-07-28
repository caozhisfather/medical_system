import type { AgentResponse, AnatomyExercise, AnatomyResult, AuthResponse, CaseSummary, ChatMessage, DataSourceItem, GuidelineDoc, KnowledgeEdge, KnowledgeItem, KnowledgeNode, Overview, PatientChatResponse, RagResponse, TeacherDashboard, TextbookStage, TrainingReport, TtsResponse } from './types';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function getOverview() { return readJson<Overview>('/api/site/overview'); }
export function getCases() { return readJson<CaseSummary[]>('/api/cases'); }
export function getCase(caseId: string) { return readJson<Record<string, unknown>>(`/api/cases/${encodeURIComponent(caseId)}`); }
export function getWorkflow() { return readJson<{ name: string; stages: Array<{ id: string; name: string; agent: string; goal: string }> }>('/api/workflow'); }
export function getGuidelines() { return readJson<GuidelineDoc[]>('/api/guidelines'); }
export function getKnowledge() { return readJson<KnowledgeItem[]>('/api/knowledge'); }
export function searchKnowledge(q: string, lang = 'zh') { return readJson<{ query: string; count: number; items: Array<{ kind: string; title: string; summary: string; target: string }> }>(`/api/knowledge/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}`); }
export function getTeacherDashboard() { return readJson<TeacherDashboard>('/api/teacher/dashboard'); }
export function getTrainingReport(caseId = 'emergency_chest_pain') { return readJson<TrainingReport>(`/api/training/report?case_id=${encodeURIComponent(caseId)}`); }
export function getKnowledgeGraph(lang = 'zh') { return readJson<{ nodes: KnowledgeNode[]; edges: KnowledgeEdge[] }>(`/api/graph?lang=${encodeURIComponent(lang)}`); }
export function searchGraph(q: string, lang = 'zh') { return readJson<{ query: string; nodes: KnowledgeNode[]; edges: KnowledgeEdge[]; learning_path: string[] }>(`/api/graph/search?q=${encodeURIComponent(q)}&lang=${encodeURIComponent(lang)}`); }
export function getAnatomyExercises() { return readJson<AnatomyExercise[]>('/api/anatomy'); }
export function submitAnatomy(exerciseId: string, selectedZone: string) { return postJson<AnatomyResult>('/api/anatomy/submit', { exercise_id: exerciseId, selected_zone: selectedZone }); }
export function speak(text: string) { return postJson<TtsResponse>('/api/tts/speak', { text, voice: 'clinical_tutor' }); }

export async function sendPatientMessage(caseId: string, message: string, history: ChatMessage[]) {
  return postJson<PatientChatResponse>('/api/training/chat', { case_id: caseId, message, history });
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
