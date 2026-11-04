# Haptric hackathon release

## Release status

P1.4 release candidate is judge-ready on the `release/hackathon-final` branch. Core engineering is feature-frozen; this pass addressed branding, copy, accessibility focus states, responsive navigation, CORS reliability, setup documentation, and rehearsal material.

## Verified product journey

- Staff login, overview, students, exam authoring, publishing, assignment, Results, and question-level review.
- Student login, assigned exam discovery, server attempt start, persisted answers, refresh restoration, server deadline, submission, and server result.
- LAN operation during upstream Cloud outage, durable pending events, recovery sync, Cloud staff review, and idempotent replay.

## Release checks

- Backend Django check: PASS.
- Backend and QA suite: 35 passed, 4 skipped. Skips are optional contract checks requiring unavailable infrastructure.
- Sync/security targeted suite: 9 passed.
- Frontend lint/typecheck: PASS.
- Frontend tests: 2 files, 14 passed.
- Frontend production build: PASS.
- PowerShell demo parser: `POWERSHELL_PARSE_OK`.
- Demo setup/seed/check/reset smoke: PASS.
- `git diff --check`: PASS.

## Headed browser rehearsal

The rehearsal used separate headed LAN and Cloud browser sessions at 1280x720 and 390x844, plus a 1440x900 login capture.

1. Staff logged in on LAN and verified the persisted synthetic exam/student.
2. Student logged in on LAN, started the assigned three-question exam, answered Q1/Q2, refreshed, and saw the same answers and reduced server deadline.
3. Cloud was stopped. The student answered Q3 and submitted successfully on LAN with a server result of 2.00 (2 correct, 1 incorrect, 0 unanswered).
4. LAN staff saw five changes waiting to sync; the sync command retained them while Cloud was unavailable.
5. Cloud restarted; sync accepted five events. Cloud staff opened Results and Review and saw the same student, score, three ordered questions, responses, and correctness.
6. A replay created no duplicates: Cloud remained at one attempt, three answers, and one result.
7. Mobile review layout was inspected at 390x844; desktop layout at 1280x720; login at 1440x900. Navigation, review heading flow, actions, and result content remained usable.

## Release security summary

- Session authentication and CSRF remained enabled.
- CORS is explicit and credentialed; the `Idempotency-Key` preflight required by attempt start is allow-listed and covered by a regression test.
- Tenant isolation, answer-key redaction, staff review permissions, published-question integrity, node authentication, replay, and conflict handling remain covered by backend tests.
- No sync token is present in React source or browser requests.
- No credentials, databases, screenshots, auth state, or generated artifacts are tracked.

## Honest limitations

- “Offline” means upstream Cloud outage while the browser still reaches the LAN node; browser-offline/PWA is not implemented.
- The demo seeds matching reference data into both disposable nodes.
- Sync is a bounded manual command, not a production scheduler.
- PostgreSQL/Docker two-node runtime was not available in this environment.
- Production token rotation, signed envelopes, rate limiting, and operational monitoring remain future hardening.

## Submission checklist

- [x] Canonical Haptric branding in judge-facing UI and README.
- [x] Standard Windows PowerShell setup documented.
- [x] Reproducible LAN/Cloud demo scripts and safe reset.
- [x] Three-minute judge script, recovery guide, and FAQ.
- [x] Headed outage/recovery/replay rehearsal completed.
- [x] Desktop and mobile responsive review completed with screenshots.
- [x] Backend/frontend/build/security gates executed.
- [ ] Add official event URL, judging rubric, deadline, and submission URL when confirmed by the organizer.
- [ ] Record the final presentation or submit the release package.
