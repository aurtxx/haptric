# Product brief
Project name: OpenExam (working title)
Problem: Schools and coaching communities need a simple examination workflow that keeps working on a local LAN when internet access is unreliable, while still synchronizing safely to a cloud deployment when available.
Target user: School, coaching-institute and tuition-center administrators, teachers, invigilators and students.
One-sentence solution: An open-source, tenant-safe exam platform with a complete author → assign → attempt → score workflow that runs on a LAN and synchronizes through explicit, idempotent boundaries to the cloud.
Hackathon rules / theme / deadline: TBD (verify against official event page)
Must-have user journey: Admin creates an exam with three original questions, assigns it to a test student, the student starts and answers it, answers persist, the server-authoritative timer submits exactly once, marks are calculated, and both student and admin can view the matching result.
Tech stack: React + TypeScript + Vite + Tailwind CSS; Python + Django + Django REST Framework; PostgreSQL; pytest + Vitest + Playwright; Docker Compose for local/LAN development.
Demo URL: TBD
Judging criteria: TBD (verify)
Constraints: Preserve tenant isolation and role boundaries; keep exam content versions immutable after publish; do not automatically merge conflicting answer events; avoid copying competitor branding, code or protected assets; support Windows PowerShell setup; do not claim unrun checks or unsupported offline behavior.

## First-slice acceptance criteria

1. A fresh local environment can run the API, frontend and database using documented commands or a clear no-Docker fallback.
2. Organization-scoped users can authenticate and receive role-aware API responses.
3. An administrator can create a draft exam with three question types represented by typed API contracts and persist it through a transaction-safe endpoint.
4. An administrator can assign the exam to a student without exposing another tenant's records.
5. A student can start the assigned exam and receive a server-issued deadline.
6. Answers can be saved idempotently and are recoverable after a page reload or simulated reconnect.
7. Submission is exactly-once, rejects late writes after the deadline, calculates marks from the published version, and creates an audit event.
8. Student and administrator result views show the same attempt receipt and score.
9. Automated tests cover tenant isolation, role permissions, scoring, timer expiry and duplicate submission; frontend tests cover loading/error/empty states.
