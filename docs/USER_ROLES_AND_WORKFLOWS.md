# Roles and workflows

## Observed role

The authorized session displayed **Super Admin**. This confirms only the visible role label for this test account. The session did not compare permissions with another role.

The Super Admin could open the online-exam authoring flow and add a tagged student in the approved disposable-record checkpoint. Scheduling, assignment, publishing and student access were not exercised.

## Proposed roles

| Role | Core permissions | Guardrails |
|---|---|---|
| Organization owner | Workspace, billing metadata, policy and backup controls | MFA, audit trail, two-person approval for destructive actions |
| Exam administrator | Students, faculty, subjects, question bank, exams and reports | Tenant-scoped permissions and reviewable changes |
| Faculty/examiner | Assigned exams, question authoring and result review | Cannot manage billing, tenant policy or unrelated cohorts |
| Centre manager | Assigned centre/classes, notices and local reports | Campus boundary enforced server-side |
| Invigilator | Exam session monitoring and attendance | No question-bank or identity administration |
| Student | Assigned exam links, attempts and results | Own-record access only |
| Auditor | Read-only logs and reports | No mutations or exports without approval |

## Proposed end-to-end workflows

1. Owner creates a workspace and chooses LAN or cloud deployment.
2. Administrator imports students and faculty, defines subjects/classes, and reviews the import summary.
3. Faculty creates or reuses questions, assembles an exam, previews it, and submits it for approval.
4. Administrator schedules the exam and shares a scoped link or classroom code.
5. Invigilator opens a session, records attendance, and monitors status without seeing secrets.
6. Student completes the exam online or through an approved LAN client.
7. The server scores objective questions, queues manual review for subjective answers, and publishes results only after approval.
8. Reports are generated from saved queries and exported only through an explicit, audited action.
9. LAN nodes back up locally and optionally synchronize approved records to the cloud.
