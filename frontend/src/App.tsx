import { useEffect, useState, type FormEvent } from 'react'
import { httpApi, HttpApiError } from './api'
import { mockApi } from './api/mockApi'
import type { ApiError, ApiExam, ApiStudent, Attempt, AuthenticatedUser, Exam, Question, Role } from './types'

type Screen = 'overview' | 'studio' | 'students' | 'exam' | 'results'

const navFor = (role: Role): { id: Screen; label: string; hint: string }[] => role === 'admin'
  ? [{ id: 'overview', label: 'Workspace', hint: 'Today at a glance' }, { id: 'studio', label: 'Exam studio', hint: 'Author and preview' }, { id: 'students', label: 'Learners', hint: 'Roster and access' }]
  : [{ id: 'overview', label: 'My desk', hint: 'Assigned learning' }, { id: 'exam', label: 'Practice exam', hint: 'One active attempt' }, { id: 'results', label: 'Results', hint: 'Feedback and marks' }]

function App() {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [sessionChecking, setSessionChecking] = useState(true)
  const [authBusy, setAuthBusy] = useState(false)
  const [authError, setAuthError] = useState<ApiError | null>(null)
  const [screen, setScreen] = useState<Screen>('overview')
  const [exam, setExam] = useState<Exam | null>(null)
  const [adminExams, setAdminExams] = useState<ApiExam[]>([])
  const [students, setStudents] = useState<ApiStudent[]>([])
  const [adminLoading, setAdminLoading] = useState(false)
  const [adminError, setAdminError] = useState<ApiError | null>(null)
  const [attempt, setAttempt] = useState<Attempt | undefined>()
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
      const [nextExams, nextStudents] = await Promise.all([httpApi.getExams(), httpApi.getStudents()])
      setAdminExams(nextExams)
      setStudents(nextStudents)
    } catch (error: unknown) {
      setAdminError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setAdminLoading(false)
    }
  }

  useEffect(() => {
    if (!user) return
    if (user.role === 'student') mockApi.getExam().then(setExam)
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
      setAttempt(undefined)
      setScreen('overview')
    } catch (error: unknown) {
      setAuthError(error instanceof HttpApiError ? error : { kind: 'network', message: 'The server is unavailable right now. Please try again.' })
    } finally {
      setAuthBusy(false)
    }
  }

  if (sessionChecking) return <main className="loading-screen" aria-live="polite">Checking session…</main>
  if (!user || !role) return <Login onSubmit={signIn} busy={authBusy} error={authError} />
  if (role === 'student' && !exam) return <main className="loading-screen" aria-live="polite">Loading your workspace…</main>

  const startExam = async () => { setAttempt(await mockApi.createAttempt()); setScreen('exam'); setMessage('The attempt is local-first and will sync when a server is available.') }
  const submit = async () => { setAttempt(await mockApi.submitAttempt()); setScreen('results'); setMessage('Attempt submitted. Marks are calculated by the server contract.') }

  return <div className="app-shell">
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand-mark"><span className="brand-dot" /> northstar<span className="brand-suffix">/exams</span></div>
      <div className="workspace-note"><span className="eyebrow">WORKSPACE</span><strong>{user.username}</strong><span className="muted">{user.role} · {user.organization ? `Org ${user.organization.slice(0, 8)}` : 'Unassigned'}</span></div>
      <nav>{navFor(role).map((item) => <button className={`nav-item ${screen === item.id ? 'active' : ''}`} key={item.id} onClick={() => setScreen(item.id)}><span>{item.label}</span><small>{item.hint}</small></button>)}</nav>
      <div className="sidebar-footer"><span className="status-dot" /> LAN node ready <button className="text-button" onClick={signOut} disabled={authBusy}>{authBusy ? 'Signing out…' : 'Sign out'}</button></div>
    </aside>
    <main className="content">
      <header className="topbar"><div><span className="eyebrow">{role === 'admin' ? 'ADMIN CONSOLE' : 'STUDENT DESK'}</span><h1>{screen === 'studio' ? 'Build a clear assessment.' : screen === 'exam' ? 'Take your time.' : screen === 'results' ? 'See what stuck.' : `Welcome, ${user.username}.`}</h1></div><div className="topbar-meta"><span className="sync-state">● Session active</span><button className="avatar" aria-label={`Signed in as ${user.username}`}>{user.username.slice(0, 2).toUpperCase()}</button></div></header>
      {message && <div className="notice" role="status">{message}<button onClick={() => setMessage('')} aria-label="Dismiss message">×</button></div>}
      {adminError && role === 'admin' && <div className="notice" role="alert">{adminError.message}<button className="text-button" onClick={() => void refreshAdmin()}>Retry</button></div>}
      {role === 'admin' && screen === 'overview' && <AdminOverview exams={adminExams} students={students} loading={adminLoading} onOpen={() => setScreen('studio')} onRefresh={refreshAdmin} />}
      {role === 'admin' && screen === 'studio' && <ExamStudio exams={adminExams} students={students} onRefresh={refreshAdmin} onMessage={setMessage} />}
      {role === 'admin' && screen === 'students' && <Students students={students} loading={adminLoading} onProvisioned={refreshAdmin} onMessage={setMessage} />}
      {role === 'student' && screen === 'overview' && <StudentOverview exam={exam!} onStart={startExam} />}
      {role === 'student' && screen === 'exam' && attempt && <ExamRunner exam={exam!} attempt={attempt} onChange={setAttempt} onSubmit={submit} />}
      {role === 'student' && screen === 'results' && <Results exam={exam!} attempt={attempt} onStart={startExam} />}
    </main>
  </div>
}

function Login({ onSubmit, busy, error }: { onSubmit: (username: string, password: string) => Promise<void>; busy: boolean; error: ApiError | null }) {
  const errorMessage = error?.kind === 'authentication' ? 'Invalid credentials. Check your username and password.' : error?.message
  return <main className="login-page"><section className="login-card"><div className="brand-mark"><span className="brand-dot" /> northstar<span className="brand-suffix">/exams</span></div><p className="eyebrow">OPEN EXAM PLATFORM</p><h1>Make room for better questions.</h1><p className="lede">A calm, resilient exam workspace for classrooms on a LAN or in the cloud.</p>{errorMessage && <div className="notice" role="alert">{errorMessage}</div>}<form className="login-fields" onSubmit={(event) => { event.preventDefault(); const form = event.currentTarget; const values = new FormData(form); const username = String(values.get('username') ?? '').trim(); const password = String(values.get('password') ?? ''); if (!username || !password) return; void onSubmit(username, password).finally(() => form.reset()) }}><label htmlFor="login-identity">Email or student ID<input id="login-identity" name="username" placeholder="you@school.org" autoComplete="username" required disabled={busy} /></label><label htmlFor="login-password">Password<input id="login-password" name="password" type="password" placeholder="••••••••" autoComplete="current-password" required disabled={busy} /></label><button className="primary-button" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Enter workspace'}</button></form><small className="muted">Your password is sent only to Django over the configured development connection. The session is kept in an HttpOnly browser cookie.</small></section><aside className="login-aside"><span className="index-number">01</span><p>Local-first by design.</p><p className="muted">Keep an exam running when the internet cannot.</p></aside></main>
}

function AdminOverview({ exams, students, loading, onOpen, onRefresh }: { exams: ApiExam[]; students: ApiStudent[]; loading: boolean; onOpen: () => void; onRefresh: () => Promise<void> }) {
  const latest = exams[0]
  const questionCount = latest?.sections.reduce((total, section) => total + section.exam_questions.length, 0) ?? 0
  return <section className="page-grid"><div className="hero-panel"><span className="eyebrow">EXAM STUDIO · REAL DATA</span><h2>One sharp loop from question to result.</h2><p>Persist drafts, link questions, publish deliberately, then assign to a learner.</p><button className="primary-button" onClick={onOpen}>Open exam studio <span aria-hidden>↗</span></button></div><div className="metric-stack"><Metric label="Active learners" value={String(students.filter((student) => student.is_active).length)} note="From Django" /><Metric label="Exams" value={String(exams.length)} note="Persisted records" /><Metric label="Published" value={String(exams.filter((item) => item.status === 'published').length)} note="Server confirmed" /></div><section className="table-panel"><div className="panel-heading"><div><span className="eyebrow">PERSISTED ASSESSMENTS</span><h3>{latest?.title ?? 'No exams yet'}</h3></div><button className="secondary-button" onClick={() => void onRefresh()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</button></div>{latest ? <div className="table-row"><span>{latest.status}</span><span>{questionCount} questions</span><span>{latest.duration_minutes} min</span><span>{latest.available_until ? 'Scheduled' : 'Open window'}</span></div> : <p className="muted">Create the first exam in Exam studio.</p>}</section></section>
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <div className="metric"><span className="eyebrow">{label}</span><strong>{value}</strong><span className="muted">{note}</span></div> }

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

function StudentOverview({ exam, onStart }: { exam: Exam; onStart: () => void }) { return <section className="page-grid"><div className="hero-panel student-hero"><span className="eyebrow">ASSIGNED PRACTICE</span><h2>Ready when you are.</h2><p>{exam.title} is available offline on this classroom node. Your answers will sync when the connection returns.</p><button className="primary-button" onClick={onStart}>Read instructions <span aria-hidden>→</span></button></div><div className="metric-stack"><Metric label="Time limit" value={`${Math.round(exam.durationSeconds / 60)} min`} note="Server deadline" /><Metric label="Questions" value={String(exam.questions.length)} note="3 formats" /><Metric label="Status" value="Open" note="One attempt available" /></div></section> }

function ExamRunner({ exam, attempt, onChange, onSubmit }: { exam: Exam; attempt: Attempt; onChange: (attempt: Attempt) => void; onSubmit: () => void }) {
  const [index, setIndex] = useState(0)
  const [remaining, setRemaining] = useState(Math.max(0, Math.ceil((attempt.deadline - Date.now()) / 1000)))
  const question = exam.questions[index]
  useEffect(() => { const timer = window.setInterval(() => setRemaining(Math.max(0, Math.ceil((attempt.deadline - Date.now()) / 1000))), 1000); return () => window.clearInterval(timer) }, [attempt.deadline])
  useEffect(() => { if (remaining === 0 && !attempt.submittedAt) onSubmit() }, [remaining, attempt.submittedAt, onSubmit])
  const answer = attempt.answers[question.id]
  const choose = async (value: string | string[]) => { const saved = await mockApi.saveAnswer(question.id, value); onChange(saved) }
  const toggleMultiple = (value: string) => { const current = Array.isArray(answer) ? answer : []; choose(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]) }
  return <section className="exam-layout"><div className="exam-main"><div className="exam-bar"><div><span className="eyebrow">{exam.title}</span><h2>Question {index + 1} of {exam.questions.length}</h2></div><div className={`timer ${remaining < 30 ? 'urgent' : ''}`} aria-live="polite"><span className="eyebrow">TIME LEFT</span><strong>{String(Math.floor(remaining / 60)).padStart(2, '0')}:{String(remaining % 60).padStart(2, '0')}</strong></div></div><div className="question-card"><p className="question-type">{question.type === 'single' ? 'Choose one' : question.type === 'multiple' ? 'Choose all that apply' : 'Enter a number'}</p><h3>{question.prompt}</h3>{question.type === 'numeric' && <input className="numeric-input" inputMode="decimal" aria-label="Numeric answer" value={typeof answer === 'string' ? answer : ''} onChange={(event) => choose(event.target.value)} />}{question.options && <div className="answer-list">{question.options.map((option) => { const selected = Array.isArray(answer) ? answer.includes(option) : answer === option; return <button className={`answer-option ${selected ? 'selected' : ''}`} key={option} onClick={() => question.type === 'multiple' ? toggleMultiple(option) : choose(option)} aria-pressed={selected}><span className="option-letter">{String.fromCharCode(65 + question.options!.indexOf(option))}</span>{option}</button> })}</div>}<div className="question-actions"><button className="secondary-button" onClick={() => setIndex((index + exam.questions.length - 1) % exam.questions.length)}>Previous</button><button className="primary-button" onClick={() => index === exam.questions.length - 1 ? onSubmit() : setIndex(index + 1)}>{index === exam.questions.length - 1 ? 'Submit attempt' : 'Save & next'}</button></div></div></div><aside className="exam-rail"><span className="eyebrow">QUESTION MAP</span>{exam.questions.map((item, itemIndex) => <button className={`question-map ${itemIndex === index ? 'active' : ''} ${attempt.answers[item.id] !== undefined ? 'answered' : ''}`} key={item.id} onClick={() => setIndex(itemIndex)}><span>0{itemIndex + 1}</span><span>{attempt.answers[item.id] !== undefined ? 'Answered' : 'Not answered'}</span></button>)}<p className="muted small-copy">Answers save on this device first. The server accepts the final attempt once.</p></aside></section>
}

function Results({ exam, attempt, onStart }: { exam: Exam; attempt?: Attempt; onStart: () => void }) { return <section className="results-layout"><div className="result-hero"><span className="eyebrow">ATTEMPT RECEIPT</span><h2>{attempt?.submittedAt ? 'Nice work showing up.' : 'No attempt yet.'}</h2><p>{attempt?.submittedAt ? `You earned ${attempt.score ?? 0} marks on ${exam.title}.` : 'Start the practice exam when you are ready.'}</p>{!attempt?.submittedAt && <button className="primary-button" onClick={onStart}>Start exam</button>}</div>{attempt?.submittedAt && <div className="result-breakdown"><div className="score-block"><span className="eyebrow">SCORE</span><strong>{attempt.score ?? 0}</strong><span className="muted">out of {exam.questions.reduce((sum, item) => sum + item.points, 0)}</span></div><div className="result-list">{exam.questions.map((question) => <div className="result-row" key={question.id}><span>{question.prompt}</span><span>{attempt.answers[question.id] === undefined ? 'Not answered' : 'Recorded'}</span></div>)}</div></div>}</section> }

export default App
