# EZExam competitor research

## Research boundary

This document describes observations from the authorized `ezexamqwertyuiop.ezexam.in` test account only. It does not inspect other tenants, undocumented endpoints, browser storage, cookies, tokens, or protected assets. The product we design from these observations must use its own identity, code, content model, and interaction design.

Authorization and account scope are user-reported and not independently verified. Research was read-only after manual login. No records were created, edited, deleted, published, exported, messaged, paid for, or launched.

## Evidence conventions

- **Confirmed:** visible in a headed Playwright snapshot from the approved session.
- **Inferred:** a design implication derived from confirmed UI, not a claim about hidden implementation.
- **Proposed:** a requirement for our open-source platform.
- Snapshot files are under ignored `.playwright-cli/`; they may contain account-specific content and are not shared. No screenshots were captured.

## Observed feature inventory

| Feature | Observed path/state | Timestamp (UTC) | Evidence | Confidence |
|---|---|---:|---|---|
| Admin login/dashboard | `/staff#`; authenticated dashboard shows expected Super Admin role | 2026-11-03 19:39 | `.playwright-cli/page-2026-11-03T19-43-43-112Z.yml` and prior session log | High |
| Dashboard navigation | Exams, Students, Settings, Payments & Plans, Customize Site, Demo Videos, More, Logout | 2026-11-03 19:43 | `.playwright-cli/page-2026-11-03T19-43-43-112Z.yml` | High |
| Exams grid | Online/OMR modes; attempts available/total; table, filters and Demo Exam row | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-17-095Z.yml` | High |
| Exam detail | Timing, sharing, Questions, Share, Attempts, Analytics tabs | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-38-856Z.yml` | High |
| Question authoring | 15 questions; answer key, subject, markings, question type, image upload, text/replace, verify link | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-46-361Z.yml` | High |
| Question import choices | One-by-one, Excel/key, Excel+PDF variants, copy from previous exam | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-46-361Z.yml` | High |
| Exam sharing/scheduling | Start/end date/time, all-day, student-tag selector, create exam link, advanced options | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-53-591Z.yml` | High |
| Attempts | Empty state says attempts appear when students take the exam | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-59-950Z.yml` | High |
| Analytics | Empty state; auto-generation after exam closes or manual generation warning | 2026-11-03 19:42 | `.playwright-cli/page-2026-11-03T19-42-05-425Z.yml` | High |
| Students | Searchable table with Name, Student ID and Tags; page-size selector; add/delete/download controls | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-24-439Z.yml` | High |
| Faculty | Searchable table with Name, Phone, Active, Subjects, Student Tags; empty state; Add Faculty | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-06-550Z.yml` | High |
| Centres | Centre Heads table with Name, Phone, Centres, Active; empty state; Add Centre Head | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-14-072Z.yml` | High |
| Notices | Table with visibility, title, centres, groups, classes, editor and edited time; filters; Add Notice | 2026-11-03 19:41 | `.playwright-cli/page-2026-11-03T19-41-21-972Z.yml` | High |
| Account settings | Name/phone/email fields, Change Password, organization name/subdomain and feature checkboxes | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-31-545Z.yml` | High; values redacted |
| Taxonomy settings | Exam Tags, Student Tags and Subjects with existing examples and add controls | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-31-545Z.yml` | High |
| Payments/plans | Capacity, free attempts, currency switch, Students/Attempts plans, pricing and Pay button | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-38-109Z.yml` | High; no payment action taken |
| Site customization | Logo/icon upload, color input and login-page preview | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-47-619Z.yml` | High |
| Help videos | Topics include scheduling/sharing, exam creation, imports, coding, question paper, attempts and analytics | 2026-11-03 19:40 | `.playwright-cli/page-2026-11-03T19-40-54-702Z.yml` | High; external videos not opened |
| Exam report form | Date range, Student Tags and Exam Tags, Generate Report action | 2026-11-03 19:42 | `.playwright-cli/page-2026-11-03T19-42-26-418Z.yml` | High; report not generated |
| Usage report form | Date range and Daily selector with Go action | 2026-11-03 19:42 | `.playwright-cli/page-2026-11-03T19-42-35-030Z.yml` | High; report not generated |
| New online exam form | Name, duration, exam tag, import mode and optional solutions PDF before Next | 2026-11-03 19:42 | `.playwright-cli/page-2026-11-03T19-42-42-161Z.yml` | High; form abandoned without saving |
| New OMR exam form | Name, date, OMR template selection, Excel attachment, solutions PDF and Add action | 2026-11-03 19:43 | `.playwright-cli/page-2026-11-03T19-43-14-383Z.yml` | High; form abandoned without saving |

## Not observed

Attendance, certificates, course management, batch management as a separate module, a dedicated question-bank screen, live proctoring workflow, student exam-taking workflow, synchronization controls, LAN deployment, backup/restore, API administration, audit logs, SSO, and mobile layouts were not visible in this account/session. A pricing page mentions proctoring and question banks, but those marketing statements are not treated as observed workflows.
