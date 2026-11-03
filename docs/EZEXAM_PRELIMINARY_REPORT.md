# EZExam preliminary security report (draft)

**Recipient:** `admin@ezexam.in`  
**Status:** Updated draft, not sent. One user-reported OTP request produced a visible UI sent notice; no verification attempt or password reset occurred.  
**Authorization basis:** User reports a limited vendor authorization email; its text and provenance have not been independently reviewed.

**Current status:** The user reported manually clicking `Get OTP` once after the form was prepared. The visible UI subsequently displayed an OTP-sent notice. Delivery was not independently verified. No OTP was viewed, recorded, or entered; no incorrect attempt or password reset occurred. Written scope remains user-reported and unverified. This draft is not a finding and must not be sent as a completed security assessment.

This draft records the current limited observation. Fill missing scope metadata using verified, redacted information and review before sending. Do not attach raw browser traces, screenshots, messages, or request bodies until reviewed and redacted. Do not send automatically.

## Subject

Authorized password-reset OTP assessment — preliminary result — [date]

## Message

Hello EZExam Security Team,

This is a preliminary status update for a password-recovery workflow review. The user reports having vendor authorization, but its terms and provenance have not been independently reviewed. This is not a report of a confirmed vulnerability.

- **Authorization reference (redacted):** [reference]
- **Approved window/timezone:** [start/end and timezone]
- **Target:** `https://ezexamqwertyuiop.ezexam.in/login` and only the specifically approved visible recovery flow
- **Test account:** assigned account `ezexamqwertyuiop` (no password or OTP included)
- **Source IP:** [user/vendor-supplied IP or approved label]
- **Test performed:** [describe only actions actually completed; no incorrect OTP was submitted as of this draft]
- **Sanitized request metadata:** [method, approved visible route, content type, field names only; omit field values and secrets]
- **Sanitized response metadata:** [status, response-size band, timing band; no raw body]
- **UI behavior:** [redacted visible result]
- **Account state:** [no unexpected change observed / stop condition observed / unable to determine]
- **Result:** [safe rejection / unexpected behavior / inconclusive]
- **Evidence:** [reviewed, redacted evidence identifier/path, if safe to share]

No password, OTP, reset URL, cookie, session token, message content, or unrelated personal data is included. No incorrect OTP submission, resend, or password reset occurred as of this draft. No further testing is authorized by this status update. [If applicable: We stopped immediately due to the following sanitized stop condition: ...]

### Current preliminary observation (replace template claims above before sending)

- **Observed at:** 2026-11-04 00:42 Asia/Calcutta (2026-11-03 19:12 UTC)
- **User-reported action:** one manual click on `Get OTP`; exact click time not recorded
- **Visible response:** UI stated that an OTP was sent to the entered test address; delivery not independently verified
- **Fields then visible:** four unlabeled number-type inputs; `New Password` and `Repeat Password` password fields; `SET PASSWORD`, `Cancel`, and `Resend OTP` controls
- **No OTP was viewed, copied, or entered. No invalid attempt, resend, or password reset was performed.**
- **Assessment conclusion:** inconclusive; this observation does not establish OTP delivery, expiry, rate limiting, resistance to guessing, or account/tenant binding.
- **Scope limitations:** vendor authorization terms, testing window, source IP, and request limits are not independently verified or recorded.

Please acknowledge receipt and advise whether you would like any further work. No additional testing is authorized by this preliminary report.

Regards,  
[Reporter/team]

## Send checklist

- Confirm written authorization reference and reporting channel.
- Fill only fields supported by contemporaneous sanitized evidence; label unknown values as unknown.
- Redact screenshots and verify no OTP, reset link, account secret, cookie, token, email/SMS content, or unrelated private data remains.
- Have the manager review scope, evidence, and wording before the user sends it.
- Do not send from this workflow without the user's separate explicit instruction.
