import { useEffect, useState } from 'react'
import { httpApi, HttpApiError } from './api'
import { mockApi } from './api/mockApi'
import type { ApiError, Attempt, AuthenticatedUser, Exam, Question, Role } from './types'

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

  useEffect(() => { if (user) mockApi.getExam().then(setExam) }, [user])

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
  if (!exam) return <main className="loading-screen" aria-live="polite">Loading your workspace…</main>

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
      {role === 'admin' && screen === 'overview' && <AdminOverview exam={exam} onOpen={() => setScreen('studio')} />}
      {role === 'admin' && screen === 'studio' && <ExamStudio exam={exam} onPublish={(updated) => { setExam(updated); setMessage('Draft saved locally. Publishing remains a deliberate next step.'); }} />}
      {role === 'admin' && screen === 'students' && <Students />}
      {role === 'student' && screen === 'overview' && <StudentOverview exam={exam} onStart={startExam} />}
      {role === 'student' && screen === 'exam' && attempt && <ExamRunner exam={exam} attempt={attempt} onChange={setAttempt} onSubmit={submit} />}
      {role === 'student' && screen === 'results' && <Results exam={exam} attempt={attempt} onStart={startExam} />}
    </main>
  </div>
}

function Login({ onSubmit, busy, error }: { onSubmit: (username: string, password: string) => Promise<void>; busy: boolean; error: ApiError | null }) {
  const errorMessage = error?.kind === 'authentication' ? 'Invalid credentials. Check your username and password.' : error?.message
  return <main className="login-page"><section className="login-card"><div className="brand-mark"><span className="brand-dot" /> northstar<span className="brand-suffix">/exams</span></div><p className="eyebrow">OPEN EXAM PLATFORM</p><h1>Make room for better questions.</h1><p className="lede">A calm, resilient exam workspace for classrooms on a LAN or in the cloud.</p>{errorMessage && <div className="notice" role="alert">{errorMessage}</div>}<form className="login-fields" onSubmit={(event) => { event.preventDefault(); const form = event.currentTarget; const values = new FormData(form); const username = String(values.get('username') ?? '').trim(); const password = String(values.get('password') ?? ''); if (!username || !password) return; void onSubmit(username, password).finally(() => form.reset()) }}><label htmlFor="login-identity">Email or student ID<input id="login-identity" name="username" placeholder="you@school.org" autoComplete="username" required disabled={busy} /></label><label htmlFor="login-password">Password<input id="login-password" name="password" type="password" placeholder="••••••••" autoComplete="current-password" required disabled={busy} /></label><button className="primary-button" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Enter workspace'}</button></form><small className="muted">Your password is sent only to Django over the configured development connection. The session is kept in an HttpOnly browser cookie.</small></section><aside className="login-aside"><span className="index-number">01</span><p>Local-first by design.</p><p className="muted">Keep an exam running when the internet cannot.</p></aside></main>
}

function AdminOverview({ exam, onOpen }: { exam: Exam; onOpen: () => void }) {
  return <section className="page-grid"><div className="hero-panel"><span className="eyebrow">EXAM STUDIO</span><h2>One sharp loop from question to result.</h2><p>Draft locally, preview with confidence, then publish a version your students can trust.</p><button className="primary-button" onClick={onOpen}>Open exam studio <span aria-hidden>↗</span></button></div><div className="metric-stack"><Metric label="Active learners" value="24" note="+6 this week" /><Metric label="Draft exams" value="3" note="1 ready to review" /><Metric label="LAN sync" value="100%" note="Last check 2m ago" /></div><section className="table-panel"><div className="panel-heading"><div><span className="eyebrow">RECENT ASSESSMENT</span><h3>{exam.title}</h3></div><span className="status-chip">{exam.status}</span></div><div className="table-row table-head"><span>Version</span><span>Questions</span><span>Duration</span><span>Owner</span></div><div className="table-row"><span>Draft 0.3</span><span>{exam.questions.length}</span><span>{Math.round(exam.durationSeconds / 60)} min</span><span>Harbor Learning</span></div></section></section>
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <div className="metric"><span className="eyebrow">{label}</span><strong>{value}</strong><span className="muted">{note}</span></div> }

function ExamStudio({ exam, onPublish }: { exam: Exam; onPublish: (exam: Exam) => void }) {
  const [draft, setDraft] = useState(exam)
  const [activeQuestion, setActiveQuestion] = useState(0)
  const question = draft.questions[activeQuestion]
  const updateQuestion = (patch: Partial<Question>) => setDraft((value) => ({ ...value, questions: value.questions.map((item, index) => index === activeQuestion ? { ...item, ...patch } : item) }))
  return <section className="studio-layout"><div className="studio-main"><div className="section-heading"><div><span className="eyebrow">STEP 1 / 3 · AUTHOR</span><h2>Make the question earn its space.</h2></div><button className="secondary-button" onClick={() => onPublish(draft)}>Save draft</button></div><label className="field-wide">Exam title<input value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label><div className="question-editor"><div className="question-toolbar"><strong>Question {activeQuestion + 1}</strong><span className="muted">{question.type} · {question.points} marks</span></div><label>Prompt<textarea value={question.prompt} onChange={(event) => updateQuestion({ prompt: event.target.value })} rows={3} /></label>{question.options && <div className="option-grid">{question.options.map((option, index) => <label key={option}>Option {String.fromCharCode(65 + index)}<input value={option} onChange={(event) => updateQuestion({ options: question.options?.map((item, i) => i === index ? event.target.value : item) })} /></label>)}</div>}<div className="question-footer"><span className="muted">Answer keys stay server-side after publish.</span><button className="text-button" onClick={() => setActiveQuestion((activeQuestion + 1) % draft.questions.length)}>Next question →</button></div></div></div><aside className="studio-rail"><span className="eyebrow">QUESTION MAP</span>{draft.questions.map((item, index) => <button className={`question-map ${index === activeQuestion ? 'active' : ''}`} key={item.id} onClick={() => setActiveQuestion(index)}><span>0{index + 1}</span><span>{item.prompt}</span></button>)}<div className="rail-note"><strong>Publish gate</strong><p className="muted">Preview, validate, then publish an immutable version. Students only see published content.</p></div></aside></section>
}

function Students() { return <section className="table-panel"><div className="section-heading"><div><span className="eyebrow">LEARNERS</span><h2>Roster with fewer surprises.</h2></div><button className="primary-button">Add learner</button></div><div className="table-row table-head"><span>Name</span><span>Student ID</span><span>Access</span><span>Last activity</span></div>{[['Maya Singh', 'MAYA-014', 'Ready', 'Today, 09:42'], ['Rohan Patel', 'ROHAN-021', 'Ready', 'Yesterday'], ['Aisha Khan', 'AISHA-008', 'Invited', '—']].map((row) => <div className="table-row" key={row[1]}>{row.map((cell) => <span key={cell}>{cell}</span>)}</div>)}</section> }

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
