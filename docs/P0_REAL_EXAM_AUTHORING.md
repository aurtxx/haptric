# P0.2 — Real Admin Exam Authoring + Student Provisioning

**Status:** Verified locally with documented boundaries
**Branch:** `feat/p0-real-exam-authoring`
**Scope:** Real Django-backed admin provisioning, exam authoring, publishing, and assignment. Student attempt-taking remains the P0.3 boundary.

## Architecture

The admin workflow now uses the typed client in `frontend/src/api/httpApi.ts` for all mutations. React no longer saves the admin roster or exam draft to local state or `mockApi`. Django remains the source of truth, with organization scoping enforced in viewsets and serializers.

Student provisioning is an explicit `POST /api/v1/students/provision/` action. The request is validated, then a `User(role=student)` and linked `Student` profile are created inside one database transaction. Django hashes the temporary credential with `set_password`; the response contains no password or credential material. Duplicate login IDs, duplicate organization-scoped student IDs, tenant mismatches, and failed linked-record creation are rejected or rolled back.

## API contracts used

- `GET /api/v1/students/` — list the authenticated staff member's organization students.
- `POST /api/v1/students/provision/` — provision a linked student login and profile.
- `GET /api/v1/exams/` — list persisted organization exams with sections and linked questions.
- `POST /api/v1/exams/` — create a draft exam with title, duration, and optional schedule.
- `GET /api/v1/exams/{id}/` — reopen a persisted exam.
- `POST /api/v1/sections/` — create a draft section for an organization exam.
- `POST /api/v1/questions/` — create a staff-only question-bank question.
- `POST /api/v1/exam-questions/` — attach a question to a section at an explicit position.
- `POST /api/v1/exams/{id}/publish/` — publish only an exam with at least one linked question.
- `POST /api/v1/exams/{id}/assign/` — assign a published exam to a same-organization student; duplicate assignment is idempotent and returns the existing assignment with HTTP 200.

All unsafe requests use the existing CSRF/session boundary. Correct answers are available only to staff serializers; student-facing question responses redact `correct_answer` and related scoring data.

## Authoring lifecycle

1. Admin loads students and exams from Django.
2. Admin provisions a student with name, student ID, and a temporary password. The browser clears the password field after a confirmed response.
3. Admin creates a draft exam, one section, and exactly three original single-choice questions. The client waits for each server response before creating the next relationship.
4. The UI re-fetches exams and displays the server-confirmed section/question count.
5. Publish is a server action. The UI changes to `published` only after Django confirms it.
6. Assignment is a server action against the selected student. Duplicate requests do not create duplicate `ExamAssignment` rows.
7. Reloading the browser re-fetches the student and exam records from Django; no localStorage exam state is used for this admin flow.

## Integrity rules

- Draft exams accept section and question-link changes.
- Published exams reject exam, section, and exam-question mutations and deletion.
- Questions linked to a published exam cannot be edited or deleted, preventing answer-key mutation after publication.
- Publishing an exam with zero linked questions is rejected.
- Assignment requires a published exam and a student in the same organization.
- Provisioning and assignment are organization-scoped and protected by staff permissions.

## Browser acceptance evidence

Using the headed `playwright-cli` session `p02-auth` against local Django + Vite:

- Logged in with a synthetic local admin through Django session auth.
- Provisioned `Hackathon Student` with ID `HACK-001`; the UI displayed a server-confirmed success state.
- Reloaded the browser and confirmed the student was fetched from Django.
- Created `Hackathon Demo Exam`, `Demo Section`, and exactly three synthetic questions.
- Reloaded and reopened the exam; the UI displayed `3 linked questions` and the persisted 30-minute duration.
- Published the exam; the UI displayed the server-confirmed `published` state.
- Assigned the exam to `HACK-001`; the UI displayed the server-confirmed assignment state.
- A second-source Django shell query confirmed one linked student, one section, three question links, published status, and one assignment row.

No student login, exam start, answer submission, timer test, result review, or offline synchronization was performed.

## Tests and checks

- `.venv\\Scripts\\python.exe backend\\manage.py check` — PASS.
- `.venv\\Scripts\\python.exe -m pytest -q tests/backend tests/qa` — backend/QA results recorded with the final verification run; QA environment skips remain documented.
- `npm run lint` in `frontend` — PASS.
- `npm run test -- --run` in `frontend` — PASS; final test count recorded in the delivery report.
- `npm run build` in `frontend` — PASS.
- `git diff --check` — required before commit.

## Remaining mock boundaries and limitations

`frontend/src/api/mockApi.ts` remains intentionally used for the student attempt screen, local answer state, timer demo, and mock result view. P0.3 must replace those paths with real attempt/answer/result APIs. Docker/PostgreSQL-backed verification and environment QA checks remain dependent on local tooling. No application deployment was performed.

## Windows PowerShell startup

From the repository root:

```powershell
.venv\\Scripts\\python.exe backend\\manage.py migrate
.venv\\Scripts\\python.exe backend\\manage.py runserver 127.0.0.1:8000
```

In a second PowerShell window:

```powershell
Set-Location frontend
npm run dev -- --host 127.0.0.1
```

Use disposable local credentials only. Never commit passwords, tokens, cookies, `.env` files, local databases, or browser artifacts.
