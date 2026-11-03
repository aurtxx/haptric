# EZExam security assessment scope

**Status: USER-SUPPLIED AUTHORIZATION REPORTED — NOT INDEPENDENTLY VERIFIED. Live testing remains paused pending confirmation below.**

The user reports supplying the text of a limited vendor authorization email. The email text itself is not present in the project or this conversation, so its sender, date, exact terms, and authenticity have not been independently reviewed. The user identifies password-reset OTP security as the priority and requests one supervised manual submission of an incorrect OTP, followed immediately by a preliminary report. This record does not independently establish vendor authorization.

## Authorization record

| Field | User-supplied information | Verification/status |
|---|---|---|
| Vendor/legal entity | EZExam (vendor legal entity/contact not included) | Reported by user; not independently verified |
| Written authorization | Limited authorization email is reported; its text/date/sender/reference is not present here | Reported by user; terms cannot be checked |
| Assigned account | `ezexamqwertyuiop` | User-supplied; no credentials or OTP recorded |
| Target | `https://ezexamqwertyuiop.ezexam.in/login` | User-supplied target; current headed session origin/path confirmed, exact reset routes not independently verified |
| Priority | Password-reset OTP security | User-supplied |
| Follow-up request ceiling | User reports follow-up approval up to 5,000 HTTP requests per hour | User-reported only; no window, per-account/per-IP allocation, concurrency, exact technique allowance, or vendor terms reviewed; not used for this assessment |
| Testing window/timezone | Not provided | Missing; must be confirmed |
| Source IP | Not provided | Missing; must be confirmed; no IP probe performed |
| Rate/concurrency/retry limits | Above hourly ceiling is reported; detailed limits remain unspecified | Not independently verified; no automated requests performed |
| Other permitted techniques | User prohibits automated live OTP guessing and password reset in current task | User-supplied; no other techniques inferred |
| Vendor emergency contact | Not provided | Missing |
| Reporting contact | `admin@ezexam.in` | User-supplied destination for a draft; no report will be sent by this assistant |

## Default exclusions until confirmed in writing

Do not test production or unrelated tenants, other users, staff/admin interfaces, undocumented APIs, infrastructure, third-party identity providers, email/SMS providers, payment flows, uploads, destructive actions, messages, publishing, permission changes, bulk enumeration, denial-of-service, high-volume fuzzing, SQL injection payloads, credential attacks, CAPTCHA/MFA bypass, token/cookie extraction, or protected asset copying.

Do not treat the reported email or assigned account as independently verified authorization. The manager must review the actual written scope (a suitably redacted copy or its exact terms), record the testing window, timezone, source IP, per-test limits, stop contact and exclusions, and receive explicit approval before any live verification attempt. A broad hourly request ceiling is not approval for automated guessing. No live OTP guessing or password reset was performed for this assessment; one user-initiated OTP request is documented separately in the research notes.

## Stop conditions

Stop immediately, preserve only redacted evidence, and notify the vendor contact and manager if any of the following occurs:

- An unexpected account, role, tenant, password, email, MFA, permission, billing, or profile change appears.
- A request reaches an out-of-scope origin, path, account, endpoint, or third-party service.
- The application returns server errors, data from another account, stack traces, internal URLs, secrets, or unusual volume/latency.
- The vendor reports availability impact, rate-limit pressure, abuse alerts, lockouts, or an incident.
- A CAPTCHA/MFA challenge, consent boundary, authorization ambiguity, or unexpected destructive action appears.
- Any lockout, cooldown, abuse warning, or account recovery state change occurs or appears likely after the one planned negative submission.
- The incorrect-OTP submission might affect a real user's access, or the test account cannot be positively distinguished from another account.
- The source IP, testing window, account, or authorization cannot be verified.

Do not retry through an error, bypass a control, widen the scope, or continue after a stop condition without fresh written direction from the vendor and manager.

## Confirmation required before active testing

## Required confirmation before the single live test

Before any live browser session or request, the user must:

1. Confirm the authorization email is written vendor authorization covering this exact host, the assigned account, password-reset flow, and one incorrect OTP submission; provide its date and a redacted reference or the exact applicable terms.
2. Confirm the allowed date/time window and timezone, vendor-approved source IP, and exact rate/retry ceiling. Confirm whether initiating one password-recovery request to the assigned account is approved (it may send an email/SMS), and exactly one incorrect OTP submission is approved. No retries, automation, or concurrent requests are planned.
3. Confirm that this negative submission is permitted without risking lockout or account disruption; provide an emergency stop contact and confirm the report destination `admin@ezexam.in`.
4. Explicitly approve opening the visible login/reset flow and submitting that one incorrect OTP. This approval does not authorize the remaining matrix.

Until all four are confirmed, status remains **paused**. Never ask the user to send credentials or the actual OTP in chat. The user must enter any values directly into the visible browser.
