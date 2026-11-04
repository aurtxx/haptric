import type {
  ApiAttempt,
  ApiAssignment,
  ApiError,
  ApiExamQuestion,
  ApiExamSection,
  ApiExam,
  ApiQuestion,
  ApiStudent,
  AuthenticatedUser,
  ValidationError,
} from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])
let csrfToken: string | undefined
let csrfRequest: Promise<string> | undefined

export class HttpApiError extends Error implements ApiError {
  readonly kind: ApiError['kind']
  readonly status?: number
  readonly fields?: ValidationError

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'HttpApiError'
    this.kind = error.kind
    this.status = error.status
    this.fields = error.fields
  }
}

function safeMessage(status: number, payload: unknown): string {
  if (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string' && (payload.detail === 'Invalid credentials.' || ('code' in payload && payload.code === 'authentication_failed'))) {
    return 'Invalid credentials.'
  }
  if (status === 401 || status === 403) return 'Your session has expired. Please sign in again.'
  if (status >= 500) return 'The server is unavailable right now. Please try again.'
  if (payload && typeof payload === 'object' && 'detail' in payload && typeof payload.detail === 'string') {
    return payload.detail
  }
  return 'The request could not be completed. Check the highlighted fields and try again.'
}

function classify(status: number, payload: unknown): ApiError['kind'] {
  if (status === 401 || status === 403) return 'authentication'
  if (status === 400 && payload && typeof payload === 'object' && 'detail' in payload && payload.detail === 'Invalid credentials.') {
    return 'authentication'
  }
  if (status >= 400 && status < 500) return 'validation'
  return 'server'
}

async function parsePayload(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return undefined
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

async function getCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken
  if (!csrfRequest) {
    csrfRequest = fetch(`${API_BASE_URL}/auth/csrf/`, { credentials: 'include' })
      .then(async (response) => {
        const payload = await parsePayload(response) as { csrfToken?: string } | undefined
        if (!response.ok || !payload?.csrfToken) {
          throw new HttpApiError({ kind: response.status >= 500 ? 'server' : 'validation', status: response.status, message: safeMessage(response.status, payload) })
        }
        csrfToken = payload.csrfToken
        return payload.csrfToken
      })
      .catch((error: unknown) => {
        csrfRequest = undefined
        if (error instanceof HttpApiError) throw error
        throw new HttpApiError({ kind: 'network', message: 'The server is unavailable right now. Please try again.' })
      })
  }
  return csrfRequest
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  if (!SAFE_METHODS.has(method)) headers.set('X-CSRFToken', await getCsrfToken())
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/${path.replace(/^\//, '')}`, { ...init, method, headers, credentials: 'include' })
  } catch {
    throw new HttpApiError({ kind: 'network', message: 'The server is unavailable right now. Please try again.' })
  }
  const payload = await parsePayload(response)
  if (!response.ok) {
    if (response.status === 403 && !SAFE_METHODS.has(method)) csrfToken = undefined
    throw new HttpApiError({
      kind: classify(response.status, payload),
      status: response.status,
      message: safeMessage(response.status, payload),
      fields: payload && typeof payload === 'object' ? payload as ValidationError : undefined,
    })
  }
  return payload as T
}

export const httpApi = {
  getCurrentUser: () => request<AuthenticatedUser>('me/'),
  login: async (username: string, password: string) => {
    const user = await request<AuthenticatedUser>('auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) })
    // Django rotates the CSRF token during session login. Refetch it for the next mutation.
    csrfToken = undefined
    csrfRequest = undefined
    return user
  },
  logout: () => request<{ status: string }>('auth/logout/', { method: 'POST' }),
  getStudents: () => request<ApiStudent[]>('students/'),
  provisionStudent: (input: { name: string; student_id: string; username?: string; temporary_password: string; is_active?: boolean }) => request<ApiStudent>('students/provision/', { method: 'POST', body: JSON.stringify(input) }),
  getExams: () => request<ApiExam[]>('exams/'),
  getExam: (id: string) => request<ApiExam>(`exams/${id}/`),
  createExam: (input: { title: string; duration_minutes: number; available_from?: string | null; available_until?: string | null }) => request<ApiExam>('exams/', { method: 'POST', body: JSON.stringify(input) }),
  createSection: (input: { exam: string; name: string; position: number }) => request<ApiExamSection>('sections/', { method: 'POST', body: JSON.stringify(input) }),
  createQuestion: (input: { question_type: 'single'; prompt: string; options: string[]; correct_answer: string; positive_marks: string; negative_marks: string; subject?: string | null }) => request<ApiQuestion>('questions/', { method: 'POST', body: JSON.stringify(input) }),
  attachQuestion: (input: { section: string; question_id: string; position: number }) => request<ApiExamQuestion>('exam-questions/', { method: 'POST', body: JSON.stringify(input) }),
  publishExam: (id: string) => request<ApiExam>(`exams/${id}/publish/`, { method: 'POST', body: JSON.stringify({}) }),
  assignExam: (id: string, student: string) => request<ApiAssignment>(`exams/${id}/assign/`, { method: 'POST', body: JSON.stringify({ student }) }),
  getAttempts: () => request<ApiAttempt[]>('attempts/'),
}

export function resetHttpApiCsrfForTests() {
  csrfToken = undefined
  csrfRequest = undefined
}
