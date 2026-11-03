import { describe, expect, it, beforeEach } from 'vitest'
import { mockApi } from '../../frontend/src/api/mockApi'

describe('mock exam contract', () => {
  beforeEach(async () => { await mockApi.getExam() })

  it('creates an attempt with a server deadline', async () => {
    const attempt = await mockApi.createAttempt()
    expect(attempt.deadline).toBeGreaterThan(attempt.startedAt)
    expect(attempt.answers).toEqual({})
  })

  it('scores single, multiple and numeric questions once on submit', async () => {
    await mockApi.createAttempt()
    await mockApi.saveAnswer('q1', '11')
    await mockApi.saveAnswer('q2', ['Solar', 'Wind'])
    await mockApi.saveAnswer('q3', '6')
    const submitted = await mockApi.submitAttempt()
    expect(submitted.score).toBe(10)
    const replay = await mockApi.submitAttempt()
    expect(replay.submittedAt).toBe(submitted.submittedAt)
    expect(replay.score).toBe(10)
  })
})
