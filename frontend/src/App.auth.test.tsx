import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'
import { resetHttpApiCsrfForTests } from './api'

const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } })

describe('App session boundary', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    resetHttpApiCsrfForTests()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('restores an authenticated session after refresh and displays the backend role', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([]))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    expect(await screen.findByText('Welcome, admin.')).toBeTruthy()
    expect(screen.getByText('admin · Org org-1')).toBeTruthy()
    expect(fetchMock.mock.calls[0][0]).toContain('/me/')
  })

  it('shows invalid credentials without entering a role preview', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'Authentication required.' }, 401))
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-one' }))
      .mockResolvedValueOnce(jsonResponse({ detail: 'Invalid credentials.', code: 'authentication_failed' }, 401))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await screen.findByRole('button', { name: 'Enter workspace' })
    fireEvent.change(screen.getByLabelText('Email or student ID'), { target: { value: 'unknown' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Enter workspace' }))

    expect((await screen.findByRole('alert')).textContent).toContain('Invalid credentials')
    expect(screen.getByRole('button', { name: 'Enter workspace' })).toBeTruthy()
  })

  it('logs in through Django and logs out through the session endpoint', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'Authentication required.' }, 401))
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-login' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 'u1', username: 'admin', role: 'admin', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse({ csrfToken: 'csrf-logout' }))
      .mockResolvedValueOnce(jsonResponse({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    await screen.findByRole('button', { name: 'Enter workspace' })
    fireEvent.change(screen.getByLabelText('Email or student ID'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Enter workspace' }))
    await screen.findByRole('button', { name: 'Sign out' })

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    await screen.findByRole('button', { name: 'Enter workspace' })
    expect(fetchMock.mock.calls[2][0]).toContain('/auth/login/')
    expect(fetchMock.mock.calls[7][0]).toContain('/auth/logout/')
  })

  it('shows a recoverable server-unavailable state when session lookup fails', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('offline'))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('server is unavailable'))
    expect(screen.getByRole('button', { name: 'Enter workspace' })).toBeTruthy()
  })

  it('loads the assigned exam and restores an in-progress attempt from Django', async () => {
    const exam = {
      id: 'exam-1', title: 'Assigned Exam', duration_minutes: 30, available_from: null, available_until: null,
      status: 'published', published_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z',
      sections: [{ id: 'section-1', name: 'Core', position: 1, exam_questions: [{ id: 1, position: 1, question: { id: 'question-1', subject: null, question_type: 'single', prompt: 'Which option is correct?', options: ['A', 'B'], version: 1 } }] }],
    }
    const attempt = {
      id: 'attempt-1', exam: 'exam-1', student: 'student-1', status: 'in_progress',
      started_at: '2026-01-01T00:00:00Z', deadline_at: '2099-01-01T00:30:00Z', submitted_at: null,
      answers: [{ id: 1, question: 'question-1', value: 'B', saved_at: '2026-01-01T00:01:00Z' }], result: null,
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ id: 'student-1', username: 'HACK-001', role: 'student', organization: 'org-1' }))
      .mockResolvedValueOnce(jsonResponse([exam]))
      .mockResolvedValueOnce(jsonResponse([attempt]))
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    expect(await screen.findByText('Question 1 of 1')).toBeTruthy()
    expect(screen.getByText('Assigned Exam')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'BB' }).className).toContain('selected')
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual(['/api/v1/me/', '/api/v1/exams/', '/api/v1/attempts/'])
  })
})
