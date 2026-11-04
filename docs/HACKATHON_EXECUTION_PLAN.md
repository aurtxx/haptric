# OpenExam Hackathon Execution Plan

This plan follows the reality audit in `docs/HACKATHON_REALITY_AUDIT.md`. It is dependency ordered and intentionally biased toward one reliable, demo-ready vertical slice before secondary modules or visual expansion.

## Delivery target

Demonstrate, with real Django requests and a browser:

1. Staff user signs in through the React client.
2. Staff creates a draft exam, section, and three original questions.
3. Staff publishes and assigns the exam to a provisioned test student.
4. Student signs in and sees only assigned published exams.
5. Student starts one attempt, answers three questions, and reloads without losing answers.
6. Server owns the deadline and submits exactly once at expiry.
7. Server scores from private answer keys.
8. Student sees the result and staff sees the matching sanitized attempt review.

## Working rules and gates

- Keep API contracts in one manager-owned change. Frontend and backend specialists may propose changes but must not silently diverge shared names or payloads.
- Every task has exclusive file ownership. Integration changes happen only after the owning specialist reports tests and a handoff summary.
- Never send `correct_answer` to a student response or bundle. Add an explicit regression test for this before wiring the UI.
- Use synthetic local users/exams only. No EZExam or external-account changes.
- Do not claim browser QA without a reproducible browser run and viewport evidence.
- A task is not done when a button is clickable; verify persisted server state by reloading/querying it.
- Keep `docs/TASKS.md` manager-owned and update it at each milestone.

## Dependency-ordered backlog

### P0.1 — Define and implement the real API boundary

- **Owner:** Architect + Backend, with Frontend contract review.
- **Files:** `frontend/src/types.ts`, new `frontend/src/api/httpApi.ts`, `frontend/src/api/index.ts`; `backend/exams/serializers.py`, `backend/exams/urls.py`, `backend/exams/views.py`; tests under `tests/backend/` and `frontend/src/*.test.ts`.
- **Current defect:** `App.tsx` imports only `mockApi`; no typed client handles CSRF, cookies, errors, or `/me/`.
- **Expected behavior:** A small fetch client obtains CSRF, logs in/out, loads the current user, and exposes typed tenant/exam/student/question/attempt operations with `credentials: 'include'` and safe error handling.
- **Acceptance criteria:** Login survives reload; unauthenticated routes show an error/redirect; all payload types match DRF; student payloads cannot contain answer keys; network errors render a recoverable state.
- **Tests:** CSRF/login/me API test; frontend client tests for success, 401, CSRF, and validation errors; typecheck.
- **Complexity:** M.
- **Dependencies:** Existing backend session contract; no new package required.

### P0.2 — Real staff authoring and assignment workflow

- **Owner:** Backend + Frontend.
- **Files:** `frontend/src/App.tsx`, `frontend/src/api/httpApi.ts`, `frontend/src/types.ts`, new focused frontend components as needed; `backend/exams/views.py`, `backend/exams/serializers.py`, `backend/exams/models.py` only for validated gaps; `tests/backend/test_api.py`, frontend tests.
- **Current defect:** Exam Studio, roster, publish, schedule, and assignment are local/hardcoded. Student CRUD does not provision a login user.
- **Expected behavior:** Staff creates a student/profile through an explicit local-dev provisioning path, creates a draft exam/section/questions, sets schedule, publishes, and assigns to that student. All saves are server-confirmed and re-openable.
- **Acceptance criteria:** A refresh shows the persisted exam and questions; publish refuses zero questions; published question content cannot be mutated/deleted; assignment is tenant-scoped and idempotent; no real notifications are sent.
- **Tests:** API tests for provisioning, CRUD persistence, publish gate, immutable content, assignment idempotency, and cross-tenant denial; frontend form/error tests.
- **Complexity:** L.
- **Dependencies:** P0.1; resolve the student-user provisioning contract before UI work.

### P0.3 — Real student attempt, answer, and result workflow

- **Owner:** Frontend + Backend.
- **Files:** `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/api/httpApi.ts`, new attempt/results components; `backend/exams/views.py`, `backend/exams/serializers.py`; `tests/backend/test_api.py`, `tests/backend/test_scoring.py`, frontend tests.
- **Current defect:** Student preview, attempt, timer, answer persistence, score, and results are all `mockApi`/localStorage. There is no admin attempt review screen.
- **Expected behavior:** The student uses a real session, starts an assigned published exam, saves answers through `PUT/PATCH`, resumes from server state, submits or expires, and reads a sanitized result. Staff can list/retrieve organization attempts and review answers/results without exposing credentials.
- **Acceptance criteria:** No `Question.answer`/`correct_answer` reaches a student response; an answer survives reload; wrong-tenant/wrong-student access is denied; repeat submit returns the same result; admin view matches the student result.
- **Tests:** API ownership and redaction tests, answer update/reload, duplicate submit, result permissions; frontend mocked HTTP tests plus one browser E2E against local services.
- **Complexity:** L.
- **Dependencies:** P0.1 and P0.2.

### P0.4 — Make timer expiry authoritative

- **Owner:** Backend + QA/Security.
- **Files:** `backend/exams/models.py`, `backend/exams/services.py`, `backend/exams/views.py`, new expiry command/task module, migration if required; `tests/backend/test_api.py`, `tests/backend/test_scoring.py`.
- **Current defect:** An expired attempt is finalized only when answer/submit traffic arrives; concurrent start and idempotency-key edge cases are not fully constrained.
- **Expected behavior:** The server rejects late writes, finalizes an expired attempt deterministically, caps a deadline at the exam closing window, and makes submission exactly once under retries/concurrency.
- **Acceptance criteria:** Tests with controlled time prove deadline enforcement without browser clock changes; two submits return one persisted result; two starts cannot create two active attempts; late answers never alter a submitted result.
- **Tests:** Transaction/concurrency tests, schedule-cap tests, expiry finalization tests, idempotency replay tests.
- **Complexity:** L.
- **Dependencies:** P0.3; choose a supported local mechanism (request-time finalization plus a documented worker/management command) before deployment.

### P0.5 — Security hardening before demo deployment

- **Owner:** Security + Backend.
- **Files:** `backend/exam_platform/settings.py`, `backend/exams/views.py`, `backend/exams/permissions.py`, `backend/exams/serializers.py`, tests and environment examples.
- **Current defect:** Development defaults are unsafe for production; throttling, secure cookies/HSTS, strict CSRF/CORS production settings, sync payload validation, and complete audit events are not established.
- **Expected behavior:** Production configuration fails closed, authentication endpoints are rate-limited, sync is least-privilege and schema-validated, and important mutations emit sanitized audit events.
- **Acceptance criteria:** No secrets in tracked files; `DEBUG=false`/secure settings are documented; student cannot access answer keys or another tenant; security tests cover malformed sync, unauthorized logout/actions, and rate limits.
- **Tests:** Django security checks, permission matrix, serializer validation, and regression tests.
- **Complexity:** M.
- **Dependencies:** P0.1–P0.4 contracts.

### P1.1 — Offline LAN client outbox and reconnect

- **Owner:** Frontend + Backend/DevOps.
- **Files:** new `frontend/src/sync/*`, `frontend/src/storage/*`, `backend/exams/views.py`, `backend/exams/services.py`, sync tests, `infra/` docs.
- **Current defect:** The client says “saved locally” but only persists a mock attempt; no durable outbox or conflict behavior is connected to `/sync/push`/`pull`.
- **Expected behavior:** Attempt answers queue locally with idempotency keys, retry with backoff, expose sync state, and never merge conflicting answer versions silently. Server remains authoritative for scoring and submission.
- **Acceptance criteria:** Disconnect/reconnect test preserves answers, retries safely, advances a checkpoint, and reports a conflict requiring explicit resolution.
- **Tests:** Unit, integration, and browser offline/reconnect tests.
- **Complexity:** XL.
- **Dependencies:** P0.3/P0.4; documented conflict policy.

### P1.2 — PostgreSQL/Compose and CI validation

- **Owner:** DevOps + QA.
- **Files:** `infra/docker-compose.yml`, `infra/.env.example`, `infra/README.md`, CI configuration, `README.md`, `docs/DEVELOPMENT_GUIDE.md`.
- **Current defect:** Docker is not installed here; Compose and PostgreSQL startup are unverified.
- **Expected behavior:** Fresh Windows PowerShell and CI instructions run migrations, backend tests, frontend checks, and a smoke browser flow against PostgreSQL.
- **Acceptance criteria:** Compose config validates; health checks pass; migrations are reproducible; no secrets are embedded; failures are visible in CI.
- **Tests:** `docker compose config`, service health, migration/test/build pipeline.
- **Complexity:** M.
- **Dependencies:** P0.1–P0.5.

### P1.3 — Visual and accessibility review after integration

- **Owner:** Design Director + Frontend + QA.
- **Files:** `frontend/src/*`, `docs/DESIGN_SYSTEM.md`, `docs/UI_QUALITY_CHECKLIST.md`, screenshot evidence under the approved QA workflow.
- **Current defect:** Existing visual evidence covers the mock flow, not the integrated states.
- **Expected behavior:** Loading, empty, validation, network-error, offline, submitted, and staff-review states share the design system and remain keyboard/screen-reader usable.
- **Acceptance criteria:** Desktop/tablet/mobile screenshots are captured from the integrated build; defects are logged and fixed before demo freeze.
- **Tests:** Browser screenshots with viewport metadata, accessibility audit, keyboard traversal.
- **Complexity:** M.
- **Dependencies:** P0.3 and stable API states.

## Milestones and quality gates

| Milestone | Exit gate |
|---|---|
| M0 contract | API schemas, auth/session behavior, and ownership are written and tested. |
| M1 staff slice | Staff can persist/reopen a three-question draft and assign a provisioned synthetic student. |
| M2 student slice | Student can authenticate, start, answer, reload, and see only assigned content. |
| M3 timing/results | Server expiry, exactly-once scoring, student result, and admin review pass automated tests. |
| M4 LAN/cloud | Offline outbox/reconnect behavior and Compose/PostgreSQL are verified or explicitly marked unsupported. |
| Demo freeze | No P0 security/test failures; browser screenshots and a rehearsed seeded-data walkthrough exist. |

## Prompt 2 exact scope

Implement **P0.1, P0.2, and P0.3**, plus only the minimum P0.4 backend changes required to prevent accepting late answers in the demonstrated flow. The implementation must be limited to:

- a typed HTTP API adapter and real session login;
- persisted staff exam/question/student/assignment workflow;
- persisted student attempt/answer/result workflow;
- one admin attempt-review screen;
- redaction and ownership regression tests;
- a local browser walkthrough against the running Django and Vite services;
- manager-owned updates to `docs/TASKS.md` and `README.md` with actual commands/results.

Do **not** implement analytics, proctoring, communications, certificates, broad sync replication, new branding, or deployment to an external service in Prompt 2. Those remain subsequent milestones.
