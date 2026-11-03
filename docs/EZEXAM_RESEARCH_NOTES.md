# EZExam product research notes

**Session:** `product-research`  
**Date:** 2026-11-04 Asia/Calcutta  
**Status:** Partial; OTP request UI observed; no verification or password reset  
**Evidence basis:** Read-only Playwright CLI snapshot from the visible authenticated session. No sanitized screenshot was captured. The raw CLI snapshot remains in ignored `.playwright-cli/` and is not shared because it contains account-specific content.

## Login and dashboard

- User confirmed they completed login manually; no credentials were provided in chat or handled by the agent.
- The same session displayed `/staff` with a product home/dashboard title, confirming an authenticated view.
- Visible navigation categories: Exams, Students, Settings, Payments & Plans, Customize Site, Demo Videos, More, and Logout.
- Visible dashboard entry points included online and OMR exam actions/list, student and faculty areas, site customization, settings, exam and usage reports, FAQs, and an onboarding tour.
- The page displayed the role label **Super Admin**. The user confirmed this is the expected admin account for the assigned username. No privileged module or control was opened.
- No record was created, edited, or deleted. Logout was later performed with the user's explicit approval; recovery was inspected only to the point described below.

## Logout and recovery interface inspection

- The user explicitly approved logout. A dashboard onboarding overlay initially intercepted the logout control; Escape did not dismiss it, so the visible `Skip` control was used (the “Don't Show Again” checkbox was not selected). The logout confirmation dialog was then confirmed, and the browser returned to `/login`.
- The login page exposes a `Phone / Email / Student ID` field, a password field, and a `Forgot Password` link.
- The recovery panel exposes an `Email / Phone Number` field, account-type radio options (`Student` and `Admin`), a `Get OTP` control, and `Back to Login`. Student was initially selected; the visible Admin option was selected for inspection, with no request submitted.
- In the selected Admin view, no OTP entry or password confirmation fields were visible before requesting an OTP.
- `Get OTP` was not clicked because it may send an email/SMS. No identifier was entered, OTP requested or entered, password reset, or additional test performed.
- Admin remained selected and the user-provided test email was entered into the visible field; its value is intentionally not copied into this document. Initially `Get OTP` was not clicked. The user later reported clicking it manually once.
- At 2026-11-04 00:42 Asia/Calcutta (2026-11-03 19:12 UTC), the visible UI displayed a notice that an OTP was sent to the entered address. This is a UI observation only; delivery was not independently verified. The email address and any code are omitted.
- Newly visible controls: four number-type inputs with no accessible labels (consistent with OTP entry, but format/length not verified), `New Password` and `Repeat Password` password fields (both empty), plus `SET PASSWORD`, `Cancel`, and `Resend OTP` controls.
- No OTP value was viewed, copied, or entered. No resend, incorrect-code attempt, password submission, or reset occurred. No screenshot was captured.
- The browser remains at the logged-out recovery form. Do not click `Resend OTP` or `SET PASSWORD`; no further interaction is authorized here. The written scope is still not independently verified, and testing window, source IP, and vendor limits remain missing.

## Current pause

The user asked whether OTP guessing could affect another tenant/account and mentioned `davjsg.ezexam.in` as an example; that target is outside the recorded scope and was not visited. Repeated OTP guessing is prohibited. One OTP request was reported by the user and the UI displayed a sent notice. OTP verification and password reset remain unperformed. The UI is currently logged out at the recovery panel.

## Not assessed

- Other dashboard pages, controls, workflows, and role boundaries.
- OTP validation behavior and code format/length, which were not tested.
- Recovery validation behavior and OTP delivery.
- OTP delivery or verification behavior.
- Accessibility, responsive layouts, and visual comparison.
