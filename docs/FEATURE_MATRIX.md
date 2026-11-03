# Feature matrix for the independent platform

Legend: **Observed** is visible in the authorized EZExam session; **Proposed** is our independent design; **Not observed** was not available in the research session.

| Capability | EZExam evidence | Our MVP | Phase 2 | Future |
|---|---|---|---|---|
| Organization/institute workspace | Settings shows organization name/subdomain | Workspace and tenant settings | Multiple campuses | Multi-organization federation |
| Admin authentication | Login, password and manual recovery UI observed | Local accounts, sessions, recovery policy | SSO/OIDC | Hardware keys |
| Students | Table, tags, ID, filters, add/delete/download controls | Student directory, import, tags | Bulk lifecycle and guardian links | SIS connectors |
| Faculty | Faculty table and subject/tag columns | Faculty accounts and scoped permissions | Faculty workload and delegation | HR integration |
| Centres/classes | Centre Heads and “Use Classes & Centres” setting | Optional campus/class hierarchy | Cross-campus reporting | Franchise federation |
| Subjects/taxonomy | Subjects and tags in Settings | Subjects, topics, tags | Difficulty/outcome taxonomy | Standards mapping |
| Online exams | Exam grid, timing, questions, sharing and attempts | Exam authoring, scheduling and link sharing | Sections, randomization, question pools | Adaptive testing |
| Question bank | Import modes and question editor observed; dedicated bank not observed | Reusable question bank with versioning | Review workflow and blueprinting | Marketplace/package exchange |
| OMR | New OMR form and templates observed | OMR template/import boundary | Scanner integration | Mobile scan pipeline |
| Attempts/results | Attempts and Analytics tabs; empty state | Attempt capture, scoring, result review | Moderation and appeals | Longitudinal insights |
| Reporting | Exam/Usage report forms | Saved report views and CSV export with approval | Scheduled reports | BI connectors |
| Notices | Notices table and scoped columns | In-app announcements | Email/push delivery with consent | Multi-channel campaigns |
| Proctoring | Marketing claim only; workflow not observed | Explicitly out of MVP unless requirements demand it | Optional consented controls | Advanced proctoring |
| Attendance | Not observed | Not in MVP | Session attendance | Institution-wide attendance |
| Certificates | Not observed | Not in MVP | Template-based certificates | Verification registry |
| Offline LAN | Not observed | Single-node LAN deployment and local auth | Sync bridge | Edge fleet management |
| Cloud WAN | Not observed | Containerized cloud deployment | Multi-region operations | Federated tenancy |
| Disposable exam lifecycle | Draft flow entered three questions, but reopened same-name record showed 15 questions; no access or attempt | Authoring, immutable publish, assignment and attempt receipt | Moderation and regrade workflow | Cross-campus exam federation |
| Timer/autosubmit | Duration range 10–240 minutes observed; runtime expiry not tested | Server-authoritative deadline and exactly-once autosubmit | Offline queue/reconnect indicators | Advanced accommodations |
| Student exam question modes | Maths single-choice, Physics multiple-correct, Chemistry numerical-value UI observed in 5-question sections; question content intentionally omitted | Typed question schemas and accessible controls | Pools, branching and accommodations | Adaptive item selection |
| Exam interaction state | Section/question navigation, overview legend, review/save labels and irreversible submit warning observed; persistence not exercised | Explicit visited/answered/reviewed/saved/submitted state machine | Offline queue and moderation | Cross-device resume |
| Frontend indicators | Public resource metadata showed jQuery 3.2.1 and legacy-named widget assets; full stack not verified | Independently implemented typed frontend/API | Performance budgets and plugin adapters | White-label theming SDK |
