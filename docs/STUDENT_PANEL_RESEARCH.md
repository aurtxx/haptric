# EZExam student panel research

## Scope and status

Read-only student-panel inspection and one approved disposable student creation were performed in the authorized Super Admin session. No student login was attempted and no credentials were entered or recorded.

## Confirmed observations

| Area | Route/state | Observation | Evidence | Confidence |
|---|---|---|---|---|
| Student directory | `/staff#` | Table exposes Name, Student ID and Student Tags with search fields, page-size selector, Delete Students and Download Students controls. | `.playwright-cli/page-2026-11-03T19-56-29-527Z.yml` | CONFIRMED |
| Add Student form | `/staff#` | Fields include Name, Student ID, Student Tags, optional phone, optional email, optional password and Login Active. | `.playwright-cli/page-2026-11-03T19-56-36-201Z.yml` | CONFIRMED |
| Validation | `/staff#` | Name and ID accept only alphanumeric values; at least one existing Student Tag is required. | `.playwright-cli/page-2026-11-03T19-56-58-031Z.yml`, `.playwright-cli/page-2026-11-03T19-58-01-863Z.yml` | CONFIRMED |
| Disposable student | `/staff#` | `TESTONLYStudent20261104` with ID `TESTONLY20261104` was added successfully using the existing `JEE-Main` tag. | `.playwright-cli/page-2026-11-03T19-58-13-840Z.yml` | CONFIRMED |
| Reopened student | `/staff#` | Clicking the saved student reopened Edit Student with the same name, ID, JEE-Main tag and Login Active checked. | `.playwright-cli/page-2026-11-03T20-03-40-726Z.yml` | CONFIRMED persistence |

## Not performed / not verified

- No email, phone, password, OTP, cookie or token was entered or recorded for the disposable student.
- No student login route was opened.
- Student dashboard, exam availability, instructions, timer, navigation, answer persistence and results are NOT VERIFIED.
- No exam assignment or notification was made.

## Verification status

Student creation: **PASS**. ID/name validation: **PASS after correcting invalid punctuation**. Tag selection: **PASS**; reopened edit state shows JEE-Main. Login credentials: **NOT VERIFIED** because no password/email/phone was created or handled.

## User-opened student-facing window (target identity unverified)

At 2026-11-03 20:08 UTC, a separate headed tab was already open at `/online-exams/60635` with title `Online Exam - Ezexamqwertyuiop`. The visible page showed `Check Demo Exam`, a timer around 59 minutes, Maths/Physics/Chemistry sections, a Maths section labeled 5 questions and maximum marks 15, one-correct-option instructions with 3 marks correct and -1 incorrect, question navigation, Question Paper, Instructions and Submit Exam controls. No question was answered, navigation control clicked, submission opened, or record changed. This is **CONFIRMED UI only** and is **NOT VERIFIED** as the approved TEST-ONLY exam or as the designated student account's view.

### Additional read-only observations — 2026-11-03 20:12–20:13 UTC

The same visible window was inspected without entering answers. The Instructions modal stated that Save & Next persists an answer, Mark for Review & Next marks it, Finish Exam submits, pausing is unavailable, and Instructions can be revisited. The modal summarized 15 questions, 60 minutes, and 55 marks. The Full Question Paper modal showed headings 1–15. Section navigation confirmed Physics uses one-or-more-correct options and Chemistry uses numerical-value entry; no question content was copied. Opening the Finish Exam modal displayed an irreversible-action warning; Submit Answers was not selected. These are **CONFIRMED UI observations** only; authentication identity, server persistence, timer expiry, autosubmit, and results remain **NOT VERIFIED**.

## Product implications

The independent platform should make student identity requirements explicit, support a credential-free LAN enrollment handoff, and show enrollment/assignment state without exposing unrelated student data. These are proposed requirements, not vendor behavior.

