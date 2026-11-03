# OpenExam — LAN-first examination platform

OpenExam is an independent, open-source exam workflow for schools and coaching communities. It provides a typed Django API and an original React interface, with explicit foundations for local LAN operation and safe cloud synchronization.

## Windows PowerShell quick start

Backend (terminal 1):

```powershell
py -3.12 -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt
.venv\\Scripts\\python.exe backend\\manage.py migrate
.venv\\Scripts\\python.exe backend\\manage.py runserver 127.0.0.1:8000
```

Frontend (terminal 2):

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/`. The current UI includes safe admin and student previews backed by a local mock adapter; the Django API contract is implemented and tested independently. No credentials are required for the preview controls.

## Docker Compose

Docker is optional and must be installed separately. Copy `infra/.env.example` to `infra/.env`, replace the development-only placeholders, then run:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml up --build
```

Compose runs PostgreSQL, Django migrations/API and Vite on the LAN-safe development ports documented in `infra/README.md`. Docker was unavailable in the current environment, so Compose runtime verification remains pending.

## Verification

```powershell
.venv\\Scripts\\python.exe -m pytest -q tests\\backend tests\\qa
Set-Location frontend
npm run lint
npm run test
npm run build
```

The research and design boundaries remain in `AGENTS.md` and `docs/AGENT_WORKFLOW.md`. Competitor observations in `docs/` are requirements research only; no EZExam branding, source, questions or protected assets are used.
