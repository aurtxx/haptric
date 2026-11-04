# HAPTRIC LOCAL TESTING

This guide describes the currently implemented Haptric product and the disposable local data used to exercise it. Commands are written for Windows PowerShell. The normal browser experience is a single React page; navigation changes the in-memory screen, not the browser URL.

## Quick start: one local node

Run these commands from the repository root in separate PowerShell terminals.

### 1. Backend

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

### 2. Frontend

```powershell
Set-Location frontend
npm install
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
npm run dev -- --host 127.0.0.1 --port 5173
```

Open the frontend at `http://127.0.0.1:5173/`. Vite proxies `/api` and `/health` to Django, so the browser does not need a direct cross-origin API URL for this single-node setup.

| Service | URL | Purpose |
|---|---|---|
| Haptric web app | `http://127.0.0.1:5173/` | React SPA and login |
| Django health | `http://127.0.0.1:8000/api/health/` | Backend readiness check |
| API base (through Vite) | `http://127.0.0.1:5173/api/v1/` | Session-authenticated API proxy |
| Django admin | `http://127.0.0.1:8000/admin/` | Optional Django admin; requires a configured staff/superuser account |
| Cloud API base (hybrid only) | `http://127.0.0.1:8001/api/v1/` | Direct API used by the Cloud frontend on port 5174 |

The application is not currently a route-per-screen SPA. After login, use the visible navigation buttons; the address remains `/`.

## Browser-visible pages and states

| Page/state | Browser URL | Allowed role | Purpose and expected content | How to reach it |
|---|---|---|---|---|
| Login | `/` | Anonymous | Username/password form and session error states | Open the frontend URL while signed out |
| Overview | `/` | Owner/admin/teacher/invigilator | Real student, exam and attempt metrics plus Cloud continuity status | Sign in as staff; choose **Overview** |
| Exams / Exam Studio | `/` | Owner/admin/teacher/invigilator | Create a draft, section and questions; publish and assign | Staff navigation → **Exams** |
| Students | `/` | Owner/admin/teacher/invigilator | Organization-scoped roster and student provisioning form | Staff navigation → **Students** |
| Results | `/` | Owner/admin/teacher/invigilator | Attempt list, filters and **Review attempt** action | Staff navigation → **Results** |
| Attempt review | `/` | Owner/admin/teacher/invigilator | Persisted summary and question-by-question staff review | Results → **Review attempt** |
| My exams | `/` | Student | Assigned published exams, duration, question count and start/resume state | Sign in as student; default screen |
| Current attempt | `/` | Student | Real questions, server deadline timer, answer save state and submit | My exams → **Start exam** or **Resume attempt** |
| Student results | `/` | Student | Server-generated score and counts after submission | Student navigation → **Results** |
| Sync status | `/` | Owner/admin/teacher/invigilator | Node identity, pending/failed/conflict/delivered event counts and last successful sync | Staff **Overview** → Cloud connection panel |

No separate `/dashboard`, `/students`, `/results`, or `/exam/:id` paths are implemented today.

## Backend and API reference

All paths below are relative to `http://127.0.0.1:8000/api/v1/` in a direct backend setup, or to `http://127.0.0.1:5173/api/v1/` when using the standard Vite proxy. Session endpoints use Django cookies and CSRF for unsafe methods.

### Authentication and status

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/health/` | Public | Backend health response |
| GET | `/auth/csrf/` | Public | Obtain the CSRF token used by the client |
| POST | `/auth/login/` | Public | Create a Django session and return the authenticated user |
| POST | `/auth/logout/` | Authenticated | End the Django session |
| GET | `/me/` | Authenticated | Restore the current user, organization and role |

### Staff resources

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/students/` | Staff, organization-scoped | List students |
| POST | `/students/provision/` | Staff, organization-scoped | Create a linked student login/profile; password is write-only |
| GET | `/organizations/` | Authenticated organization member | Read the current organization record |
| GET | `/users/` | Staff, organization-scoped | Read organization users where permitted |
| GET/POST | `/subjects/` | Staff, organization-scoped | List or create subjects |
| GET/POST | `/questions/` | Staff, organization-scoped | List or create question-bank questions |
| GET/POST | `/exams/` | Staff, organization-scoped | List or create exams |
| GET/PATCH | `/exams/{id}/` | Staff, organization-scoped | Reopen or update an exam while permitted |
| POST | `/sections/` | Staff, organization-scoped | Create an exam section |
| POST | `/exam-questions/` | Staff, organization-scoped | Attach a question to a section |
| POST | `/exams/{id}/publish/` | Staff, organization-scoped | Publish a valid exam |
| POST | `/exams/{id}/assign/` | Staff, same organization | Assign a published exam to a student |
| GET | `/attempts/` | Staff, organization-scoped | List attempts/results for staff review |
| GET | `/attempts/{id}/review/` | Staff, same organization | Question-level review of an attempt |
| GET | `/sync/status/` | Staff, node-local | Read real outbox and upstream status |

### Student attempt resources

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/exams/` | Student | List only assigned, published exams; answer keys and marking internals are redacted |
| GET | `/attempts/` | Student | List the student's own attempts and restore state |
| POST | `/attempts/start/` | Student | Start or resume an assigned attempt; send an `Idempotency-Key` header |
| PUT | `/attempts/{id}/answer/` | Student, own in-progress attempt | Persist one answer |
| POST | `/attempts/{id}/submit/` | Student, own attempt | Submit once and let Django score the attempt |
| GET | `/attempts/{id}/review/` | Staff only | Students must not call the staff review endpoint |

### Server-to-server sync

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/sync/push/` | LAN/Cloud node authentication via `X-Haptric-Sync-Token`; never browser-facing | Ingest a supported sync event envelope idempotently |
| GET | `/sync/pull/` | Authenticated non-student staff | Read organization-scoped outbox events; the demo uses the bounded server-side push command instead |

Never place `HAPTRIC_SYNC_TOKEN` in React, a browser request, a screenshot, or a committed file.

## Disposable demo accounts and data

The existing seed workflow creates the following values in both demo databases. It does not store or print the password.

| Item | Seeded value |
|---|---|
| Organization | `Haptric Hybrid Demo` |
| Staff username | `demo-staff` |
| Student username | `demo-student` |
| Student ID | `HYBRID-001` |
| Exam | `Hybrid Demo Exam` |
| Exam duration | 10 minutes |
| Questions | 3 synthetic questions |
| Assignment | Student is assigned to the published exam |

Set the disposable password only in the current PowerShell process:

```powershell
$env:HAPTRIC_DEMO_PASSWORD = 'choose-a-local-only-password'
```

The password source is the environment variable `HAPTRIC_DEMO_PASSWORD`. Do not put the value in Git, documentation, browser storage, or a report. The hybrid scripts also require a local-only `$env:HAPTRIC_SYNC_TOKEN`; it is never displayed by the scripts.

## Simple product walkthrough

This is the easiest way to test the product without first demonstrating an outage. It uses the LAN demo database and the normal Vite proxy.

1. From the repository root, set `HAPTRIC_DEMO_PASSWORD` and run `tools\demo\setup-hybrid-demo.ps1`.
2. Run `tools\demo\seed-hybrid-demo.ps1`.
3. In a new terminal, set the same `HAPTRIC_SYNC_TOKEN` required by the LAN script and run `tools\demo\start-lan.ps1`.
4. In another terminal, start the frontend using the Quick start command on port 5173.
5. Open `http://127.0.0.1:5173/` and sign in as `demo-staff`.
6. Inspect Overview, Students, Exams, and Results. The dashboard metrics and seeded records come from the LAN Django database.
7. Sign out, sign in as `demo-student`, open **My exams**, start **Hybrid Demo Exam**, answer the synthetic questions, submit, and open **Results**.
8. Sign out, sign back in as `demo-staff`, open **Results**, select the submitted attempt, and review the persisted responses and marks.

## Hybrid LAN + Cloud test

This demonstration uses two Django processes, two React dev servers, and two SQLite databases. “Offline” means the student browser can still reach the LAN node while the upstream Cloud node is stopped; it does not mean browser-offline/PWA operation.

Before starting, use a fresh PowerShell session and set both values:

```powershell
$env:HAPTRIC_DEMO_PASSWORD = 'choose-a-local-only-password'
$env:HAPTRIC_SYNC_TOKEN = 'choose-a-local-only-token'
.\tools\demo\setup-hybrid-demo.ps1
.\tools\demo\seed-hybrid-demo.ps1
.\tools\demo\hybrid-demo-check.ps1
```

Use this terminal layout:

| Terminal | Command | Result |
|---|---|---|
| 1 — Cloud Django | `$env:HAPTRIC_SYNC_TOKEN = 'same-local-only-token'; .\tools\demo\start-cloud.ps1` | Cloud backend `http://127.0.0.1:8001` using `.demo-hybrid\cloud.sqlite3` |
| 2 — LAN Django | `$env:HAPTRIC_SYNC_TOKEN = 'same-local-only-token'; .\tools\demo\start-lan.ps1` | LAN backend `http://127.0.0.1:8000` using `.demo-hybrid\lan.sqlite3` |
| 3 — LAN React | `Set-Location frontend; Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue; npm run dev -- --host 127.0.0.1 --port 5173` | LAN frontend `http://127.0.0.1:5173/`, proxied to port 8000 |
| 4 — Cloud React | `Set-Location frontend; $env:VITE_API_BASE_URL='http://127.0.0.1:8001/api/v1'; npm run dev -- --host 127.0.0.1 --port 5174` | Cloud frontend `http://127.0.0.1:5174/`, direct to port 8001 |
| 5 — Sync/control | `.\tools\demo\sync-lan.ps1` | Bounded LAN → Cloud push; token stays server-side |

Sequence:

1. Open LAN frontend, sign in as `demo-staff`, and confirm the seeded exam/student.
2. Sign in as `demo-student` in the LAN frontend, start the assigned exam, and answer questions.
3. Stop the Cloud Django terminal only. The LAN student can continue and submit because the LAN database is authoritative for this local attempt.
4. Return to the LAN staff view and refresh the Cloud connection panel. Pending events should remain visible; the local result remains available.
5. Restart Cloud Django. Run `.\tools\demo\sync-lan.ps1` from the control terminal.
6. Open Cloud frontend `http://127.0.0.1:5174/`, sign in as `demo-staff`, open Results → Review attempt, and confirm the synchronized result.
7. Run `.\tools\demo\sync-lan.ps1` again. Reopening Cloud Results must not create a duplicate attempt, answer, or result.

Use `.\tools\demo\hybrid-demo-check.ps1` before presenting to verify both known databases and aligned reference IDs. Use [docs/HACKATHON_DEMO.md](HACKATHON_DEMO.md) for the timed judge script.

## Role capability matrix

The current application has `owner`, `admin`, `teacher`, `invigilator`, and `student` roles. A separate platform-wide admin role is not implemented; “Platform Admin” is therefore marked unsupported rather than inferred.

| Feature | Platform Admin | Institute Admin / Owner | Teacher / Invigilator | Student |
|---|---|---|---|---|
| Sign in and view own organization | Not implemented | Yes | Yes | Yes |
| Dashboard / sync status | Not implemented | Yes | Yes (staff-scoped) | No |
| Student list/provisioning | Not implemented | Yes | Yes (staff permission) | No |
| Exam authoring/publishing/assignment | Not implemented | Yes | Yes (staff permission) | No |
| Assigned exam discovery | Not implemented | Staff may see staff data, not student exam workflow | Staff may see staff data, not student exam workflow | Yes, assigned published exams only |
| Start/save/submit attempt | Not implemented | Only when using a student account | Only when using a student account | Yes, own attempt only |
| Results list and attempt review | Not implemented | Yes, same-organization attempts | Yes, same-organization attempts | Own result only; no staff review |
| Sync ingestion | Not implemented | Server-to-server only; not a browser action | Server-to-server only; not a browser action | No |

## Expected seeded test data

The seed creates one published 10-minute exam with one section and exactly three synthetic single-choice questions. The student `HYBRID-001` is assigned before the walkthrough starts. Question prompts and answer keys are intentionally omitted from this main guide; the student path should be tested without relying on answer-key disclosure.

## Troubleshooting and reset

For port conflicts, migration/CORS/CSRF issues, missing sync tokens, reference-ID drift, pending sync failures, or stale sessions, use [docs/DEMO_RECOVERY.md](DEMO_RECOVERY.md). It contains symptoms, fast diagnosis, and safe recovery steps.

To reset only the disposable hybrid demo databases:

```powershell
.\tools\demo\reset-hybrid-demo.ps1
```

The script deletes only `.demo-hybrid\lan.sqlite3` and `.demo-hybrid\cloud.sqlite3` after validating that the directory contains no unexpected files. It does not delete a generic database, source file, or production data. Run setup and seed again after reset.

## Verification notes

The documented URLs and scripts are derived from the current `main` source and the `tools/demo` PowerShell scripts. The standard setup uses the Vite proxy; direct Cloud browser access uses the explicit `VITE_API_BASE_URL` and the Cloud script’s allow-listed origin. Docker/PostgreSQL are not required for this local guide and are not claimed as verified by the SQLite two-node demo.
