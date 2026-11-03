# Research session log

Copy this template for an approved session. Never record passwords, OTPs, tokens, cookies, storage state, account IDs, private names, or unrelated personal data.

## EZExam login handoff — 2026-11-04 Asia/Calcutta

- Session ID/name: `product-research`
- Date/time and timezone: 2026-11-04 00:23 Asia/Calcutta (2026-11-03 18:53 UTC)
- Research owner: manager
- Website origin: `https://ezexamqwertyuiop.ezexam.in`
- User-provided objective: manual login handoff, followed by authorized read-only dashboard and password-recovery interface research after confirmation
- Authorized scope confirmed by user: visible login-page navigation explicitly requested; broader vendor authorization remains user-reported and not independently verified
- Manual login confirmation received: no
- Browser/channel and headed status: Playwright CLI default Chromium, headed, persistent
- Playwright CLI version: 0.1.23
- Research status: paused at login handoff
- Evidence: CLI generated an automatic login-page snapshot and console log under ignored `.playwright-cli/`; neither was inspected or copied into the session record
- Boundaries: no form submission, no credential/OTP handling, no dashboard inspection, no recovery request, and no other live interaction performed

**Handoff:** The visible browser is open at the requested login page. User must log in manually and confirm completion in chat. Do not send credentials, OTPs, or other secrets. Continue only after explicit confirmation and within the approved scope.

### Login confirmed and dashboard overview — 2026-11-04 Asia/Calcutta

- User confirmed manual login in chat; no credentials were received.
- Read-only snapshot route: `/staff`; page title indicated the product home/dashboard. This verifies an authenticated dashboard view in the named browser session.
- Visible navigation labels/categories: Exams, Students, Settings, Payments & Plans, Customize Site, Demo Videos, More, and Logout.
- Dashboard areas visible: online/OMR exam actions and list, student/faculty entry points, customization/settings, exam/usage reports, FAQs, and an onboarding tour.
- The UI displays the role label `Super Admin`; the user confirmed this is expected for the assigned admin test account. No privileged feature was opened.
- No records were created, edited, or deleted. No screenshot was captured. The CLI snapshot contains account-specific dashboard content under ignored `.playwright-cli/`; it is not attached or copied into this log.
- The user later confirmed that the displayed admin role is expected and explicitly approved logout. The dashboard onboarding overlay intercepted clicks; Escape did not dismiss it. The visible `Skip` control was used without selecting the “Don't Show Again” checkbox, then the logout confirmation was accepted. Browser returned to `/login`.
- On the login page, a `Phone / Email / Student ID` field, password field, and `Forgot Password` link were visible. The recovery panel showed an `Email / Phone Number` field, Student/Admin options (Admin selected for inspection), `Get OTP`, and `Back to Login`. No OTP input or password confirmation fields were visible before an OTP request.
- At the first recovery-panel inspection, `Get OTP` had not been clicked and no request had been made. In a later continuation, Admin remained selected and the user-provided test email was entered in the visible field; its value is omitted here.
- The user subsequently reported clicking `Get OTP` once. At 2026-11-04 00:42 Asia/Calcutta (2026-11-03 19:12 UTC), a sanitized read of visible page text showed an OTP-sent notice. Delivery was not independently verified; no email address or OTP was recorded.
- Visible controls after the request: four number-type inputs without accessible labels (OTP interpretation not independently confirmed), password inputs labeled `New Password` and `Repeat Password`, and `SET PASSWORD`, `Cancel`, and `Resend OTP` controls. All fields were empty at inspection. No code was viewed or entered; no resend, incorrect attempt, or password reset occurred. No screenshot was captured.
- Research status: paused on the logged-out recovery form. Written scope is still unverified and the testing window, source IP, and vendor limits remain unspecified. No other tenant was visited; `davjsg.ezexam.in` remains out of scope.

### Login re-entry checkpoint — 2026-11-04

- Existing headed `product-research` session is on the approved `/login` route.
- Sanitized visible-form metadata: username field empty; password field non-empty. No field values were inspected or recorded.
- Login was not clicked. User must complete or verify the form manually and explicitly confirm before the agent clicks Login.

### Authenticated feature inventory — 2026-11-03 19:39–19:43 UTC

- User confirmed manual login. The headed session reached `/staff#` and displayed the expected `Super Admin` role.
- Read-only navigation covered Exams, Students, Settings, Payments & Plans, Customize Site, Demo Videos, More → Faculty/Centres/Notices, exam detail tabs, report forms, and new online/OMR exam forms.
- Evidence snapshots remain under ignored `.playwright-cli/` and may contain account-specific content. No screenshots were captured or shared.
- Confirmed observations and evidence paths are summarized in [COMPETITOR_RESEARCH.md](COMPETITOR_RESEARCH.md). Product recommendations and architecture proposals in the new research documents are explicitly marked as proposed or inferred.
- No record creation, editing, deletion, publishing, report generation, export, payment, message, exam launch, file upload, or settings change was performed.
- Not observed in this session: attendance, certificates, dedicated question bank, separate batch/course pages, student exam-taking flow, live proctoring workflow, sync/LAN controls, backup/restore, API administration, audit logs, and mobile layouts.
- Final handoff status: the named headed `product-research` session was rechecked at 2026-11-03 19:44 UTC and remained on the authorized `/staff#` route. It is still authenticated and open for the user's review; no logout or further mutation was performed.

### Exam workflow creation checkpoint — 2026-11-03 19:51 UTC

- The authenticated `product-research` session was preserved on the authorized `/staff#` route.
- The online-exam creation panel was inspected without entering values or advancing: Step 1 shows `Exam Name`, `Exam Duration` in minutes, and `Next`.
- No exam name, duration, questions, schedule, sharing, publication, student assignment, notification, or other mutation was performed.
- Evidence: `.playwright-cli/page-2026-11-03T19-51-16-265Z.yml` (ignored browser artifact; not copied into project documentation).
- Status: paused pending explicit user approval to create a clearly labeled disposable test exam and, separately, a disposable test student.

### Approved disposable records checkpoint — 2026-11-03 19:51–19:58 UTC

- User approved creation of one clearly labeled disposable online exam and one disposable student, while separately prohibiting scheduling, publishing, assignment, notifications, start, submit and delete actions.
- Historical draft flow: `TEST-ONLY Browser Research 20261104`, minimum accepted duration 10 minutes. Three synthetic single-correct questions were entered with positive marking 1 and negative marking 0. The UI opened a blank fourth-question editor after the third save; later reopening did not match this flow, so persistence is now marked FAIL/NOT VERIFIED.
- Timing/share settings were inspected. The Save action was not clicked; no access window, sharing, exam link or advanced-option change was saved.
- Student creation required an existing Student Tag. `TESTONLYStudent20261104` / `TESTONLY20261104` was added successfully with the existing `JEE-Main` tag. No email, phone, password, OTP, cookie or token was entered or recorded.
- Evidence snapshots: `.playwright-cli/page-2026-11-03T19-55-26-390Z.yml`, `.playwright-cli/page-2026-11-03T19-55-41-433Z.yml`, `.playwright-cli/page-2026-11-03T19-56-36-201Z.yml`, `.playwright-cli/page-2026-11-03T19-58-13-840Z.yml`.
- Current status: paused before scheduling/sharing/assignment and before any student browser login or exam attempt.

### Persistence verification retry — 2026-11-03 20:03–20:05 UTC

- Student row search found `TESTONLYStudent20261104` / `TESTONLY20261104` with JEE-Main. Reopening the row displayed Edit Student with the same fields, tag and Login Active checked. Student persistence is PASS; credentials remain unverified and were not handled.
- Returning to Exams and searching the named exam found one row with duration 10, an exam ID displayed by the UI, a JEE-Main tag, and a past From/To window. The named row reopened successfully.
- Reopened exam detail showed Questions (15), an existing image-backed question, marking 3 / -1, and a different Verify Questions reference. This does not match the three synthetic questions entered in the prior draft flow. The intended exam creation/persistence result is therefore FAIL/NOT VERIFIED, not success.
- No Save, schedule correction, assignment change, exam link, notification, publish, start, submit or delete action was performed in this retry.
- Research is blocked pending user direction on whether this same-name 15-question record is the intended test record and whether correction/deletion of its questions is authorized. Do not create a replacement identifier without approval.

### User-opened student-facing window — 2026-11-03 20:08 UTC

- A third headed tab was already open at `/online-exams/60635`, titled `Online Exam - Ezexamqwertyuiop`, showing `Check Demo Exam`, a timer around 59 minutes, Maths/Physics/Chemistry sections, a 5-question Maths section, 3/-1 marking text, question navigation and Submit Exam controls.
- No answer, submit, question-paper/instructions modal, clock change, or destructive action was performed. The tab is not verified as the named TEST-ONLY exam or the designated student account view.

### Read-only inspection of `/online-exams/60635` — 2026-11-03 20:12–20:13 UTC

- Reused the visible `product-research` Playwright session and selected the exact user-provided URL. No answers, save/next actions, review markers, submission, record edits, or deletion were performed.
- Confirmed the visible exam header is `Check Demo Exam`; the timer decreased naturally from approximately `00:56:22` to `00:55:18` during inspection. Identity as the approved TEST-ONLY exam remains **NOT VERIFIED**.
- Opened and closed the read-only Instructions modal. It states: Save & Next saves an answer and advances; Mark for Review & Next marks a question; Finish Exam submits; the test cannot be paused; Instructions can be reopened. The modal summary states `15 Questions • 60 Minutes • 55 Marks`.
- Opened and closed the read-only Full Question Paper modal. It displayed question headings 1 through 15; no bulk question text or protected assets were copied.
- Read-only section navigation showed: Maths — 5 questions, maximum 15 marks, one correct option, +3/-1; Physics — 5 questions, maximum 20 marks, one or more correct options with all/only-correct scoring text; Chemistry — 5 questions, maximum 20 marks, numerical-value input with +4/0 scoring.
- Opened and closed the read-only Overview Legend and Finish Exam confirmation modal. The latter explicitly warned `This can't be undone!`; the `Submit Answers` action was not clicked.
- Resized the visible page to 390×844 and restored 1280×800. The same core controls remained visible in snapshots; no answer state changed. This is structural evidence only, not a full visual accessibility audit.
- Playwright reported a console error/warning during the session; it was not investigated because doing so could expose implementation details outside the approved read-only research objective.

### Deep exam UI and frontend metadata inspection — 2026-11-03 20:19–20:21 UTC

- Read-only navigation visited all 15 positions: Maths 1–5, Physics 1–5 and Chemistry 1–5. Question text, images and answer keys were intentionally not recorded.
- Maths positions exposed four single-choice affordances, +3/−1 scoring and Save & Next/Mark for Review & Next. Physics positions exposed four multi-correct affordances and its all/only-correct scoring guidance. Chemistry positions exposed numerical-value entry with an on-screen numpad; Q5 displayed Save & Finish. **CONFIRMED UI; answer persistence NOT VERIFIED.**
- Section switching and question-number navigation changed the visible position and counters without entering answers. Chemistry numpad open/close was repeated safely with no value entered. **CONFIRMED.**
- Keyboard-only Tab traversal reached visible navigation/modal links. Full focus order and assistive-technology semantics remain **NOT VERIFIED**.
- Sanitized performance metadata reported resource initiator counts script=6, link=3, fetch=2 and XMLHttpRequest=14 at the inspection point. Public script/style filenames and runtime globals indicated jQuery 3.2.1; no bundles were downloaded or inspected. Framework conclusion is **INFERRED**, not definitive.
- No answer submission, exam reset, deletion, credential handling, source extraction or hidden-endpoint probing occurred.

## Session

- Session ID/name:
- Date/time and timezone:
- Research owner:
- Website origin:
- User-provided objective:
- Authorized scope confirmed by user: yes / no
- Manual login confirmation received: yes / no / not applicable
- Browser/channel and headed status:
- Playwright CLI version:
- Research status: planned / in progress / complete / blocked

## Boundaries

- Approved pages/features:
- Excluded pages/features:
- Allowed actions: read-only / explicitly approved reversible test data
- Prohibited actions:
- Data handling and redaction plan:

## Evidence index

| ID | Route or feature | Step / observation | Expected | Actual | Evidence path | Sensitive material removed | Status |
|---|---|---|---|---|---|---|---|
| R-001 |  |  |  |  | `.playwright-cli/research/` |  |  |

## Handoff

- Product findings:
- Architecture implications:
- Design implications:
- Accessibility or UX observations:
- Risks and blockers:
- Untested areas:
- Recommended next step:
