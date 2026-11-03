# Password-recovery security test matrix

**Status: preparation only. No live EZExam tests have run.** Authorization is user-reported, not independently verified. Only PR-04 (one manually entered incorrect OTP) is proposed for an initial live test, and it remains paused pending the confirmations in `docs/SECURITY_SCOPE.md`. All other rows require separate approval.

| ID | Control | Safe validation | Expected secure behavior | Evidence | Live status |
|---|---|---|---|---|---|
| ID | Control | Safe validation | Expected secure behavior | Evidence | Live status |
|---|---|---|---|---|---|
| PR-01 | OTP length/format | Review vendor documentation or local mock. No live guessing or malformed-input fuzzing. | Bounded documented format; value is not echoed in logs, URLs, or UI after submission. | Sanitized field metadata or mock result only | Not approved |
| PR-02 | Expiration | Use local mock, or a separately approved vendor-issued test OTP and wait for its stated expiry before one submission. | Expired code rejected; no reset; generic safe response. | Timestamp delta and sanitized UI/status | Not approved |
| PR-03 | Reuse | In local mock, submit a valid fixture twice. Live reuse needs separate approval because it entails a second submission. | First accepted once; subsequent reuse rejected. | Sanitized status/UI only | Not approved |
| PR-04 | Single incorrect OTP | After all scope confirmations, user manually enters exactly one incorrect value into the visible authorized UI. No assistant handling or recording of the value; no retry. | Safe rejection, no reset, no unexpected lockout/account change, no account data disclosure. | Timestamp; route; request method/content type and field names only; response status/size/timing band; redacted UI outcome | **Paused for user confirmation** |
| PR-05 | Recovery request rate limiting | No live rate-limit probing in this phase. Review documentation or use local mock. Future live checks need explicit count/ceiling and vendor approval. | Limits/backoff are bounded and do not impair availability. | Mock result or approved count band and sanitized response metadata | Not approved |
| PR-06 | OTP verification rate limiting | No repeated live negatives in this phase. Future test requires separately approved exact attempt count and lockout safeguards. | Attempts are throttled; limits do not expose account state. | Mock result or approved count band only | Not approved |
| PR-07 | Expiry boundary | Local mock only unless a discrete live case is separately approved; do not create repeated OTPs. | Expiry boundary is enforced consistently. | Mock timestamps or approved single-case timeline | Not approved |
| PR-08 | Account lockout | Do not intentionally trigger live lockout. Stop if a lockout/cooldown or warning appears during PR-04. | Recovery path is bounded and does not enable denial of service. | Visible sanitized state; no account secret | Not approved |
| PR-09 | Account enumeration | No live comparison against nonexistent accounts in this phase. Mock/docs only. | Known/unknown identifiers receive equivalent public behavior. | Mock result only | Not approved |
| PR-10 | Reset/session binding | No token/cookie inspection, session export, cross-session replay, or reset action in this phase. Future visible check requires separate approval. | Reset applies only to intended account and approved flow/session. | Visible UI outcome only; never identifiers | Not approved |

## Matrix execution rules

Do not run automated guessing, SQL injection payloads, credential stuffing, bulk enumeration, concurrency tests, or availability tests. The proposed PR-04 is exactly one manually entered incorrect OTP and is paused until explicitly confirmed. Each other live row needs its own written scope reference, exact request ceiling, expected rollback, stop condition, and approval. If a row cannot be tested safely, mark it untested rather than weakening the control.

The local loopback service in `tools/mock_password_recovery.py` exercises the matrix with synthetic data and fixed fixtures. It never contacts EZExam or any external host.
