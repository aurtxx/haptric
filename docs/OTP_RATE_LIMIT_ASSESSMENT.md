# OTP rate-limit assessment — local mock only

## Executive summary

Assessment was performed only against the repository's synthetic loopback mock at `127.0.0.1` on an ephemeral port. **No EZExam host or other external service was contacted.** This validates the mock's behavior and test workflow; it provides no evidence about EZExam's implementation.

The final run generated a fresh random four-digit challenge in memory and submitted 20 distinct incorrect values. The mock counted five failures server-side, returned `423` from attempt 5 onward, and rejected the correct value during the active lockout. When the lockout timer was advanced using an internal test fixture (not a real wait), the still-unexpired challenge was accepted. Expiration, session binding, replay prevention, and the recovery-request rate limit behaved as configured. Sanitized failure bodies were generic, though HTTP status codes distinguish failure states.

The assessment also found a local mock defect: before correction, requesting a new challenge cleared the account's failure counter and active lockout. The mock was updated to preserve account-scoped lockout state across reissue; the final regression run confirmed the fix. **This defect belonged to the mock only and must not be attributed to EZExam.**

## Environment and scope

- Environment: Python standard-library HTTP server/client, bound only to `127.0.0.1`, ephemeral local port.
- Harness: `tools/mock_password_recovery.py --assessment`.
- Synthetic challenge: `secrets`-generated four-digit OTP held in process memory. OTP values, wrong candidates, session identifiers, cookies, request bodies, and passwords were not printed or logged.
- Mock policy: verification limit 5, 60-second lockout, 120-second OTP TTL, and 3 recovery requests per source-IP/account within 60 seconds.
- Session model: synthetic `X-Test-Session` value held in memory; logs contain no session identifier.
- Test data: fixed synthetic account under the reserved `.test` domain.
- Time reference: UTC timestamps from the final post-correction assessment run on 2026-11-03.
- Live EZExam assessment: **not performed**. Vendor authorization terms, source IP, testing window, and limits remain unverified in `docs/SECURITY_SCOPE.md`.

## Methodology

1. Start an ephemeral local server and issue a fresh challenge for the synthetic test account.
2. Generate 20 distinct incorrect four-digit values in memory; submit them sequentially through the local verification endpoint. Never print or persist any submitted value.
3. Record UTC timestamp, attempt number, HTTP status, and sanitized response message. Read the mock's in-memory counter after the sequence to confirm server-side counting.
4. Submit the correct value once while locked, then use a local-only clock fixture to move the lockout expiration into the past and submit it again while still within the challenge TTL.
5. Use fresh mock state to check wrong-session rejection, correct bound-session use, replay, expiration, and recovery-request throttling.
6. Reissue after lockout to check whether requesting a new challenge resets the account-level attempt counter. Correct the mock after recording the baseline defect, then rerun the full assessment.

## Twenty incorrect submissions

Final post-correction run. Every message below was the same sanitized generic text; the OTP values were not recorded.

| UTC timestamp | Attempt | HTTP | Sanitized message |
|---|---:|---:|---|
| 2026-11-03T19:21:27.173Z | 1 | 401 | Unable to verify request. |
| 2026-11-03T19:21:27.189Z | 2 | 401 | Unable to verify request. |
| 2026-11-03T19:21:27.191Z | 3 | 401 | Unable to verify request. |
| 2026-11-03T19:21:27.192Z | 4 | 401 | Unable to verify request. |
| 2026-11-03T19:21:27.193Z | 5 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.204Z | 6 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.221Z | 7 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.235Z | 8 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.237Z | 9 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.238Z | 10 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.239Z | 11 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.240Z | 12 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.240Z | 13 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.267Z | 14 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.268Z | 15 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.282Z | 16 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.283Z | 17 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.298Z | 18 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.300Z | 19 | 423 | Unable to verify request. |
| 2026-11-03T19:21:27.313Z | 20 | 423 | Unable to verify request. |

## Results

| Control | Result | Evidence / limitation |
|---|---|---|
| Server-side attempt counting and lockout | **Pass in final mock** | Attempts 1–4 returned 401; attempt 5 activated lockout and returned 423. Attempts 6–20 remained 423. In-memory count stayed at 5 because later requests were rejected while locked. |
| Correct OTP immediately after 20 failures | **Rejected while locked** | At `2026-11-03T19:21:27.315Z`, valid challenge returned 423 with the same generic failure message. |
| Challenge after lockout cooldown | **Still usable in mock** | At `2026-11-03T19:21:27.329Z`, the harness advanced the lockout timer using an internal fixture (no real 60-second wait); the correct value then returned 200 before the 120-second challenge expiry. The mock preserves the challenge across lockout. Whether that is acceptable is a policy decision; consider invalidating it after the attempt ceiling. |
| Session binding | **Pass in mock** | A different synthetic session got 400; the issuing session then got 200. No session value was logged. |
| Expiration | **Pass in mock** | The test-only expiry fixture forced the issued-at time beyond the 120-second TTL; valid verification returned 400 with the generic message. This was an accelerated fixture, not a real-time wait. |
| Replay prevention | **Pass in mock** | After one successful verification, replay returned 400 with the same generic failure message. |
| Recovery-request rate limit | **Pass in mock** | Requests 1–3 returned 202; request 4 within the 60-second window returned 429 `rate_limited`. |
| Safe error body | **Partial pass** | Invalid, locked, expired, wrong-session, and replay failures used `Unable to verify request.` without remaining-attempt or retry-time details. HTTP codes differ (400/401/423), so clients can distinguish some states. |
| Lockout persistence across challenge reissue | **Failed before correction; passed after correction** | Baseline at `19:21:07.934Z`: reissue returned 202, reset server count to 0, cleared lockout, and one more wrong value returned 401. Mock correction preserves account-scoped counters/lockout. Final at `19:21:27.407Z`: reissue returned 202, count remained 5, lockout remained active; next wrong value returned 423 at `19:21:27.423Z`. |

## Pass/fail criteria

- **Pass:** Count invalid attempts on the server; block verification at the configured threshold; do not reset the account's attempt budget when a fresh OTP is issued; reject expired, wrong-session, and replayed challenges; rate-limit recovery requests; avoid returning OTPs, remaining attempts, retry durations, or account existence.
- **Fail:** A new challenge clears the account-level failure counter or lockout and permits another guess budget. This failed in the baseline mock and passed after the mock correction.
- **Conditional:** The mock allows a still-unexpired challenge to succeed after lockout cooldown. If policy requires a challenge to be invalidated on threshold, this fails that policy; the test must not assume the policy without vendor requirements.
- **Not assessed:** Any EZExam deployment, real OTP entropy/generation, email/SMS delivery, distributed-source limits, cross-tenant binding, production persistence, or behavior of a user-facing API.

## Implications and remediation

The four-digit code has only 10,000 possible values, so its safety depends on strict server-side limits and short validity. A client-side counter is insufficient. Preserve attempt state across OTP reissue and across browser sessions; key controls at least to the account/challenge and add source/network abuse controls. Invalidate or rotate the challenge at the attempt ceiling if that matches the recovery policy, and avoid permanent account lockout that could enable denial of service. Keep failures generic, avoid disclosing remaining guesses or exact retry times, and log only sanitized metadata. Use a higher-entropy OTP where product constraints allow.

For a real vendor assessment, use a vendor-approved staging tenant and explicitly documented limits. Do not infer EZExam behavior from this mock result. No live OTP guessing, brute force, reset, or testing of another tenant occurred.

## Verification

- `python -m py_compile tools/mock_password_recovery.py` — passed.
- `python tools/mock_password_recovery.py --self-test` — passed (`SELF_TEST_OK`).
- `python tools/mock_password_recovery.py --assessment` — passed (`ASSESSMENT_COMPLETE`); only loopback requests were made.
- During harness development, earlier iterations also ran synthetic 20-attempt batches against the same ephemeral loopback mock. Those runs did not contact any external host; the table above records the final post-correction batch.
