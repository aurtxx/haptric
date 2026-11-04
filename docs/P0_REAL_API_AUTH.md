# P0.1 — Real API Boundary + Authentication

**Status:** Complete with documented mock boundaries
**Branch:** `feat/p0-real-api-auth`
**Scope:** React/Django communication and session authentication only. No exam lifecycle or LAN/cloud synchronization was implemented here.

## Architecture

The frontend now uses a single typed HTTP boundary in `frontend/src/api/httpApi.ts`. Components do not issue raw `fetch` calls. The client defaults to `/api/v1` and uses the Vite development proxy to forward `/api` and `/health` requests to Django at `http://127.0.0.1:8000`.

All requests use `credentials: "include"`, so Django's session cookie remains browser-managed and is never copied to localStorage. The client classifies authentication, validation, network, and server failures through `HttpApiError` and exposes sanitized user-facing messages.

## API endpoints used

- `GET /api/v1/auth/csrf/` — obtains Django's CSRF token and establishes the CSRF cookie.
- `POST /api/v1/auth/login/` — authenticates username/password and creates the Django session.
- `GET /api/v1/me/` — restores the current authenticated user after startup/login.
- `POST /api/v1/auth/logout/` — clears the Django session; protected by CSRF and POST-only handling.
- Typed foundation methods also exist for `GET /students/`, `GET /exams/`, and `GET /attempts/` for later milestones.

Backend auth errors now include stable codes (`authentication_failed`, `authentication_required`, `validation_error`, and `method_not_allowed`) and invalid credentials return HTTP 401. Logout requires a valid CSRF token.

## CSRF approach

The client lazily requests `/auth/csrf/` before every unsafe request and sends the returned token as `X-CSRFToken`. Django's CSRF middleware remains enabled; no `csrf_exempt` path or wildcard CORS was added. After login, the CSRF cache is cleared because Django rotates the token during session authentication. Credentialed CORS and trusted origins are scoped to configured development origins, while the preferred local path is same-origin Vite proxying.

## Session behavior

On app startup, Haptric displays `Checking session…` while calling `/me`. An anonymous 401 returns the login form; network/server failures remain visible as a recoverable `server unavailable` state. Login sends the entered values to Django, then calls `/me` and derives the UI role from the returned backend role. Refresh repeats `/me` and preserves the authenticated session through Django's HttpOnly cookie. Logout calls the real POST endpoint, clears local auth state, and a subsequent refresh remains logged out.

No passwords, session identifiers, cookies, CSRF values, or tokens are stored in localStorage or committed to the repository.

## Frontend changes

- Added typed `httpApi` and barrel export under `frontend/src/api/`.
- Added `AuthenticatedUser`, `Organization`, `ApiError`, `ValidationError`, and minimum API exam/student/attempt contracts in `frontend/src/types.ts`.
- Replaced the fake role-preview login path in `frontend/src/App.tsx` with real login, `/me` restoration, logout, loading, invalid-credential, and network/server error states.
- Removed Admin preview/Student preview controls from the authentication path.
- Displayed the authenticated username, backend role, and organization identifier.
- Added Vite proxy configuration for local Django connectivity.

## Backend changes

- Added structured auth error codes and JSON payload validation.
- Changed invalid credentials to HTTP 401 with a generic message.
- Restricted logout to POST and protected it with CSRF.
- Added scoped `CSRF_TRUSTED_ORIGINS` and credentialed CORS configuration for development origins.
- Extended API tests for anonymous `/me`, invalid login, organization identity, CSRF logout, session termination, and student question access/redaction.

## Tests and browser evidence

Executed from the repository:

- `.venv\\Scripts\\python.exe backend\\manage.py check` — PASS.
- `.venv\\Scripts\\python.exe -m pytest -q tests/backend tests/qa` — **10 passed, 4 skipped**. Skips require `QA_API_BASE_URL` and a separately running contract service.
- `npm run lint` in `frontend` — PASS.
- `npm run test -- --run` in `frontend` — **3 files, 11 tests passed**.
- `npm run build` in `frontend` — PASS.
- `git diff --check` — PASS.

Headed Playwright smoke used a synthetic local admin account and no captured secrets:

1. Logged-out page called `/api/v1/me/` and received 401.
2. Login called `/auth/csrf/`, `/auth/login/` (200), and `/me/` (200).
3. Authenticated workspace displayed the real username, role, and organization.
4. Browser refresh called `/me/` and preserved the session.
5. Sign out called `/auth/csrf/` and `/auth/logout/` (200).
6. Refresh after logout called `/me/` and remained logged out.
7. Wrong credentials displayed the recoverable invalid-credentials state.

## Remaining mock boundaries

`frontend/src/api/mockApi.ts` remains intentionally used for the existing demo exam, attempt timer, local answer state, and mock score. The dashboard metrics, roster, exam editor, and results view therefore remain demo data. This is the explicit Prompt 3 boundary; it is not evidence that the exam lifecycle is API-integrated.

## Known limitations

- No real exam CRUD, assignment, student provisioning, attempt persistence, server timer, or result retrieval is connected to React yet.
- The backend has no standalone result endpoint; later work must define that contract before UI integration.
- Docker/PostgreSQL and the skipped environment-backed QA checks remain unverified here.
- Existing development defaults still require production hardening before deployment.

## Local startup commands

From the repository root in Windows PowerShell:

```powershell
.venv\\Scripts\\python.exe backend\\manage.py migrate
.venv\\Scripts\\python.exe backend\\manage.py runserver 127.0.0.1:8000
```

In a second PowerShell window:

```powershell
Set-Location frontend
npm run dev -- --host 127.0.0.1
```

The Vite proxy forwards `/api/*` and `/health` to Django. Use a disposable local Django organization/user for smoke testing; do not place credentials in source, docs, `.env` files, or commits.
