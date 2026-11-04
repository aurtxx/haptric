# OpenExam Hackathon Reality Audit

**Audit date:** 2026-11-04
**Scope:** source, tests, local HTTP smoke checks, and repository configuration only
**Change policy:** no application code was changed for this audit. Only this audit document and `docs/HACKATHON_EXECUTION_PLAN.md` are being added.

## Executive finding

OpenExam has a useful Django/DRF domain foundation and a polished local React demonstration, but it is not yet an integrated full-stack product. The frontend imports `frontend/src/api/mockApi.ts` directly; it does not call the Django API or perform real authentication. The backend implements many lifecycle primitives and has passing API tests, but several server guarantees required for a production exam flow are incomplete. The admin-to-student journey therefore stops at the frontend/backend boundary.

The highest-value next step is a narrow, real API-backed vertical slice: session login, staff-created draft exam with three questions, assignment, student login, attempt start, answer saves, server-enforced expiry/submission, scoring, and result views. Visual expansion and secondary modules should wait until that slice is demonstrated end to end.

## Evidence sources inspected

- `AGENTS.md`, `README.md`, `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, and `docs/OVERNIGHT_PROGRESS.md`.
- Frontend: `frontend/src/App.tsx`, `frontend/src/api/mockApi.ts`, `frontend/src/types.ts`, `frontend/src/App.test.ts`, Vite/package configuration.
- Backend: `backend/exams/models.py`, `views.py`, `serializers.py`, `services.py`, `permissions.py`, `urls.py`, `backend/exam_platform/settings.py`, migrations, tests, and `infra/docker-compose.yml`.
- Existing research and visual evidence were treated as context, not proof of backend/frontend integration.

## Reality matrix

| Capability | Reality | Evidence and boundary |
|---|---|---|
| Authentication | **Backend-only; frontend mocked** | Django session login, logout, CSRF, and `/me/` exist in `backend/exams/views.py` and are covered by API tests. `App.tsx` ignores entered credentials and selects a demo role locally. |
| Roles | **Backend authorization exists; UI role preview only** | `IsOrgStaff`, `IsStudent`, and `IsOrgMember` filter API access. The React role is a local `admin`/`student` state set by preview buttons. |
| Tenant isolation | **Backend implemented and partly tested** | Scoped querysets use `request.user.organization_id`; tests cover cross-tenant visibility. No real frontend session establishes or displays tenant data. |
| Organization/user provisioning | **Incomplete** | Organization and user viewsets are read-only. A `Student` can be created without provisioning/linking a login `User`, so a newly created student cannot necessarily authenticate. |
| Exam creation | **Backend CRUD; frontend local draft** | Staff API serializers/viewsets and publish gate exist. Exam Studio edits React state and “Save draft” only reports a local save. |
| Question authoring | **Backend CRUD; frontend mock editor** | Questions, sections, and exam-question links exist server-side. The client edits hardcoded questions and never sends them to Django. |
| Scheduling | **Backend fields and early/late start guards** | `available_from`/`available_until` and schedule rejection are present and tested. No schedule controls exist in the React flow. |
| Assignment | **Backend endpoint; UI absent** | Published exams can be assigned to an organization-scoped student. The roster is hardcoded and “Add learner” has no handler. |
| Student login | **Backend primitive; not integrated** | Session auth supports any properly provisioned user. The client login form always enters the admin role; student preview is not authentication. |
| Attempt start | **Backend endpoint; client mock** | Backend checks published status, assignment, active window, and student ownership. React creates a local attempt in `mockApi`. |
| Answer persistence | **Backend transaction path; client localStorage** | DRF `answer` uses `update_or_create` and validates exam-question membership. The client writes to browser localStorage and does not call the endpoint. |
| Timer | **Model/deadline checks, not a complete server timer** | Backend stores `deadline_at` and closes an expired attempt when an answer request reaches it. There is no worker/read-time finalization that guarantees submission at the deadline. React uses a browser interval and calls the mock submit function. |
| Auto-submit | **Incomplete** | No background scheduler or server-authoritative expiry job is configured. A silent/offline browser can miss the deadline until another request arrives. |
| Scoring | **Backend service; frontend mock scoring** | `submit_attempt` scores from server-side answer keys in a transaction and persists `Result`. `mockApi.submitAttempt` scores from answer keys bundled in the browser. |
| Results | **Backend embedded result; UI student-only mock** | Attempt serialization includes a result. There is no standalone results endpoint or admin attempt-review screen in the React app. |
| Audit trail | **Partial** | Publish, assignment, and submission create audit events. Answer saves, student/question changes, and exam creation are not consistently audited. |
| LAN/cloud synchronization | **Primitives only** | `SyncOutbox`, bounded pull, idempotency-key push, and collision checks exist. No durable client outbox, retry worker, cursor/checkpoint UI, conflict workflow, or end-to-end offline test is integrated. |
| Deployment | **Configuration only** | SQLite fallback and PostgreSQL URL parsing work in code; Compose documents the intended topology. Docker/Compose is unavailable in this environment, so container startup is unverified. |
| Accessibility/visual quality | **Local UI evidence only** | Existing local browser screenshots and frontend checks show the demo renders; they do not prove API behavior, responsive parity after integration, or a production accessibility review. |

## End-to-end journey trace

| Journey step | Actual path | Result |
|---|---|---|
| 1. Admin login | React form submit → `onSelect('admin')`; no request | **BREAKS at integration boundary.** Backend login exists separately. |
| 2. Create exam | Exam Studio mutates `draft` state | **Frontend-only.** No `POST /api/.../exams`. Reload loses the draft. |
| 3. Add three questions | Local hardcoded questions are edited | **Frontend-only.** Server question/section records are untouched. |
| 4. Publish/schedule | No publish, schedule, or assignment action in UI | **NOT IMPLEMENTED in the client.** Backend publish/assign endpoints exist with guards. |
| 5. Assign student | Hardcoded roster; Add learner has no handler | **NOT IMPLEMENTED in the client.** Backend assignment endpoint exists. |
| 6. Student login | Preview button sets role | **BREAKS at authentication.** No student credentials reach Django. |
| 7. Start attempt | `mockApi.createAttempt()` creates a browser-local object | **Mocked.** Backend `/attempts/start/` is not called. |
| 8. Save answers | `mockApi.saveAnswer()` writes localStorage | **Mocked.** Backend validation, transaction, and tenant checks are bypassed. |
| 9. Timer expiry | React `setInterval` reaches zero and calls mock submit | **Client-only.** Server does not proactively submit at the deadline. |
| 10. Submit and score | Mock API compares browser-shipped answer keys | **Mocked and security-inappropriate for production.** Backend scorer is not invoked. |
| 11. Student result | React renders mock score and recorded/unanswered states | **Frontend-only.** No API result retrieval. |
| 12. Admin result review | No admin attempt/results screen | **NOT IMPLEMENTED.** Backend attempt read data exists but has no dedicated admin UI contract. |

## Backend strengths verified in source and tests

- Custom user, organization, student, subject, question, exam, section, assignment, attempt, answer, result, audit, and sync-outbox models.
- Organization-scoped querysets and role permissions.
- Published exams require at least one linked question.
- Published exam question create/update is blocked to preserve immutable content; deletion behavior still needs a dedicated policy/test.
- Student exam serialization removes `correct_answer`.
- Start checks schedule, publication, assignment, and active student profile.
- Answer writes are unique per attempt/question and are transaction-safe at the database operation level.
- Submission locks the attempt, calculates marks, persists a result, emits audit/outbox events, and is idempotent for repeated submissions.
- Sync push requires an idempotency key and rejects a cross-organization collision.

## Backend gaps and risks

1. **Student account provisioning:** Student CRUD does not create or link a login user. The real flow needs an explicit, secure invitation/provisioning contract.
2. **Server-authoritative expiry:** `deadline_at` is checked only when answer/submit traffic arrives; no scheduler or deterministic read-time finalizer guarantees closure at the deadline.
3. **Attempt concurrency:** active-attempt lookup and create are not protected by a uniqueness rule/lock for one active attempt per student/exam. Start idempotency-key reuse can surface a database uniqueness error.
4. **Schedule cap:** attempt deadline is `started_at + duration`; it is not capped to `available_until`.
5. **Validation boundary:** `Exam.clean()` is not automatically called by every `save`, and serializers do not fully enforce duration/schedule invariants.
6. **Published content deletion:** question-link deletion needs the same immutable-published guard as create/update.
7. **Numeric scoring:** normalization is string-based; equivalent numeric representations may compare unexpectedly.
8. **Sync trust boundary:** any organization member can push largely unvalidated envelopes; conflict resolution and authoritative entity application are not implemented.
9. **Result API shape:** results are embedded in attempts; a stable, permissioned result/attempt-review endpoint is still needed for the UI.
10. **Production security defaults:** development secret/debug defaults, no visible throttling/rate-limit policy, and incomplete secure-cookie/HSTS/CSRF-origin production settings require hardening before deployment.
11. **Audit completeness:** important CRUD and answer events are not consistently recorded.
12. **Logout method policy:** logout lacks the explicit CSRF/method treatment used by login.

## Frontend gaps and risks

- `Question.answer` is part of the client type and hardcoded mock data. Real answer keys must never be delivered to a student bundle.
- Login, role switching, exam creation, roster, assignment, schedule, attempts, and results are all local UI state or hardcoded content.
- App startup does not hydrate an attempt into the Results route; local persistence is only consulted when starting the mock exam.
- Client mock methods do not enforce server deadlines, transactionality, or concurrent-submit semantics.
- There are no component, API integration, offline reconnect, accessibility, or browser E2E tests in the active frontend test configuration.
- External Google Fonts are imported from CSS, which is not reliable for an isolated LAN deployment.

## Verification record

All commands below were run from the repository in this audit. Exit code `0` means the command completed successfully.

| Check | Command | Result |
|---|---|---|
| Git state | `git status --short` | Clean before audit-document edits. |
| Django system check | `.venv\\Scripts\\python.exe backend\\manage.py check` | PASS, exit `0`; “no issues”. |
| Migration plan | `.venv\\Scripts\\python.exe backend\\manage.py migrate --plan` | PASS, exit `0`; no pending operations. |
| Backend/QA tests | `.venv\\Scripts\\python.exe -m pytest -q tests/backend tests/qa` | PASS, exit `0`; **8 passed, 4 skipped**. The skips are environment-backed contract checks without `QA_API_BASE_URL`. |
| Frontend typecheck/lint | `npm run lint` in `frontend` | PASS, exit `0` (`tsc --noEmit`). |
| Frontend tests | `npm run test -- --run` in `frontend` | PASS, exit `0`; **1 file, 2 tests passed**. These cover mock deadline/scoring/replay behavior, not API integration. |
| Frontend production build | `npm run build` in `frontend` | PASS, exit `0`; Vite emitted `frontend/dist`. |
| Backend HTTP smoke | Runserver then `Invoke-WebRequest` to `/health/` and `/api/v1/health/` | PASS; both returned HTTP `200` and `{"status":"ok","service":"exam-platform-api"}`. |
| Frontend HTTP smoke | Vite dev server at `http://127.0.0.1:5175/` (5173/5174 already occupied) | PASS; HTTP `200`, 672-byte HTML response. Existing listeners were not modified. |
| Docker/Compose | `docker --version`; `docker compose version` | **UNAVAILABLE**; Docker is not installed/on PATH. No installation was attempted. |

## Documentation drift found

`docs/TASKS.md` still contains an older verification footer claiming that no application manifest exists and that no commit was made. The repository now has a frontend/backend manifest, passing local checks, and commits `73e8a92` and `bbb97e4`. This is not an application defect, but it can mislead future agents and should be reconciled during the next manager-owned board update.

## Critical blockers

1. No real frontend-to-Django API adapter or authenticated session flow.
2. No student account provisioning contract.
3. No server-guaranteed timer expiry/auto-submit mechanism.
4. No integrated admin assignment/results workflow.
5. Mock answer keys are shipped to the browser.
6. LAN/offline sync is documented and partially modeled, not demonstrated.
7. Docker/PostgreSQL and integrated browser E2E are unverified in this environment.

## Top five implementation priorities

1. Build the typed API client and real session-auth bootstrap; remove role-preview login from the primary path.
2. Integrate staff exam/question/assignment creation and student provisioning with the existing DRF contract.
3. Integrate student attempt start, answer saves, server result retrieval, and admin attempt review without exposing answer keys.
4. Make expiry authoritative and test exactly-once submission under expiry, retries, and concurrent requests.
5. Add offline outbox/reconnect behavior, Compose/PostgreSQL validation, and a browser-backed end-to-end test of the vertical slice.

## Prompt 2 boundary

Prompt 2 should implement only the first three priorities as one thin vertical slice, plus the minimum backend fixes needed to make its acceptance criteria true. It should not add analytics, proctoring, communications, certificates, new visual themes, or broad synchronization features. The exact task contracts, files, dependencies, tests, and gates are in `docs/HACKATHON_EXECUTION_PLAN.md`.
