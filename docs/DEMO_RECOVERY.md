# Demo recovery guide

Use these fixes only for the disposable local demo. Do not point reset commands at a production database.

| Symptom | Fast diagnosis | Safe recovery |
|---|---|---|
| LAN will not start | Port 8000 is occupied or `.demo-hybrid/lan.sqlite3` is missing | Stop the process using port 8000; rerun setup and seed; start LAN again. |
| Cloud will not start | Port 8001 is occupied or Cloud DB is missing | Stop the process using port 8001; rerun setup and seed; start Cloud again. |
| Frontend port occupied | Vite cannot bind 5173/5174 | Stop the old Vite process or choose a new port and update the matching CORS/CSRF origin. |
| Migration error | Wrong working directory or stale disposable DB | Run commands from the repository root; for the demo only, run `reset-hybrid-demo.ps1`, then setup and seed again. |
| Wrong environment | `DATABASE_NAME` or node variables point elsewhere | Open a fresh PowerShell session and use the demo scripts, which set node-local values explicitly. |
| CORS error | Cloud frontend origin is not allow-listed | Set Cloud `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to the exact frontend origin, such as `http://127.0.0.1:5174`, then restart Cloud. |
| CSRF error | Origin changed or a stale browser session is open | Use the exact configured origin, close the tab, reopen the frontend, and sign in again. Never disable CSRF. |
| Sync token missing | `sync-lan.ps1` reports a missing token | Set `HAPTRIC_SYNC_TOKEN` in the current LAN terminal only; never put it in React or commit it. |
| Reference IDs not aligned | Health check fails | Rerun setup and seed for both disposable databases; do not manually edit production records. |
| Pending events do not sync | Cloud is still unavailable or LAN URL/token is wrong | Check Cloud health, `HAPTRIC_SYNC_URL`, and the token; rerun the command. Failed events are retained for retry. |
| Browser session stale | Login or results appear inconsistent | Refresh once; if necessary sign out and sign in again. Do not clear or export cookies for the demo. |

After a failed rehearsal, collect the visible error and command output, fix the local setup, and rerun the health check before presenting.
