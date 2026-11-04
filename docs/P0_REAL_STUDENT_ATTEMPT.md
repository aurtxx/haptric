# P0.3 — Real Student Exam Engine

**Status:** Verified locally with documented environment limits
**Branch:** `feat/p0-real-student-attempt`
**Scope:** Real student exam discovery, attempt start/resume, answer persistence, server-deadline display, expiry finalization, submission, scoring, and result restoration. LAN/cloud synchronization and broader UI redesign remain out of scope.

## State machine

The backend persists only `Attempt.status` (`in_progress` or `submitted`). Availability and terminal conditions are derived from the published exam, assignment, schedule, active student profile, and server timestamps:

`ASSIGNED -> AVAILABLE -> IN_PROGRESS -> SUBMITTED`

`NOT_YET_OPEN`, `CLOSED`, `UNASSIGNED`, and inactive-student states are rejected at start. An in-progress attempt whose `deadline_at` has passed is finalized server-side as `SUBMITTED` when it is listed, retrieved, answered, or submitted. The frontend renders these server-confirmed states and does not create a parallel attempt model.

## API contracts

- `GET /api/v1/exams/` — students receive only same-organization, published exams assigned to their student profile. Nested question payloads omit `correct_answer`, `positive_marks`, and `negative_marks`.
- `GET /api/v1/attempts/` — returns the authenticated student's attempts with status, server timestamps, saved answers, and an own-attempt result.
- `POST /api/v1/attempts/start/` — starts or resumes the assigned exam using a client idempotency key; Django supplies `started_at` and `deadline_at`.
- `PUT /api/v1/attempts/{id}/answer/` — validates question membership, ownership, deadline, and answer shape, then updates one answer per attempt/question.
- `POST /api/v1/attempts/{id}/submit/` — locks and scores the attempt on Django; repeated submissions return the same persisted result.

Answer validation supports single-choice options, unique valid multi-choice collections, and finite numeric values. Score calculation remains entirely server-side.

## Frontend behavior

The student path in `frontend/src/App.tsx` uses only the typed `httpApi` boundary. It loads assigned exams and attempts from Django, restores an in-progress or submitted attempt after refresh, sends answer saves with `Saving…`/`Saved`/error states, and renders results from the server response. The timer is display-only and computes remaining time from `deadline_at`; it never stores an authoritative deadline or score in localStorage. When the displayed countdown reaches zero, the client requests server submission; the server independently finalizes expired attempts on every relevant read/write path.

`frontend/src/api/mockApi.ts` and its mock-only test were removed. No student lifecycle dependency on `mockApi`, browser-only scoring, or localStorage persistence remains.

## Security and privacy

- Student exam discovery is assignment-, organization-, publication-, and role-scoped.
- Nested student question payloads redact answer keys and private marking fields.
- Attempt querysets expose only the authenticated student's own attempts; staff remain organization-scoped.
- Answer writes require ownership, active status, exam-question membership, valid value shape, and an unexpired in-progress attempt.
- Published attempts and results are idempotent under repeat submit; late writes cannot alter them.

## Headed browser verification

Using the headed `playwright-cli` session `p03-student` with the local synthetic account `HACK-001`:

1. Login succeeded through Django session authentication.
2. `GET /api/v1/exams/` displayed the assigned published `Hackathon Demo Exam`; the network response contained no `correct_answer`, `positive_marks`, or `negative_marks`.
3. `POST /api/v1/attempts/start/` returned a real attempt and server deadline.
4. Questions 1 and 2 were answered through two successful `PUT /answer/` requests.
5. Browser refresh restored the same attempt, both saved selections, and a reduced timer (`29:38` versus the initial `29:59`).
6. Question 3 was answered, browser refreshed again, and all three question-map entries remained answered.
7. `POST /submit/` returned the real result: score `3.00`, correct `3`, incorrect `0`, unanswered `0`.
8. A second refresh restored the submitted result from Django.

Independent Django state verification reported one attempt, three answers, one result, `submitted` status, and a populated `submitted_at`.

## Expiry verification

A separate disposable one-minute published exam was assigned locally. The headed browser started it and was left untouched until the displayed countdown naturally reached zero. The UI transitioned to the server result with score `0.00`, correct `0`, incorrect `0`, unanswered `3`, and a successful `POST /attempts/{id}/submit/`. Django independently confirmed exactly one attempt, zero answers, one result, submitted status, and a populated submission timestamp. No browser clock or production validation was modified.

## Tests and checks

- `.venv\\Scripts\\python.exe backend\\manage.py check` — PASS.
- `.venv\\Scripts\\python.exe -m pytest -q tests/backend tests/qa` — **22 passed, 4 skipped** (QA skips require the optional contract service).
- `npm run lint` in `frontend` — PASS.
- `npm run test -- --run` in `frontend` — **2 files, 12 tests passed**.
- `npm run build` in `frontend` — PASS.
- `git diff --check` — required before commit.

## Remaining limitations

Docker/PostgreSQL and environment-backed QA remain unavailable in this workspace. The current expiry strategy is request/read plus browser deadline handling; a production deployment should add an operational scheduler/worker and clock-drift telemetry. LAN/cloud sync, offline outboxes, conflict resolution, and staff attempt-review UI are intentionally deferred.
