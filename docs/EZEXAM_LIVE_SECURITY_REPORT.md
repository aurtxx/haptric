# EZExam live security assessment report

**Status:** Draft for review; not sent.  
**Conclusion:** No vulnerability finding established. Key OTP security properties are **NOT VERIFIED**.  
**Target:** `https://ezexamqwertyuiop.ezexam.in/login`  
**Account:** Designated vendor-provided test account only.

## Executive summary

The existing headed Playwright session was confirmed on the specified EZExam login route. The user reports manually clicking `Get OTP` once for the designated test account. At the subsequent UI observation, the recovery page displayed an OTP-sent notice and showed OTP-entry and new-password controls. The exact request time and HTTP response status were not captured; message delivery was not independently verified.

No OTP was inspected or entered. No incorrect attempt, resend, password reset, automated guessing, or cross-tenant request was performed. Consequently this evidence does not establish rate limiting, lockout, OTP expiration, session binding, replay prevention, challenge reissue behavior, account enumeration, or cross-account impact. No severity is assigned.

## Scope and authorization

- Target origin/path: `https://ezexamqwertyuiop.ezexam.in/login` and the visible recovery interface on that origin.
- Account: designated vendor-provided test account; account identifiers and email address are omitted from evidence.
- Authorization: user reports a vendor authorization email covering the account and URL, plus follow-up approval up to 5,000 HTTP requests per hour. These claims are **user-reported and not independently verified**; the email text, sender, date, testing window, and exact terms are not recorded here.
- Request ceiling: the reported hourly ceiling was not used. No automated or repeated live requests were made by the agent.
- Exclusions: OTP guessing, password reset, secret/token/cookie inspection, other accounts/tenants, and testing `davjsg.ezexam.in`.
- Source IP: **[NOT PROVIDED]**.
- Reporting destination: `admin@ezexam.in` (user-supplied); this report has not been sent.

## Environment

- Browser: existing Playwright CLI `product-research` session, headed Chromium, persistent profile.
- CLI version recorded in session log: 0.1.23.
- Current page target was confirmed in-session as `https://ezexamqwertyuiop.ezexam.in/login`.
- No screenshot was retained for this report because browser captures can contain account-specific data. No cookies, tokens, passwords, or OTPs were inspected or exported.
- The named browser session remains open at the approved login route. The recovery interface was last observed after the user's request at the time listed below; no new OTP request was triggered by the agent during this report preparation.

## Actions and evidence

| Evidence ID | Time (UTC) | Action / evidence | Result and limits |
|---|---|---|---|
| LIVE-01 | 2026-11-03 19:12 UTC (observation time; exact click time unknown) | User reported one manual click on `Get OTP`; agent read visible UI text with email addresses redacted and inspected visible input metadata without reading input values. | UI displayed an OTP-sent notice. This confirms only what the page displayed; delivery was not independently verified. |
| LIVE-02 | Same observation | Visible controls after request: four number-type inputs without accessible labels; `New Password` and `Repeat Password` password fields; `SET PASSWORD`, `Cancel`, and `Resend OTP`. | Inputs were empty. Four controls are consistent with OTP entry, but OTP length/format was not submitted or verified. No resend or password action was taken. |
| LIVE-03 | Current session review | Playwright session listing showed the named headed Chromium session open; an in-session evaluation returned the approved origin/path. | Confirms browser location only; no request trace, response body, cookie, or token was inspected. |

### Request/response evidence

- User-initiated action: one reported click on `Get OTP`; the exact click timestamp and outgoing request metadata were not captured.
- Visible response: OTP-sent notice, with the recipient omitted from this report.
- HTTP response status: **NOT VERIFIED**. No safe status-only record was available from the contemporaneous notes; no raw request/response trace was inspected to avoid capturing secrets or private data.
- Lockout/error message: none observed during this single request; lockout behavior was not exercised.
- No OTP, password, cookie, token, reset URL, or message content is retained here.

## Findings and unverified properties

| Property | Status | Evidence / limitation |
|---|---|---|
| OTP request UI response | Observed | Page displayed an OTP-sent notice after the user-reported click. Delivery and response status are unknown. |
| Input validation | Partially observed | Admin recovery panel displayed an email/phone field before request and four unlabeled number inputs afterward. No invalid field input was submitted. |
| Verification attempt rate limiting | **NOT VERIFIED** | No live OTP value was entered and no invalid verification attempt was made. |
| Lockout threshold/duration | **NOT VERIFIED** | No lockout was triggered; no lockout message or status observed. |
| OTP expiration | **NOT VERIFIED** | No OTP was inspected or submitted after a wait. |
| Session/account binding | **NOT VERIFIED** | No cross-session or cross-account verification was attempted. |
| Replay prevention | **NOT VERIFIED** | No code was submitted, so no replay test occurred. |
| Reissue behavior | **NOT VERIFIED** | `Resend OTP` was not clicked; no second challenge was requested. |
| Account enumeration | **NOT VERIFIED** | Only the designated test account was used; no unknown-account comparison was made. |
| Cross-tenant/account impact | **NOT VERIFIED** | No other tenant or account was accessed. |
| Safe error disclosure | **NOT VERIFIED** | No invalid, expired, reused, or locked response was elicited. The single request acknowledgment is insufficient to assess enumeration. |

## Risk assessment

No exploitable condition is confirmed by the available live evidence. The OTP-sent notice is a UI acknowledgment, not proof of successful delivery or a security result. Brute-force resistance, account/tenant isolation, and recovery-token protections remain unassessed. Risk and severity therefore remain **undetermined**.

## Reproduction of the observed UI state

This records the sequence already reported/observed; it is not authorization to repeat it. Do not repeat the request until the written scope, window, source IP, and vendor limits are confirmed.

1. Open the approved login route in the headed browser and complete account login manually.
2. Open the visible Forgot Password flow and select Admin for the designated admin test account.
3. The user-provided test email was entered in the visible field; the value is omitted. The user reports manually submitting one OTP request.
4. Observe the visible acknowledgment and recovery controls without reading or recording the OTP. Do not submit a code or change the password.

The reported request was user-initiated. The account email is deliberately omitted. No automated request or verification sequence was run.

## Recommendations

- Have the vendor verify server-side request and verification controls from staging configuration or sanitized logs: per-account/challenge limits, source/network abuse controls, lockout behavior, and safe recovery.
- Confirm OTP expiry, single-use behavior, and binding to the intended account and recovery session using vendor-controlled staging test accounts.
- Ensure attempt limits survive OTP reissue and cannot be reset by starting a new challenge. Do not reveal remaining guesses or distinguish account existence unnecessarily.
- Prefer an OTP with sufficient entropy and a short lifetime; make throttling and lockout limits server-side.
- Capture status-only evidence through an approved staging harness or vendor-provided log export that excludes request bodies, OTPs, cookies, tokens, and personal data.
- Do not use the reported 5,000 requests/hour ceiling for OTP guessing. It is not needed for this limited observation and could cause disruption.

## Separate local mock results

The local mock assessment is documented in [OTP_RATE_LIMIT_ASSESSMENT.md](OTP_RATE_LIMIT_ASSESSMENT.md). It tested a synthetic four-digit challenge, attempt lockout, reissue, expiry, session binding, replay, and generic errors on `127.0.0.1` only. Those results describe the mock and are **not evidence about EZExam**.

## Limitations and handling

- The authorization email and follow-up request ceiling were reported by the user, not independently reviewed.
- Testing window, vendor-approved source IP, emergency contact, and exact permitted techniques remain missing from `docs/SECURITY_SCOPE.md`.
- The live request's HTTP status and exact click time were not captured. No status is inferred from the UI notice.
- No screenshot or raw network trace is attached; the session artifacts may contain account-specific material.
- No report has been sent. Any further live assessment requires completed scope and explicit approval for each non-read-only action.
