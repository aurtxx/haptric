export type Role = 'admin' | 'student'
export type QuestionType = 'single' | 'multi' | 'multiple' | 'numeric'
export type UserRole = 'owner' | 'admin' | 'teacher' | 'invigilator' | 'student'

export interface Organization {
  id: string
  name: string
  slug: string
  mode: 'lan' | 'cloud'
  installation_id: string
  created_at: string
}

export interface AuthenticatedUser {
  id: string
  username: string
  role: UserRole
  organization: string | null
}

export type ApiErrorKind = 'authentication' | 'validation' | 'network' | 'server'

export interface ValidationError {
  detail?: string
  [field: string]: string | string[] | undefined
}

export interface ApiError {
  kind: ApiErrorKind
  message: string
  status?: number
  fields?: ValidationError
}

export interface ApiQuestion {
  id: string
  subject: string | null
  question_type: QuestionType
  prompt: string
  options: unknown[]
  positive_marks?: string
  negative_marks?: string
  version: number
  /** Present only for staff responses; student responses must omit it. */
  correct_answer?: unknown
}

export interface ApiExamQuestion {
  id: number
  question: ApiQuestion
  position: number
}

export interface ApiExamSection {
  id: string
  name: string
  position: number
  exam_questions: ApiExamQuestion[]
}

export interface ApiExam {
  id: string
  title: string
  duration_minutes: number
  available_from: string | null
  available_until: string | null
  status: 'draft' | 'published' | 'closed'
  published_at: string | null
  created_at: string
  sections: ApiExamSection[]
}

export interface ApiStudent {
  id: string
  name: string
  student_id: string
  username?: string | null
  is_active: boolean
  created_at: string
}

export interface ApiAssignment {
  id: number
  exam: string
  student: string
  assigned_at: string
}

export interface ApiAnswer {
  id: number
  question: string
  value: unknown
  saved_at: string
}

export interface ApiResult {
  score: string
  correct_count: number
  incorrect_count: number
  unanswered_count: number
  calculated_at: string
}

export interface ApiAttempt {
  id: string
  exam: string
  exam_title?: string
  student: string
  student_name?: string
  student_id?: string
  status: 'in_progress' | 'submitted'
  started_at: string
  deadline_at: string
  submitted_at: string | null
  answers: ApiAnswer[]
  result: ApiResult | null
}

export type AttemptAnswerState = 'correct' | 'incorrect' | 'unanswered' | 'pending'

export interface ApiAttemptReviewQuestion {
  question_id: string
  section_id?: string
  section_name?: string
  section_position?: number
  position: number
  prompt: string
  question_type: QuestionType
  options: unknown[]
  student_response: unknown
  correct_answer?: unknown
  answer_state: AttemptAnswerState
  marks_awarded?: string | null
  positive_marks?: string
  negative_marks?: string
}

export interface ApiAttemptReview extends ApiAttempt {
  questions: ApiAttemptReviewQuestion[]
}

export interface Question {
  id: string
  prompt: string
  type: QuestionType
  options?: string[]
  answer: string | string[]
  points: number
  penalty: number
}

export interface Exam {
  id: string
  title: string
  durationSeconds: number
  status: 'draft' | 'published'
  questions: Question[]
}

export interface Attempt {
  id: string
  examId: string
  studentId: string
  startedAt: number
  deadline: number
  answers: Record<string, string | string[]>
  submittedAt?: number
  score?: number
}
