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
})
