import { useEffect, useState, type FormEvent } from 'react'
import { httpApi, HttpApiError } from './api'
import type { ApiAttempt, ApiAttemptReview, ApiError, ApiExam, ApiResult, ApiStudent, AuthenticatedUser, Role } from './types'

type Screen = 'overview' | 'studio' | 'students' | 'exam' | 'results'

const navFor = (role: Role): { id: Screen; label: string; hint: string }[] => role === 'admin'
  ? [{ id: 'overview', label: 'Overview', hint: 'Today at a glance' }, { id: 'studio', label: 'Exams', hint: 'Author and publish' }, { id: 'students', label: 'Students', hint: 'Roster and access' }, { id: 'results', label: 'Results', hint: 'Attempts and scores' }]
  : [{ id: 'overview', label: 'My exams', hint: 'Assigned learning' }, { id: 'exam', label: 'Current attempt', hint: 'Resume and answer' }, { id: 'results', label: 'Results', hint: 'Server feedback' }]

function App() {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [sessionChecking, setSessionChecking] = useState(true)
  const [authBusy, setAuthBusy] = useState(false)
  const [authError, setAuthError] = useState<ApiError | null>(null)
  const [screen, setScreen] = useState<Screen>('overview')
  const [studentExams, setStudentExams] = useState<ApiExam[]>([])
  const [studentAttempts, setStudentAttempts] = useState<ApiAttempt[]>([])
  const [studentLoading, setStudentLoading] = useState(false)
  const [studentError, setStudentError] = useState<ApiError | null>(null)
  const [selectedStudentExamId, setSelectedStudentExamId] = useState('')
  const [attempt, setAttempt] = useState<ApiAttempt | null>(null)
  const [studentResult, setStudentResult] = useState<ApiResult | null>(null)
  const [studentBusy, setStudentBusy] = useState(false)
  const [adminExams, setAdminExams] = useState<ApiExam[]>([])
  const [students, setStudents] = useState<ApiStudent[]>([])
  const [adminAttempts, setAdminAttempts] = useState<ApiAttempt[]>([])
  const [adminLoading, setAdminLoading] = useState(false)
  const [adminError, setAdminError] = useState<ApiError | null>(null)
  const [message, setMessage] = useState('')

  const role: Role | null = user ? user.role === 'student' ? 'student' : 'admin' : null

  useEffect(() => {
    httpApi.getCurrentUser()
      .then((currentUser) => { setUser(currentUser); setAuthError(null) })
      .catch((error: unknown) => {
        const apiError = error instanceof HttpApiError ? error : { kind: 'network' as const, message: 'The server is unavailable right now. Please try again.' }
        if (apiError.kind !== 'authentication') setAuthError(apiError)
      })
      .finally(() => setSessionChecking(false))
  }, [])

  const refreshAdmin = async () => {
    setAdminLoading(true)
    setAdminError(null)
    try {
      const [nextExams, nextStudents, nextAttempts] = await Promise.all([httpApi.getExams(), httpApi.getStudents(), httpApi.getAttempts()])
      setAdminExams(nextExams)
      setStudents(nextStudents)
      setAdminAttempts(nextAttempts)
    } catch (error: unknown) {
      setAdminError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setAdminLoading(false)
    }
  }

  const refreshStudent = async () => {
    setStudentLoading(true)
    setStudentError(null)
    try {
      const [nextExams, nextAttempts] = await Promise.all([httpApi.getExams(), httpApi.getAttempts()])
      setStudentExams(nextExams)
      setStudentAttempts(nextAttempts)
      const activeAttempt = nextAttempts.find((item) => item.status === 'in_progress')
      const submittedAttempt = nextAttempts.find((item) => item.status === 'submitted')
      const restoredAttempt = activeAttempt ?? submittedAttempt ?? null
      const restoredExamId = restoredAttempt?.exam ?? nextExams[0]?.id ?? ''
      setSelectedStudentExamId((current) => current || restoredExamId)
      setAttempt(restoredAttempt)
      setStudentResult(restoredAttempt?.result ?? null)
      if (restoredAttempt?.status === 'in_progress') setScreen('exam')
      else if (restoredAttempt?.status === 'submitted') setScreen('results')
    } catch (error: unknown) {
      setStudentError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setStudentLoading(false)
    }
  }

  useEffect(() => {
    if (!user) return
    if (user.role === 'student') void refreshStudent()
    else void refreshAdmin()
  }, [user])

  const signIn = async (username: string, password: string) => {
    setAuthBusy(true)
    setAuthError(null)
    try {
      await httpApi.login(username, password)
      const currentUser = await httpApi.getCurrentUser()
      setUser(currentUser)
      setScreen('overview')
      setMessage('')
    } catch (error: unknown) {
      setAuthError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setAuthBusy(false)
    }
  }

  const signOut = async () => {
    setAuthBusy(true)
    setAuthError(null)
    try {
      await httpApi.logout()
      setUser(null)
      setAttempt(null)
      setStudentExams([])
      setStudentAttempts([])
      setStudentResult(null)
      setAdminAttempts([])
      setScreen('overview')
    } catch (error: unknown) {
      setAuthError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setAuthBusy(false)
    }
  }

  if (sessionChecking) return <main className="loading-screen" aria-live="polite">Checking session…</main>
  if (!user || !role) return <Login onSubmit={signIn} busy={authBusy} error={authError} />
  if (role === 'student' && studentLoading) return <main className="loading-screen" aria-live="polite">Loading your workspace…</main>

  const selectedStudentExam = studentExams.find((item) => item.id === selectedStudentExamId) ?? studentExams[0] ?? null
  const startExam = async () => {
    if (!selectedStudentExam) return
    setStudentBusy(true)
    setStudentError(null)
    try {
      const key = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`
      const started = await httpApi.startAttempt(selectedStudentExam.id, key)
      setAttempt(started)
      setStudentAttempts((items) => [...items.filter((item) => item.id !== started.id), started])
      setStudentResult(started.result)
      setScreen(started.status === 'submitted' ? 'results' : 'exam')
      setMessage(started.status === 'submitted' ? 'This attempt is already submitted.' : 'Attempt started on Django.')
    } catch (error: unknown) {
      setStudentError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setStudentBusy(false)
    }
  }
  const submit = async () => {
    if (!attempt || attempt.status === 'submitted' || studentBusy) return
    setStudentBusy(true)
    setStudentError(null)
    try {
      const result = await httpApi.submitAttempt(attempt.id)
      setStudentResult(result)
      const refreshed = await httpApi.getAttempts()
      const submitted = refreshed.find((item) => item.id === attempt.id) ?? { ...attempt, status: 'submitted' as const, submitted_at: new Date().toISOString(), result }
      setStudentAttempts(refreshed)
      setAttempt(submitted)
      setScreen('results')
      setMessage('Attempt submitted. Results were calculated by Django.')
    } catch (error: unknown) {
      setStudentError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setStudentBusy(false)
    }
  }

  return <div className="app-shell">
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand-mark"><span className="brand-dot" /> northstar<span className="brand-suffix">/exams</span></div>
      <div className="workspace-note"><span className="eyebrow">WORKSPACE</span><strong>{user.username}</strong><span className="muted">{user.role} · {user.organization ? `Org ${user.organization.slice(0, 8)}` : 'Unassigned'}</span></div>
      <nav>{navFor(role).map((item) => <button className={`nav-item ${screen === item.id ? 'active' : ''}`} key={item.id} onClick={() => setScreen(item.id)}><span>{item.label}</span><small>{item.hint}</small></button>)}</nav>
      <div className="sidebar-footer"><span className="status-dot" /> LAN node ready <button className="text-button" onClick={signOut} disabled={authBusy}>{authBusy ? 'Signing out…' : 'Sign out'}</button></div>
    </aside>
    <main className="content">
      <header className="topbar"><div><span className="eyebrow">{role === 'admin' ? 'STAFF CONSOLE' : 'STUDENT DESK'}</span><h1>{screen === 'studio' ? 'Build a clear assessment.' : screen === 'exam' ? 'Take your time.' : screen === 'results' ? role === 'admin' ? 'Review every attempt.' : 'See what stuck.' : `Welcome, ${user.username}.`}</h1></div><div className="topbar-meta"><span className="sync-state">● Session active</span><button className="avatar" aria-label={`Signed in as ${user.username}`}>{user.username.slice(0, 2).toUpperCase()}</button></div></header>
      {message && <div className="notice" role="status">{message}<button onClick={() => setMessage('')} aria-label="Dismiss message">×</button></div>}
      {adminError && role === 'admin' && <div className="notice" role="alert">{adminError.message}<button className="text-button" onClick={() => void refreshAdmin()}>Retry</button></div>}
      {studentError && role === 'student' && <div className="notice" role="alert">{studentError.message}<button className="text-button" onClick={() => void refreshStudent()}>Retry</button></div>}
      {role === 'admin' && screen === 'overview' && <AdminOverview exams={adminExams} students={students} attempts={adminAttempts} loading={adminLoading} onOpen={() => setScreen('studio')} onRefresh={refreshAdmin} />}
      {role === 'admin' && screen === 'studio' && <ExamStudio exams={adminExams} students={students} onRefresh={refreshAdmin} onMessage={setMessage} />}
      {role === 'admin' && screen === 'students' && <Students students={students} loading={adminLoading} onProvisioned={refreshAdmin} onMessage={setMessage} />}
      {role === 'admin' && screen === 'results' && <StaffResults attempts={adminAttempts} exams={adminExams} students={students} loading={adminLoading} onRefresh={refreshAdmin} />}
      {role === 'student' && screen === 'overview' && <StudentOverview exams={studentExams} selectedExamId={selectedStudentExam?.id ?? ''} onSelect={setSelectedStudentExamId} attempt={attempt} onStart={startExam} busy={studentBusy} />}
      {role === 'student' && screen === 'exam' && selectedStudentExam && attempt && <ExamRunner exam={selectedStudentExam} attempt={attempt} onChange={setAttempt} onSubmit={submit} busy={studentBusy} />}
      {role === 'student' && screen === 'results' && selectedStudentExam && <Results exam={selectedStudentExam} attempt={attempt} result={studentResult} onStart={startExam} busy={studentBusy} />}
    </main>
  </div>
}

function Login({ onSubmit, busy, error }: { onSubmit: (username: string, password: string) => Promise<void>; busy: boolean; error: ApiError | null }) {
  const errorMessage = error?.kind === 'authentication' ? 'Invalid credentials. Check your username and password.' : error?.message
  return <main className="login-page"><section className="login-card"><div className="brand-mark"><span className="brand-dot" /> northstar<span className="brand-suffix">/exams</span></div><p className="eyebrow">OPEN EXAM PLATFORM</p><h1>Make room for better questions.</h1><p className="lede">A calm, resilient exam workspace for classrooms on a LAN or in the cloud.</p>{errorMessage && <div className="notice" role="alert">{errorMessage}</div>}<form className="login-fields" onSubmit={(event) => { event.preventDefault(); const form = event.currentTarget; const values = new FormData(form); const username = String(values.get('username') ?? '').trim(); const password = String(values.get('password') ?? ''); if (!username || !password) return; void onSubmit(username, password).finally(() => form.reset()) }}><label htmlFor="login-identity">Email or student ID<input id="login-identity" name="username" placeholder="you@school.org" autoComplete="username" required disabled={busy} /></label><label htmlFor="login-password">Password<input id="login-password" name="password" type="password" placeholder="••••••••" autoComplete="current-password" required disabled={busy} /></label><button className="primary-button" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Enter workspace'}</button></form><small className="muted">Your password is sent only to Django over the configured development connection. The session is kept in an HttpOnly browser cookie.</small></section><aside className="login-aside"><span className="index-number">01</span><p>Local-first by design.</p><p className="muted">Keep an exam running when the internet cannot.</p></aside></main>
}

function AdminOverview({ exams, students, attempts, loading, onOpen, onRefresh }: { exams: ApiExam[]; students: ApiStudent[]; attempts: ApiAttempt[]; loading: boolean; onOpen: () => void; onRefresh: () => Promise<void> }) {
  const latest = exams[0]
  const questionCount = latest?.sections.reduce((total, section) => total + section.exam_questions.length, 0) ?? 0
  return <section className="page-grid"><div className="hero-panel"><span className="eyebrow">EXAM STUDIO · REAL DATA</span><h2>One sharp loop from question to result.</h2><p>Persist drafts, link questions, publish deliberately, then assign to a learner.</p><button className="primary-button" onClick={onOpen}>Open exam studio <span aria-hidden>↗</span></button></div><div className="metric-stack"><Metric label="Active learners" value={String(students.filter((student) => student.is_active).length)} note="From Django" /><Metric label="Exams" value={String(exams.length)} note="Persisted records" /><Metric label="Published" value={String(exams.filter((item) => item.status === 'published').length)} note="Server confirmed" /><Metric label="Active attempts" value={String(attempts.filter((item) => item.status === 'in_progress').length)} note="Currently in progress" /><Metric label="Submitted attempts" value={String(attempts.filter((item) => item.status === 'submitted').length)} note="Ready for review" /></div><section className="table-panel"><div className="panel-heading"><div><span className="eyebrow">PERSISTED ASSESSMENTS</span><h3>{latest?.title ?? 'No exams yet'}</h3></div><button className="secondary-button" onClick={() => void onRefresh()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button></div>{latest ? <div className="table-row"><span>{latest.status}</span><span>{questionCount} questions</span><span>{latest.duration_minutes} min</span><span>{latest.available_until ? 'Scheduled' : 'Open window'}</span></div> : <p className="muted">Create the first exam in Exams.</p>}</section></section>
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <div className="metric"><span className="eyebrow">{label}</span><strong>{value}</strong><span className="muted">{note}</span></div> }

function formatReviewDate(value: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function StaffResults({ attempts, exams, students, loading, onRefresh }: { attempts: ApiAttempt[]; exams: ApiExam[]; students: ApiStudent[]; loading: boolean; onRefresh: () => Promise<void> }) {
  const [selectedReview, setSelectedReview] = useState<ApiAttemptReview | null>(null)
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewError, setReviewError] = useState('')
  const [examFilter, setExamFilter] = useState('')
  const [studentFilter, setStudentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const filtered = attempts.filter((attempt) => (!examFilter || attempt.exam === examFilter) && (!studentFilter || attempt.student === studentFilter) && (!statusFilter || attempt.status === statusFilter))
  const openReview = async (attempt: ApiAttempt) => {
    setReviewLoading(true); setReviewError('')
    try { setSelectedReview(await httpApi.getAttemptReview(attempt.id)) } catch (error: unknown) { setReviewError(error instanceof HttpApiError ? error.message : 'The attempt review could not be loaded.') } finally { setReviewLoading(false) }
  }
  if (selectedReview) return <AttemptReview review={selectedReview} onBack={() => setSelectedReview(null)} />
  return <section className="table-panel"><div className="section-heading"><div><span className="eyebrow">RESULTS · ORGANIZATION SCOPED</span><h2>Review every attempt.</h2><p className="muted">Scores and statuses below are read from Django. Answer keys stay staff-only.</p></div><button className="secondary-button" onClick={() => void onRefresh()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh results'}</button></div><div className="option-grid" aria-label="Filter attempts"><label>Exam<select aria-label="Filter by exam" value={examFilter} onChange={(event) => setExamFilter(event.target.value)}><option value="">All exams</option>{exams.map((exam) => <option key={exam.id} value={exam.id}>{exam.title}</option>)}</select></label><label>Student<select aria-label="Filter by student" value={studentFilter} onChange={(event) => setStudentFilter(event.target.value)}><option value="">All students</option>{students.map((student) => <option key={student.id} value={student.id}>{student.name} · {student.student_id}</option>)}</select></label><label>Status<select aria-label="Filter by status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option><option value="submitted">Submitted</option><option value="in_progress">In progress</option></select></label></div>{reviewError && <div className="notice" role="alert">{reviewError}</div>}{reviewLoading && <p className="muted" role="status">Loading attempt review…</p>}{loading && <p className="muted" role="status">Loading attempts…</p>}{!loading && attempts.length === 0 && <div className="empty-state"><h3>No attempts yet.</h3><p className="muted">When a learner submits an assigned exam, the result will appear here.</p></div>}{!loading && attempts.length > 0 && filtered.length === 0 && <div className="empty-state"><h3>No matching attempts.</h3><p className="muted">Adjust the filters to find a persisted attempt.</p></div>}{!loading && filtered.length > 0 && <><div className="table-row table-head" aria-hidden="true"><span>Learner</span><span>Exam</span><span>Status</span><span>Result</span><span>Action</span></div>{filtered.map((attempt) => { const exam = exams.find((item) => item.id === attempt.exam); const student = students.find((item) => item.id === attempt.student); const result = attempt.result; return <div className="table-row" key={attempt.id}><span><strong>{attempt.student_name ?? student?.name ?? 'Learner'}</strong><small className="muted">{attempt.student_id ?? student?.student_id ?? attempt.student}</small></span><span><strong>{attempt.exam_title ?? exam?.title ?? 'Exam'}</strong><small className="muted">Started {formatReviewDate(attempt.started_at)}</small></span><span><span className={`status-chip ${attempt.status === 'submitted' ? 'status-success' : ''}`}>{attempt.status === 'submitted' ? 'Submitted' : 'In progress'}</span><small className="muted">{attempt.submitted_at ? formatReviewDate(attempt.submitted_at) : 'Not submitted'}</small></span><span>{result ? <><strong>{result.score}</strong><small className="muted">{result.correct_count} correct · {result.incorrect_count} incorrect · {result.unanswered_count} unanswered</small></> : <small className="muted">Awaiting submission</small>}</span><span><button className="secondary-button" onClick={() => void openReview(attempt)} disabled={reviewLoading}>{reviewLoading ? 'Loading…' : 'Review attempt'}</button></span></div> })}</>}</section>
}

function AttemptReview({ review, onBack }: { review: ApiAttemptReview; onBack: () => void }) {
  const submitted = review.status === 'submitted'
  const orderedQuestions = review.questions.slice().sort((a, b) => (a.section_position ?? 0) - (b.section_position ?? 0) || a.position - b.position)
  return <section className="table-panel"><div className="section-heading"><div><button className="text-button" onClick={onBack}>← Back to results</button><span className="eyebrow">ATTEMPT REVIEW · STAFF ONLY</span><h2>{review.exam_title ?? 'Attempt review'}</h2><p className="muted">{review.student_name ?? 'Learner'} · {review.student_id ?? review.student}</p></div><span className={`status-chip ${submitted ? 'status-success' : ''}`}>{submitted ? 'Submitted' : 'In progress'}</span></div><div className="metric-stack"><Metric label="Score" value={review.result?.score ?? '—'} note={submitted ? 'Server result' : 'Pending submission'} /><Metric label="Correct" value={String(review.result?.correct_count ?? '—')} note="Persisted result" /><Metric label="Incorrect" value={String(review.result?.incorrect_count ?? '—')} note="Persisted result" /><Metric label="Unanswered" value={String(review.result?.unanswered_count ?? '—')} note="Persisted result" /></div><div className="review-meta"><span>Started {formatReviewDate(review.started_at)}</span><span>Submitted {formatReviewDate(review.submitted_at)}</span></div>{!submitted && <div className="notice" role="status">This attempt is still in progress. Correctness and marks are hidden until submission.</div>}<div className="review-questions">{orderedQuestions.map((question, index) => <ReviewQuestion key={`${question.question_id}-${question.position}`} question={question} number={index + 1} showKey={submitted} />)}</div></section>
}

function ReviewQuestion({ question, number, showKey }: { question: ApiAttemptReview['questions'][number]; number: number; showKey: boolean }) {
  const stateLabel = question.answer_state === 'correct' ? 'Correct' : question.answer_state === 'incorrect' ? 'Incorrect' : question.answer_state === 'unanswered' ? 'Unanswered' : 'Pending'
  const response = Array.isArray(question.student_response) ? question.student_response.join(', ') : question.student_response == null ? 'No response' : String(question.student_response)
  const expected = Array.isArray(question.correct_answer) ? question.correct_answer.join(', ') : question.correct_answer == null ? 'Hidden until submission' : String(question.correct_answer)
  return <article className="review-question"><div className="review-question-heading"><span className="question-number">Question {number}</span><span className={`status-chip status-${question.answer_state}`}>{stateLabel}</span><span className="marks">{showKey ? `${question.marks_awarded ?? '0.00'} marks` : 'Marks pending'}</span></div><h3>{question.prompt}</h3><div className="review-answer-grid"><div><span className="eyebrow">STUDENT RESPONSE</span><p>{response}</p></div>{showKey && <div><span className="eyebrow">CORRECT ANSWER</span><p>{expected}</p></div>}</div>{question.options.length > 0 && <div className="review-options">{question.options.map((option) => { const label = String(option); const selected = Array.isArray(question.student_response) ? question.student_response.map(String).includes(label) : String(question.student_response ?? '') === label; const correct = showKey && (Array.isArray(question.correct_answer) ? question.correct_answer.map(String).includes(label) : String(question.correct_answer ?? '') === label); return <span className={`review-option ${selected ? 'selected' : ''} ${correct ? 'correct' : ''}`} key={label}>{label}{selected ? ' · selected' : ''}{correct ? ' · correct' : ''}</span> })}</div>}</article>
}

type QuestionDraft = { prompt: string; options: string; correct_answer: string; positive_marks: string; negative_marks: string }
const defaultQuestionDrafts: QuestionDraft[] = [
  { prompt: 'Which number is prime?', options: '2, 4, 6, 8', correct_answer: '2', positive_marks: '1', negative_marks: '0' },
  { prompt: 'Which planet is known as the Red Planet?', options: 'Mars, Venus, Jupiter, Mercury', correct_answer: 'Mars', positive_marks: '1', negative_marks: '0' },
  { prompt: 'What is 2 + 2?', options: '3, 4, 5, 6', correct_answer: '4', positive_marks: '1', negative_marks: '0' },
]

function ExamStudio({ exams, students, onRefresh, onMessage }: { exams: ApiExam[]; students: ApiStudent[]; onRefresh: () => Promise<void>; onMessage: (message: string) => void }) {
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState('30')
  const [availableFrom, setAvailableFrom] = useState('')
  const [availableUntil, setAvailableUntil] = useState('')
  const [sectionName, setSectionName] = useState('Demo Section')
  const [questions, setQuestions] = useState<QuestionDraft[]>(defaultQuestionDrafts)
  const [selectedExamId, setSelectedExamId] = useState('')
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const selectedExam = exams.find((item) => item.id === selectedExamId) ?? exams[0]
  const updateQuestion = (index: number, patch: Partial<QuestionDraft>) => setQuestions((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item))
  const toIso = (value: string) => value ? new Date(value).toISOString() : null
  const createWorkflow = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try {
      if (!title.trim()) throw new Error('Exam title is required.')
      const created = await httpApi.createExam({ title: title.trim(), duration_minutes: Number(duration), available_from: toIso(availableFrom), available_until: toIso(availableUntil) })
      const section = await httpApi.createSection({ exam: created.id, name: sectionName.trim() || 'Demo Section', position: 1 })
      for (const [index, question] of questions.entries()) {
        const options = question.options.split(',').map((item) => item.trim()).filter(Boolean)
        const createdQuestion = await httpApi.createQuestion({ question_type: 'single', prompt: question.prompt.trim(), options, correct_answer: question.correct_answer.trim(), positive_marks: question.positive_marks, negative_marks: question.negative_marks })
        await httpApi.attachQuestion({ section: section.id, question_id: createdQuestion.id, position: index + 1 })
      }
      setSelectedExamId(created.id); onMessage('Draft saved to Django with exactly three questions.'); await onRefresh()
    } catch (caught: unknown) { setError(caught instanceof HttpApiError ? caught.message : caught instanceof Error ? caught.message : 'The server is unavailable right now.') } finally { setBusy(false) }
  }
  const publish = async () => {
    if (!selectedExam) return
    setBusy(true); setError('')
    try { await httpApi.publishExam(selectedExam.id); onMessage('Exam published by Django.'); await onRefresh() } catch (caught: unknown) { setError(caught instanceof HttpApiError ? caught.message : 'The server is unavailable right now.') } finally { setBusy(false) }
  }
  const assign = async () => {
    if (!selectedExam || !selectedStudentId) return
    setBusy(true); setError('')
    try { await httpApi.assignExam(selectedExam.id, selectedStudentId); onMessage('Exam assignment confirmed by Django.'); await onRefresh() } catch (caught: unknown) { setError(caught instanceof HttpApiError ? caught.message : 'The server is unavailable right now.') } finally { setBusy(false) }
  }
  return <section className="studio-layout"><div className="studio-main"><div className="section-heading"><div><span className="eyebrow">REAL DJANGO AUTHORING</span><h2>Create a persisted assessment.</h2></div><span className="status-chip">{selectedExam?.status ?? 'new draft'}</span></div>{error && <div className="notice" role="alert">{error}</div>}<form className="question-editor" onSubmit={createWorkflow}><label className="field-wide">Exam title<input required value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Hackathon Demo Exam" /></label><div className="option-grid"><label>Duration (minutes)<input required type="number" min="1" max="240" value={duration} onChange={(event) => setDuration(event.target.value)} /></label><label>Section name<input required value={sectionName} onChange={(event) => setSectionName(event.target.value)} /></label><label>Available from<input type="datetime-local" value={availableFrom} onChange={(event) => setAvailableFrom(event.target.value)} /></label><label>Available until<input type="datetime-local" value={availableUntil} onChange={(event) => setAvailableUntil(event.target.value)} /></label></div>{questions.map((question, index) => <fieldset key={index}><legend>Question {index + 1} · single-choice</legend><label>Prompt<textarea required rows={2} value={question.prompt} onChange={(event) => updateQuestion(index, { prompt: event.target.value })} /></label><label>Options, comma separated<input required value={question.options} onChange={(event) => updateQuestion(index, { options: event.target.value })} /></label><label>Correct answer<input required value={question.correct_answer} onChange={(event) => updateQuestion(index, { correct_answer: event.target.value })} /></label><div className="option-grid"><label>Positive marks<input required type="number" min="0" step="0.01" value={question.positive_marks} onChange={(event) => updateQuestion(index, { positive_marks: event.target.value })} /></label><label>Negative marks<input required type="number" min="0" step="0.01" value={question.negative_marks} onChange={(event) => updateQuestion(index, { negative_marks: event.target.value })} /></label></div></fieldset>)}<button className="primary-button" type="submit" disabled={busy}>{busy ? 'Saving…' : 'Create exam and save 3 questions'}</button></form></div><aside className="studio-rail"><span className="eyebrow">PERSISTED EXAMS</span><label>Open exam<select value={selectedExamId || selectedExam?.id || ''} onChange={(event) => setSelectedExamId(event.target.value)}><option value="">No exam selected</option>{exams.map((item) => <option key={item.id} value={item.id}>{item.title} · {item.status}</option>)}</select></label>{selectedExam && <><p className="muted">{selectedExam.sections.reduce((total, section) => total + section.exam_questions.length, 0)} linked questions · {selectedExam.duration_minutes} minutes</p><button className="primary-button" onClick={() => void publish()} disabled={busy || selectedExam.status !== 'draft'}>{busy ? 'Publishing…' : selectedExam.status === 'published' ? 'Published' : 'Publish exam'}</button><label>Assign to student<select value={selectedStudentId} onChange={(event) => setSelectedStudentId(event.target.value)}><option value="">Choose provisioned student</option>{students.map((student) => <option key={student.id} value={student.id}>{student.name} · {student.student_id}</option>)}</select></label><button className="secondary-button" onClick={() => void assign()} disabled={busy || selectedExam.status !== 'published' || !selectedStudentId}>{busy ? 'Assigning…' : 'Assign exam'}</button></>}<div className="rail-note"><strong>Publish gate</strong><p className="muted">Server confirmation is required before status or assignment success is shown.</p></div></aside></section>
}

function Students({ students, loading, onProvisioned, onMessage }: { students: ApiStudent[]; loading: boolean; onProvisioned: () => Promise<void>; onMessage: (message: string) => void }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', studentId: '', password: '' })
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try {
      await httpApi.provisionStudent({ name: form.name.trim(), student_id: form.studentId.trim(), username: form.studentId.trim(), temporary_password: form.password })
      setForm({ name: '', studentId: '', password: '' }); setOpen(false); onMessage('Student provisioned and saved to Django.'); await onProvisioned()
    } catch (caught: unknown) { setError(caught instanceof HttpApiError ? caught.message : 'The server is unavailable right now. Please try again.') } finally { setBusy(false) }
  }
  return <section className="table-panel"><div className="section-heading"><div><span className="eyebrow">LEARNERS</span><h2>Roster with fewer surprises.</h2></div><button className="primary-button" onClick={() => setOpen((value) => !value)}>{open ? 'Close form' : 'Add learner'}</button></div>{open && <form className="notice" onSubmit={submit}><div className="option-grid"><label>Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label>Student ID<input required value={form.studentId} onChange={(event) => setForm({ ...form, studentId: event.target.value })} /></label><label>Temporary password<input required type="password" autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label></div>{error && <p role="alert">{error}</p>}<button className="primary-button" type="submit" disabled={busy}>{busy ? 'Provisioning…' : 'Provision student'}</button></form>}<div className="table-row table-head"><span>Name</span><span>Student ID</span><span>Access</span><span>Status</span></div>{loading && <p className="muted">Loading students…</p>}{!loading && students.length === 0 && <p className="muted">No students yet.</p>}{students.map((student) => <div className="table-row" key={student.id}><span>{student.name}</span><span>{student.student_id}</span><span>{student.is_active ? 'Ready' : 'Inactive'}</span><span>{student.is_active ? 'Active' : 'Inactive'}</span></div>)}</section>
}

function studentQuestions(exam: ApiExam) {
  return exam.sections.flatMap((section) => section.exam_questions).sort((a, b) => a.position - b.position).map((link) => link.question)
}

function StudentOverview({ exams, selectedExamId, onSelect, attempt, onStart, busy }: { exams: ApiExam[]; selectedExamId: string; onSelect: (id: string) => void; attempt: ApiAttempt | null; onStart: () => void; busy: boolean }) {
  if (exams.length === 0) return <section className="page-grid"><div className="hero-panel student-hero"><span className="eyebrow">ASSIGNED LEARNING</span><h2>No published exams yet.</h2><p>Your teacher has not assigned an available exam to this account.</p></div></section>
  const exam = exams.find((item) => item.id === selectedExamId) ?? exams[0]
  const questions = studentQuestions(exam)
  const activeAttempt = attempt?.exam === exam.id && attempt.status === 'in_progress'
  const submittedAttempt = attempt?.exam === exam.id && attempt.status === 'submitted'
  return <section className="page-grid"><div className="hero-panel student-hero"><span className="eyebrow">ASSIGNED PRACTICE · FROM DJANGO</span><h2>{exam.title}</h2><p>{activeAttempt ? 'Resume the attempt from the server deadline.' : submittedAttempt ? 'This attempt is submitted. Review the server result.' : 'Start when you are ready. Your attempt and answers are persisted by Django.'}</p><button className="primary-button" onClick={onStart} disabled={busy || submittedAttempt}>{busy ? 'Starting…' : activeAttempt ? 'Resume attempt' : submittedAttempt ? 'Submitted' : 'Start exam'} <span aria-hidden>→</span></button></div><div className="metric-stack"><Metric label="Time limit" value={`${exam.duration_minutes} min`} note="Server deadline" /><Metric label="Questions" value={String(questions.length)} note="Published content" /><Metric label="Availability" value={exam.available_until ? 'Scheduled' : 'Open'} note={exam.status} /></div><section className="table-panel"><div className="panel-heading"><div><span className="eyebrow">ASSIGNED EXAMS</span><h3>Choose an assessment</h3></div></div>{exams.map((item) => <button className={`question-map ${item.id === exam.id ? 'active' : ''}`} key={item.id} onClick={() => onSelect(item.id)}><span>{item.title}</span><span>{item.duration_minutes} min · {studentQuestions(item).length} questions</span></button>)}</section></section>
}

function ExamRunner({ exam, attempt, onChange, onSubmit, busy }: { exam: ApiExam; attempt: ApiAttempt; onChange: (attempt: ApiAttempt) => void; onSubmit: () => void; busy: boolean }) {
  const [index, setIndex] = useState(0)
  const questions = studentQuestions(exam)
  const [remaining, setRemaining] = useState(Math.max(0, Math.ceil((new Date(attempt.deadline_at).getTime() - Date.now()) / 1000)))
  const [saving, setSaving] = useState<string | null>(null)
  const [saveError, setSaveError] = useState('')
  const [expiredSubmitted, setExpiredSubmitted] = useState(false)
  const question = questions[index]
  useEffect(() => { const timer = window.setInterval(() => setRemaining(Math.max(0, Math.ceil((new Date(attempt.deadline_at).getTime() - Date.now()) / 1000))), 1000); return () => window.clearInterval(timer) }, [attempt.deadline_at])
  useEffect(() => { if (remaining === 0 && !expiredSubmitted && attempt.status === 'in_progress') { setExpiredSubmitted(true); onSubmit() } }, [remaining, expiredSubmitted, attempt.status, onSubmit])
  const answer = attempt.answers.find((item) => item.question === question.id)?.value as string | string[] | undefined
  const choose = async (value: unknown) => {
    setSaving(question.id); setSaveError('')
    try {
      const saved = await httpApi.saveAnswer(attempt.id, question.id, value)
      const nextAnswers = [...attempt.answers.filter((item) => item.question !== question.id), saved]
      onChange({ ...attempt, answers: nextAnswers })
    } catch (error: unknown) {
      setSaveError(error instanceof HttpApiError ? error.message : 'Answer could not be saved. Please retry.')
    } finally { setSaving(null) }
  }
  const options = (question.options ?? []).map((option) => String(option))
  const toggleMultiple = (value: string) => { const current = Array.isArray(answer) ? answer.map(String) : []; void choose(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]) }
  return <section className="exam-layout"><div className="exam-main"><div className="exam-bar"><div><span className="eyebrow">{exam.title}</span><h2>Question {index + 1} of {questions.length}</h2></div><div className={`timer ${remaining < 30 ? 'urgent' : ''}`} aria-live="polite"><span className="eyebrow">TIME LEFT</span><strong>{String(Math.floor(remaining / 60)).padStart(2, '0')}:{String(remaining % 60).padStart(2, '0')}</strong></div></div><div className="question-card"><p className="question-type">{question.question_type === 'single' ? 'Choose one' : question.question_type === 'multi' ? 'Choose all that apply' : 'Enter a number'}</p><h3>{question.prompt}</h3>{question.question_type === 'numeric' && <input className="numeric-input" inputMode="decimal" aria-label="Numeric answer" value={typeof answer === 'string' ? answer : ''} onChange={(event) => void choose(event.target.value)} disabled={busy || saving !== null} />}{question.question_type !== 'numeric' && <div className="answer-list">{options.map((option, optionIndex) => { const selected = Array.isArray(answer) ? answer.includes(option) : answer === option; return <button className={`answer-option ${selected ? 'selected' : ''}`} key={option} onClick={() => question.question_type === 'multi' ? toggleMultiple(option) : void choose(option)} aria-pressed={selected} disabled={busy || saving !== null}><span className="option-letter">{String.fromCharCode(65 + optionIndex)}</span>{option}</button> })}</div>}{saving === question.id && <p className="muted" role="status">Saving…</p>}{!saving && !saveError && attempt.answers.some((item) => item.question === question.id) && <p className="muted" role="status">Saved</p>}{saveError && <p className="notice" role="alert">{saveError}</p>}<div className="question-actions"><button className="secondary-button" onClick={() => setIndex((index + questions.length - 1) % questions.length)} disabled={busy}>Previous</button><button className="primary-button" onClick={() => index === questions.length - 1 ? onSubmit() : setIndex(index + 1)} disabled={busy || saving !== null}>{index === questions.length - 1 ? 'Submit attempt' : 'Save & next'}</button></div></div></div><aside className="exam-rail"><span className="eyebrow">QUESTION MAP</span>{questions.map((item, itemIndex) => <button className={`question-map ${itemIndex === index ? 'active' : ''} ${attempt.answers.some((answerItem) => answerItem.question === item.id) ? 'answered' : ''}`} key={item.id} onClick={() => setIndex(itemIndex)}><span>0{itemIndex + 1}</span><span>{attempt.answers.some((answerItem) => answerItem.question === item.id) ? 'Answered' : 'Not answered'}</span></button>)}<p className="muted small-copy">Answers are persisted by Django. The timer uses the server deadline.</p></aside></section>
}

function Results({ exam, attempt, result, onStart, busy }: { exam: ApiExam; attempt: ApiAttempt | null; result: ApiResult | null; onStart: () => void; busy: boolean }) {
  const questions = studentQuestions(exam)
  const submitted = attempt?.status === 'submitted' || Boolean(result)
  return <section className="results-layout"><div className="result-hero"><span className="eyebrow">ATTEMPT RECEIPT · SERVER RESULT</span><h2>{submitted ? 'Nice work showing up.' : 'No submitted attempt yet.'}</h2><p>{submitted ? `Your result for ${exam.title} is stored by Django.` : 'Start the assigned exam when you are ready.'}</p>{!submitted && <button className="primary-button" onClick={onStart} disabled={busy}>{busy ? 'Starting…' : 'Start exam'}</button>}</div>{submitted && <div className="result-breakdown"><div className="score-block"><span className="eyebrow">SCORE</span><strong>{result?.score ?? attempt?.result?.score ?? '0.00'}</strong><span className="muted">Server calculated</span></div><div className="result-list"><div className="result-row"><span>Correct</span><span>{result?.correct_count ?? attempt?.result?.correct_count ?? 0}</span></div><div className="result-row"><span>Incorrect</span><span>{result?.incorrect_count ?? attempt?.result?.incorrect_count ?? 0}</span></div><div className="result-row"><span>Unanswered</span><span>{result?.unanswered_count ?? attempt?.result?.unanswered_count ?? questions.length}</span></div>{questions.map((question) => <div className="result-row" key={question.id}><span>{question.prompt}</span><span>{attempt?.answers.some((item) => item.question === question.id) ? 'Recorded' : 'Not answered'}</span></div>)}</div></div>}</section>
}

export default App
