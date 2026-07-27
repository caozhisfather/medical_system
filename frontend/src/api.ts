import type { CaseSummary, GuidelineDoc, KnowledgeEdge, KnowledgeNode, Overview, PatientChatResponse, RagResponse, TeacherDashboard, TrainingReport, WorkflowStage, ChatMessage } from './types';

const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(`${baseUrl}${url}`);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function getOverview() { return readJson<Overview>('/api/site/overview'); }
export function getCases() { return readJson<CaseSummary[]>('/api/cases'); }
export function getWorkflow() { return readJson<{ name: string; stages: WorkflowStage[] }>('/api/workflow'); }
export function getGuidelines() { return readJson<GuidelineDoc[]>('/api/guidelines'); }
export function getTeacherDashboard() { return readJson<TeacherDashboard>('/api/teacher/dashboard'); }
export function getTrainingReport(caseId = 'emergency_chest_pain') { return readJson<TrainingReport>(`/api/training/report?case_id=${encodeURIComponent(caseId)}`); }
export function getKnowledgeGraph() { return readJson<{ nodes: KnowledgeNode[]; edges: KnowledgeEdge[] }>('/api/knowledge-graph'); }

export async function sendPatientMessage(caseId: string, message: string, history: ChatMessage[]) {
  const response = await fetch(`${baseUrl}/api/patient/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseId, message, history })
  });
  if (!response.ok) throw new Error(`Patient chat failed: ${response.status}`);
  return response.json() as Promise<PatientChatResponse>;
}

export async function askRag(question: string, scenario: string) {
  const response = await fetch(`${baseUrl}/api/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, scenario })
  });
  if (!response.ok) throw new Error(`RAG request failed: ${response.status}`);
  return response.json() as Promise<RagResponse>;
}
