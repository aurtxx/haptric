import type { Attempt, Exam } from '../types'

const exam: Exam = {
  id: 'northstar-demo',
  title: 'Foundations check-in',
  durationSeconds: 90,
  status: 'published',
  questions: [
    { id: 'q1', prompt: 'Which value is prime?', type: 'single', options: ['9', '11', '15', '21'], answer: '11', points: 3, penalty: 1 },
    { id: 'q2', prompt: 'Select the two renewable energy sources.', type: 'multiple', options: ['Solar', 'Coal', 'Wind', 'Diesel'], answer: ['Solar', 'Wind'], points: 4, penalty: 0 },
    { id: 'q3', prompt: 'Enter the number of sides in a hexagon.', type: 'numeric', answer: '6', points: 3, penalty: 0 },
  ],
}

let attempt: Attempt | undefined
const ATTEMPT_STORAGE_KEY = 'openexam.demo.attempt.v1'

function loadAttempt(): Attempt | undefined {
  if (attempt) return attempt
  if (typeof window === 'undefined') return undefined
  const raw = window.localStorage.getItem(ATTEMPT_STORAGE_KEY)
  if (!raw) return undefined
  try {
    attempt = JSON.parse(raw) as Attempt
    return attempt
  } catch {
    window.localStorage.removeItem(ATTEMPT_STORAGE_KEY)
    return undefined
  }
}

function persistAttempt(value: Attempt | undefined) {
  attempt = value
  if (typeof window === 'undefined') return
  if (value) window.localStorage.setItem(ATTEMPT_STORAGE_KEY, JSON.stringify(value))
  else window.localStorage.removeItem(ATTEMPT_STORAGE_KEY)
}

export const mockApi = {
  async getExam(): Promise<Exam> { return structuredClone(exam) },
  async createAttempt(): Promise<Attempt> {
    const existing = loadAttempt()
    if (existing && !existing.submittedAt && existing.examId === exam.id) return structuredClone(existing)
    const now = Date.now()
    const next = { id: `attempt-${now}`, examId: exam.id, studentId: 'student-demo', startedAt: now, deadline: now + exam.durationSeconds * 1000, answers: {} }
    persistAttempt(next)
    return structuredClone(next)
  },
  async saveAnswer(id: string, answer: string | string[]): Promise<Attempt> {
    loadAttempt()
    if (!attempt || attempt.submittedAt) throw new Error('This attempt is no longer editable.')
    attempt.answers[id] = answer
    persistAttempt(attempt)
    return structuredClone(attempt)
  },
  async submitAttempt(): Promise<Attempt> {
    loadAttempt()
    if (!attempt) throw new Error('No active attempt.')
    if (!attempt.submittedAt) {
      const score = exam.questions.reduce((sum, q) => {
        const value = attempt?.answers[q.id]
        const correct = Array.isArray(q.answer) ? Array.isArray(value) && q.answer.length === value.length && q.answer.every((v) => value.includes(v)) : value === q.answer
        return sum + (value === undefined || value === '' ? 0 : correct ? q.points : -q.penalty)
      }, 0)
      attempt.submittedAt = Date.now()
      attempt.score = score
      persistAttempt(attempt)
    }
    return structuredClone(attempt)
  },
  async getAttempt(): Promise<Attempt | undefined> { const current = loadAttempt(); return current ? structuredClone(current) : undefined },
}
