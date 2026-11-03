# QA and security verification plan

This plan is for the independent examination platform. It is a defensive, non-destructive acceptance plan; it does not authorize testing EZExam or any external service.

## Gates

1. Run unit tests and migrations before integration tests.
2. Use a disposable local tenant and synthetic users/questions only.
3. Keep admin and student sessions separate; never place credentials, cookies or bearer tokens in fixtures or logs.
4. Run browser tests only against an explicitly configured local URL (`QA_API_BASE_URL`/`QA_WEB_BASE_URL`).
5. Block release on cross-tenant data, privilege escalation, answer-key exposure, timer bypass, duplicate submission, secret leakage or destructive default behavior.

## Acceptance matrix

| Area | Verification | Expected result | Status |
|---|---|---|---|
| Tenant isolation | Organization A user requests Organization B student/exam/attempt IDs | 404 or 403 with no body leakage | NOT VERIFIED until backend is runnable |
| Role boundaries | Student calls admin endpoints; teacher calls owner/billing endpoints | 403/404; no mutation | NOT VERIFIED |
| Authentication | Login, session expiry, logout and CSRF behavior on local app | Secure session lifecycle; no token in URL/logs | NOT VERIFIED |
| Question persistence | Create three synthetic questions, reopen and compare stable IDs/version | Exact count/content/type persists | NOT VERIFIED |
| Scheduling | Assignment outside access window and to wrong tenant | Rejected server-side | NOT VERIFIED |
| Answer persistence | Save/reload an answer in a disposable attempt | Latest authorized answer survives reload and reconnect | NOT VERIFIED |
| Timer authority | Attempt uses server-issued deadline; client clock changes do not extend time | Expiry enforced by server | NOT VERIFIED |
| Auto-submit | Repeated expiry/submission calls for one attempt | One immutable submission receipt | NOT VERIFIED |
| Scoring | Single-choice, multi-correct and numerical synthetic fixtures | Marks match versioned rubric | NOT VERIFIED |
| Sync idempotency | Replay same outbox event and reorder events | One effect per idempotency key; conflict recorded | NOT VERIFIED |
| Audit | Create, publish, assign, answer, submit and result-release events | Tenant-scoped actor/action/time/object, no secrets | NOT VERIFIED |
| Secrets | Scan logs, fixtures, HTML and API errors | No passwords, OTPs, cookies, tokens, private keys or answer keys | NOT VERIFIED |
| Browser UX | Desktop/tablet/mobile screenshots, keyboard and reduced motion | Required controls usable and focus-visible | NOT VERIFIED |

## Security review checklist

- [ ] Every query is scoped by authenticated organization/tenant.
- [ ] Object-level permissions are enforced server-side, not only by route guards.
- [ ] Student responses cannot request answer keys or unpublished question versions.
- [ ] Exam versions become immutable at publish time; attempts pin an exact version.
- [ ] Submission endpoint accepts an idempotency key and rejects a second conflicting finalization.
- [ ] Deadline checks use server time and a persisted deadline; client timer is display-only.
- [ ] CSRF protection is enabled for cookie sessions; CORS allows only configured origins.
- [ ] Passwords use the framework password hasher; secrets are environment-provided and redacted.
- [ ] Audit records are append-only and do not store answer values, credentials or raw tokens.
- [ ] Sync envelopes include tenant, origin node, sequence, schema version and idempotency key.
- [ ] Conflicting exam/answer merges fail closed and require review; no silent overwrite.
- [ ] Rate limiting and lockout policies are local-only tests until explicitly specified for deployment.
- [ ] Error responses are generic to untrusted clients and contain no stack traces or SQL.
- [ ] Uploads and exports are permission checked, size limited and stored outside executable paths.

## Evidence requirements

For each check record command, environment, synthetic fixture ID, timestamp, route, expected/actual result and a redacted snapshot path. Never record credentials, OTPs, cookies, session state, authorization headers or full response bodies. A skipped check must say why it was skipped; a passing check must include executable evidence.

## Current blocker

At plan creation time the repository had no frontend/backend manifests or running local service. The contract tests therefore skip unless `QA_API_BASE_URL` is configured. The first integration milestone must seed a local tenant and make health/auth/exam endpoints available before claiming security coverage.
