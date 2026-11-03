export type Role = 'admin' | 'student'
export type QuestionType = 'single' | 'multiple' | 'numeric'

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
