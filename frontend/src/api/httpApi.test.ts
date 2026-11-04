import { beforeEach, describe, expect, it, vi } from 'vitest'
import { httpApi, resetHttpApiCsrfForTests } from './httpApi'

const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

describe('httpApi authentication boundary', () => {
  beforeEach(() => {
    resetHttpApiCsrfForTests()
    vi.restoreAllMocks()
  })

  it('gets CSRF, logs in with a session cookie, and restores the current user', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-one' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(httpApi.login('admin', 'password')).resolves.toMatchObject({ username: 'admin', role: 'admin' })
    await expect(httpApi.getCurrentUser()).resolves.toMatchObject({ id: 'u1' })

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: 'include' })
    expect(fetchMock.mock.calls[1][0]).toContain('/auth/login/')
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ credentials: 'include', method: 'POST' })
    expect(new Headers(fetchMock.mock.calls[1][1].headers).get('X-CSRFToken')).toBe('csrf-one')
    expect(fetchMock.mock.calls[2][0]).toContain('/me/')
  })

  it('classifies invalid credentials without exposing backend details', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-one' }))
      .mockResolvedValueOnce(jsonResponse({ detail: 'Invalid credentials.', code: 'authentication_failed' }, 401))
    vi.stubGlobal('fetch', fetchMock)

    await expect(httpApi.login('unknown', 'wrong')).rejects.toMatchObject({ kind: 'authentication', message: 'Invalid credentials.' })
  })

  it('classifies network failures as recoverable server-unavailable errors', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('offline'))
    vi.stubGlobal('fetch', fetchMock)

    await expect(httpApi.getCurrentUser()).rejects.toMatchObject({ kind: 'network', message: 'The server is unavailable right now. Please try again.' })

    resetHttpApiCsrfForTests()
    await expect(httpApi.login('admin', 'password')).rejects.toMatchObject({ kind: 'network', message: 'The server is unavailable right now. Please try again.' })
  })

  it('handles anonymous sessions and validation payloads as typed errors', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'Authentication required.' }, 401))
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-two' }))
      .mockResolvedValueOnce(jsonResponse({ title: ['This field is required.'] }, 400))
    vi.stubGlobal('fetch', fetchMock)

    await expect(httpApi.getCurrentUser()).rejects.toMatchObject({ kind: 'authentication', status: 401 })
    await expect(httpApi.login('admin', 'password')).rejects.toMatchObject({ kind: 'validation', fields: { title: ['This field is required.'] } })
  })

  it('refreshes CSRF after login before logging out', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'before-login' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'after-login' }))
      .mockResolvedValueOnce(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    await httpApi.login('admin', 'password')
    await httpApi.logout()
    expect(new Headers(fetchMock.mock.calls[3][1].headers).get('X-CSRFToken')).toBe('after-login')
  })

  it('uses typed persisted admin authoring endpoints', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-admin' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'exam-1', title: 'Demo', duration_minutes: 30, sections: [], status: 'draft' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'section-1', name: 'Demo', position: 1, exam_questions: [] }))
      .mockResolvedValueOnce(jsonResponse({ id: 'question-1', prompt: 'Q', question_type: 'single', options: ['A'], positive_marks: '1.00', negative_marks: '0.00', version: 1 }))
      .mockResolvedValueOnce(jsonResponse({ id: 1, position: 1 }))
      .mockResolvedValueOnce(jsonResponse({ id: 'exam-1', title: 'Demo', duration_minutes: 30, sections: [], status: 'published' }))
      .mockResolvedValueOnce(jsonResponse({ id: 1, exam: 'exam-1', student: 'student-1', assigned_at: '2026-01-01T00:00:00Z' }))
    vi.stubGlobal('fetch', fetchMock)

    await httpApi.createExam({ title: 'Demo', duration_minutes: 30, available_from: null, available_until: null })
    await httpApi.createSection({ exam: 'exam-1', name: 'Demo', position: 1 })
    await httpApi.createQuestion({ question_type: 'single', prompt: 'Q', options: ['A'], correct_answer: 'A', positive_marks: '1', negative_marks: '0' })
    await httpApi.attachQuestion({ section: 'section-1', question_id: 'question-1', position: 1 })
    await httpApi.publishExam('exam-1')
    await httpApi.assignExam('exam-1', 'student-1')

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/v1/auth/csrf/', '/api/v1/exams/', '/api/v1/sections/', '/api/v1/questions/', '/api/v1/exam-questions/', '/api/v1/exams/exam-1/publish/', '/api/v1/exams/exam-1/assign/',
    ])
    expect(JSON.parse(fetchMock.mock.calls[2][1].body)).toMatchObject({ exam: 'exam-1', name: 'Demo', position: 1 })
    expect(JSON.parse(fetchMock.mock.calls[6][1].body)).toEqual({ student: 'student-1' })
  })

  it('uses typed student attempt endpoints with idempotency and persisted answers', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-student' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'attempt-1', exam: 'exam-1', student: 'student-1', status: 'in_progress', started_at: '2026-01-01T00:00:00Z', deadline_at: '2026-01-01T00:30:00Z', answers: [], result: null }))
      .mockResolvedValueOnce(jsonResponse({ id: 1, question: 'question-1', value: 'A', saved_at: '2026-01-01T00:01:00Z' }))
      .mockResolvedValueOnce(jsonResponse({ score: '1.00', correct_count: 1, incorrect_count: 0, unanswered_count: 0, calculated_at: '2026-01-01T00:02:00Z' }))
    vi.stubGlobal('fetch', fetchMock)

    await httpApi.startAttempt('exam-1', 'attempt-key-1')
    await httpApi.saveAnswer('attempt-1', 'question-1', 'A')
    await httpApi.submitAttempt('attempt-1')

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      '/api/v1/auth/csrf/', '/api/v1/attempts/start/', '/api/v1/attempts/attempt-1/answer/', '/api/v1/attempts/attempt-1/submit/',
    ])
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST' })
    expect(new Headers(fetchMock.mock.calls[1][1].headers).get('Idempotency-Key')).toBe('attempt-key-1')
    expect(JSON.parse(fetchMock.mock.calls[2][1].body)).toEqual({ question: 'question-1', value: 'A' })
  })
})
