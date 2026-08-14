export interface Metric { label: string; value: string; trend: string; }
export type Role = 'student' | 'teacher' | 'admin';
export interface Overview { name: string; subtitle: string; contest_track: string; positioning: string; metrics: Metric[]; scenarios: string[]; }
export interface Citation { id: string; title: string; source: string; snippet: string; }
export interface WorkflowStage { id: string; name: string; agent: string; goal: string; }
export interface WorkflowTrace { id: string; name: string; agent: string; status: string; detail: string; }
export interface PatientProfile { age: number; gender: string; occupation: string; personality: string; communication_style: string; }
export interface AvailableTest { test_name: string; result: string; trigger_keywords: string[]; }
export interface CaseVariant { variant_id: string; label: string; age: number; gender: string; communication_style: string; opening_statement: string; distractor: string; }
export interface CaseSummary {
  case_id?: string;
  id: string;
  title_zh?: string;
  title_en?: string;
  title: string;
  department: string;
  specialty?: string;
  scenario?: string;
  chief_complaint: string;
  difficulty: string;
  symptom_tags?: string[];
  training_goals?: string[];
  learning_goals: string[];
  recommended_minutes?: number;
  completion_status?: string;
  patient_profile: PatientProfile;
  patient_image?: string;
  patient_profile_text?: string;
  speaking_style?: string;
  opening?: string;
  opening_statement?: string;
  history?: Record<string, string[]>;
  present_illness?: string;
  past_history?: string;
  personal_history?: string;
  family_history?: string;
  physical_exam?: string[];
  physical_exam_text?: string;
  available_tests?: AvailableTest[];
  available_exams?: string[];
  exam_results?: Record<string, string>;
  hidden_final_diagnosis?: string;
  differential_diagnoses?: string[];
  key_scoring_points?: string[];
  high_risk_misses?: string[];
  high_risk_omissions?: Array<{ id: string; level: string; text: string; suggestion: string; keywords?: string[] }>;
  common_student_errors?: string[];
  recommended_guidelines?: string[];
  related_knowledge_ids?: string[];
  related_graph_node_ids?: string[];
  graph_node_ids?: string[];
  recommended_followups?: string[];
  recommended_retraining?: string[];
  patient_answer_rules?: { can_only_answer_known_facts: boolean; do_not_reveal_final_diagnosis: boolean; unknown_answer: string };
  case_variants?: CaseVariant[];
  source?: { type: string; name: string; license_review_required?: boolean; contains_real_patient_data: boolean };
  active_variant?: string;
  script?: { identity?: string; style?: string; opening?: string; answers?: Array<{ keywords: string[]; reply: string }> };
}
export interface ChatMessage { role: 'student' | 'patient' | 'tutor' | 'agent'; content: string; citations?: Citation[]; }
export interface ScoreItem { name: string; score: number; max_score: number; feedback: string; }
export interface MissingPoint { id: string; level: string; text: string; suggestion: string; citation?: Citation | null; }
export interface PatientChatResponse { session_id?: string | null; case_id?: string; variant_id?: string; matched_field?: string; revealed_diagnosis?: boolean; ordered_test?: string | null; patient_reply: ChatMessage; tutor_hint: string; scores: ScoreItem[]; missing_points: MissingPoint[]; workflow_trace: WorkflowTrace[]; citations: Citation[]; safety_notes: string[]; }
export interface GuidelineDoc { id: string; title: string; source: string; type: string; tags: string[]; content: string; }
export interface TeacherDashboard { class_average: number; completion_rate?: number; training_sessions: number; teacher_time_saved: string; citation_accuracy: string; intervention_needed?: number; improvements: Array<{ label: string; value: number }>; common_missing_points: string[]; risk_rankings?: Array<{ label: string; count: number; level: string }>; students?: Array<{ name: string; sessions: number; average_score: number; last_case: string; weakness: string; needs_intervention: boolean }>; teaching_suggestions?: string[]; }
export interface TrainingReport { case_id: string; diagnosis_path: string[]; strengths: string[]; improvements: string[]; recommended_cases: string[]; citations: Citation[]; }
export interface DailyReview {
  review_id: string;
  student_id: string;
  date: string;
  status: '已生成' | '待补充训练' | '需要教师关注';
  summary: string;
  completed_cases: number;
  anatomy_practices: number;
  knowledge_searches: number;
  average_score: number;
  high_risk_misses: string[];
  performance: Record<string, number>;
  weak_points: string[];
  strengths: string[];
  recommended_cases: string[];
  recommended_knowledge: string[];
  recommended_anatomy: string[];
  recommended_graph_path: string[];
  tomorrow_plan: string[];
  teacher_attention_required: boolean;
}
export interface DailyReviewClassSummary {
  class_id: string;
  date: string;
  summary: string;
  trained_students: number;
  review_completion_rate: number;
  average_score: number;
  high_risk_rankings: Array<{ label: string; count: number; level: string }>;
  common_weak_points: string[];
  attention_students: Array<{ student_id: string; name: string; reason: string; average_score: number }>;
  teaching_suggestions: string[];
}
export interface DailyReviewPolicy {
  generate_time: string;
  score_weights: Record<string, number>;
  recommended_case_count: number;
  recommended_knowledge_count: number;
  digital_human_review_enabled: boolean;
  teacher_alert_enabled: boolean;
  service_status: string;
  last_generated_at: string;
  policy_note: string;
}
export interface KnowledgeNode { id: string; label: string; group: string; type?: string; label_zh?: string; label_en?: string; aliases_zh?: string[]; aliases_en?: string[]; summary?: string; description_zh?: string; description_en?: string; embedding?: number[]; score?: number; embedding_id?: string; embedding_text?: string; embedding_text_zh?: string; embedding_text_en?: string; vector_status?: string; source_ids?: string[]; related_case_ids?: string[]; related_knowledge_ids?: string[]; }
export interface KnowledgeEdge { source: string; target: string; relation: string; relation_zh?: string; relation_en?: string; weight?: number; evidence_source?: string; explanation_zh?: string; explanation_en?: string; }
export interface RagResponse { answer: string; citations: Citation[]; workflow_trace: WorkflowTrace[]; safety_notes: string[]; matched_knowledge?: KnowledgeItem[]; graph_nodes?: KnowledgeNode[]; graph_edges?: KnowledgeEdge[]; bilingual_terms?: BilingualTerm[]; related_cases?: CaseSummary[]; related_anatomy_exercises?: AnatomyExercise[]; recommended_learning_path?: string[]; }
export interface KnowledgeItem { id: string; title: string; title_zh?: string; title_en?: string; subject: string; type?: string; category?: string; summary: string; summary_zh?: string; summary_en?: string; keywords: string[]; keywords_en?: string[]; related_diseases: string[]; related_symptoms: string[]; related_exams: string[]; related_anatomy?: string[]; related_cases?: string[]; source?: string; source_type?: string; source_name?: string; data_source?: string; citation?: string; embedding_placeholder?: number[]; embedding_id?: string; embedding_text?: string; embedding_text_zh?: string; embedding_text_en?: string; vector_status?: string; graph_node_id?: string; graph_node_ids?: string[]; }
export interface AnatomyExercise { id: string; title: string; system?: string; target: string; prompt: string; answer_zone: string; standard_region?: string; explanation: string; clinical_link: string; graph_node_ids?: string[]; }
export interface AnatomyResult { correct: boolean; score_items: ScoreItem[]; feedback: string; explanation: string; clinical_link: string; }
export interface AgentResultCard { kind: string; title: string; summary: string; target: string; }
export interface AgentResponse { intent: string; action: string; target_module?: string | null; target_case_id?: string | null; target_exercise_id?: string | null; reply: string; result_cards: AgentResultCard[]; learning_path: string[]; workflow_trace: WorkflowTrace[]; safety_notes: string[]; }
export interface TtsResponse { status: string; voice: string; duration_seconds: number; audio_url?: string | null; message: string; }



export interface AuthUser { id: string; name: string; account: string; role: string; status: string; department: string; permissions: string[]; }
export interface AuthResponse { token: string; user: AuthUser; }
export interface DataSourceItem { id: string; name: string; platform: string; type: string; modules: string[]; license: string; connected: boolean; index_status: string; sync_status: string; url: string; mapping: Record<string, unknown>; }
export interface TextbookStage { id: string; title_zh: string; title_en: string; goal: string; books: string[]; }
export interface BilingualTerm { id: string; type: string; label_zh: string; label_en: string; aliases_zh?: string[]; aliases_en?: string[]; }

export type DigitalHumanState = 'idle' | 'listening' | 'speaking' | 'warning' | 'scoring' | 'reviewing';
export type DigitalHumanMode = 'mock' | 'liveact';
export interface DigitalHumanSpeakRequest {
  session_id: string;
  text: string;
  emotion: string;
  action: string;
  avatar_id: string;
  voice: string;
  mode: DigitalHumanMode;
  audio_url?: string | null;
}
export interface DigitalHumanResponse {
  status: string;
  session_id: string;
  request_id: string;
  requested_mode: DigitalHumanMode;
  mode: DigitalHumanMode;
  state: DigitalHumanState;
  video_url?: string | null;
  stream_url?: string | null;
  poster_url: string;
  subtitle: string;
  emotion: string;
  action: string;
  duration: number;
  provider: string;
  fallback_reason?: string | null;
}
export interface DigitalHumanModesResponse {
  active_mode: DigitalHumanMode;
  modes: Array<{ id: DigitalHumanMode; label: string; available: boolean; description: string }>;
  liveact_service_url: string;
  liveact_available: boolean;
  fallback_enabled: boolean;
}




