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
})
