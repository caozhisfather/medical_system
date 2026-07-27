export interface Metric { label: string; value: string; trend: string; }
export interface Overview { name: string; subtitle: string; contest_track: string; positioning: string; metrics: Metric[]; scenarios: string[]; }
export interface Citation { id: string; title: string; source: string; snippet: string; }
export interface WorkflowStage { id: string; name: string; agent: string; goal: string; }
export interface WorkflowTrace { id: string; name: string; agent: string; status: string; detail: string; }
export interface CaseSummary { id: string; title: string; department: string; chief_complaint: string; difficulty: string; learning_goals: string[]; }
export interface ChatMessage { role: 'student' | 'patient' | 'tutor'; content: string; citations?: Citation[]; }
export interface ScoreItem { name: string; score: number; max_score: number; feedback: string; }
export interface MissingPoint { id: string; level: string; text: string; suggestion: string; citation?: Citation | null; }
export interface PatientChatResponse { patient_reply: ChatMessage; tutor_hint: string; scores: ScoreItem[]; missing_points: MissingPoint[]; workflow_trace: WorkflowTrace[]; citations: Citation[]; safety_notes: string[]; }
export interface GuidelineDoc { id: string; title: string; source: string; type: string; tags: string[]; content: string; }
export interface TeacherDashboard { class_average: number; training_sessions: number; teacher_time_saved: string; citation_accuracy: string; improvements: Array<{ label: string; value: number }>; common_missing_points: string[]; }
export interface TrainingReport { case_id: string; diagnosis_path: string[]; strengths: string[]; improvements: string[]; recommended_cases: string[]; citations: Citation[]; }
export interface KnowledgeNode { id: string; label: string; group: string; score?: number; }
export interface KnowledgeEdge { source: string; target: string; relation: string; }
export interface RagResponse { answer: string; citations: Citation[]; workflow_trace: WorkflowTrace[]; safety_notes: string[]; }
