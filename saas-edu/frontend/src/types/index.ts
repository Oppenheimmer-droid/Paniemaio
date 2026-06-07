// ===========================================
// Domain Types — Frontend
// ===========================================

// User & Auth
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'teacher' | 'student'
  tenant_id: string
  tenant_name?: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
  status: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  tenant: Tenant
}

// Documents
export interface Document {
  id: string
  tenant_id: string
  subject_id: string | null
  title: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  page_count: number
  chunk_count: number
  error_message: string | null
  created_at: string
  updated_at: string
  uploaded_by: string
}

export interface Subject {
  id: string
  tenant_id: string
  name: string
  code: string
  description: string | null
}

// Chat
export interface ChatSession {
  id: string
  tenant_id: string
  user_id: string
  document_id: string | null
  title: string
  is_archived: boolean
  message_count: number
  total_tokens: number
  last_message_at: string
  created_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  tokens_used: number
  latency_ms: number
  created_at: string
}

export interface Citation {
  source: string
  page: number | null
  document_id: string
  text: string
}

// Evaluations
export interface Evaluation {
  id: string
  tenant_id: string
  document_id: string
  title: string
  evaluation_type: 'quiz' | 'exam' | 'practice'
  question_count: number
  difficulty: number
  time_limit_minutes: number
  passing_score: number
  is_published: boolean
  total_attempts: number
  avg_score: number | null
  created_at: string
}

export interface Question {
  id: string
  evaluation_id: string
  question_text: string
  question_type: 'multiple_choice' | 'true_false' | 'short_answer'
  options: string[]
  explanation: string | null
  difficulty: number
  points: number
  order_index: number
}

export interface EvaluationAttempt {
  id: string
  tenant_id: string
  evaluation_id: string
  user_id: string
  started_at: string
  completed_at: string | null
  score: number
  passed: boolean
  time_spent_seconds: number
}

export interface Answer {
  id: string
  attempt_id: string
  question_id: string
  answer_text: string
  is_correct: boolean
  points_earned: number
  ai_grade_feedback: string | null
}

// Analytics
export interface AnalyticsOverview {
  total_documents: number
  active_students_7d: number
  messages_today: number
  avg_score: number | null
}

export interface StudentProgress {
  user_id: string
  user_name: string
  email: string
  total_attempts: number
  avg_score: number
  last_activity: string
}

export interface DocumentUsage {
  document_id: string
  title: string
  rag_queries: number
  evaluations: number
  chunks: number
}

// API Error
export interface ApiError {
  code: string
  message: string
  detail?: string
}