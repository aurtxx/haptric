# Local LAN and cloud operations

## Windows PowerShell (LAN development)

```powershell
Copy-Item infra/.env.example infra/.env
# Edit infra/.env and replace the development placeholders.
docker compose --env-file infra/.env -f infra/docker-compose.yml up --build
```

The development UI is exposed at `http://localhost:5173` and the API at `http://localhost:8000`. PostgreSQL is exposed on the configured local port for tooling. Do not expose these development ports directly to the internet.

Useful checks:

```powershell
docker compose --env-file infra/.env -f infra/docker-compose.yml ps
docker compose --env-file infra/.env -f infra/docker-compose.yml logs --tail=100 backend
docker compose --env-file infra/.env -f infra/docker-compose.yml exec backend python manage.py check
docker compose --env-file infra/.env -f infra/docker-compose.yml down
```

The compose file expects the backend to provide `/health/` and the frontend to provide `npm run dev`. It runs migrations on backend startup; production deployments must run migrations as an explicit release step instead.

## Deployment modes

- `DEPLOYMENT_MODE=lan`: a single managed node, local PostgreSQL, local media and a durable sync outbox. The exam server remains authoritative during an offline exam window.
- `DEPLOYMENT_MODE=cloud`: stateless API/frontend containers, managed PostgreSQL, private object storage and a worker for bounded sync batches. Set secrets through the deployment secret store, not `.env` committed to the repository.

The same API contract is used in both modes. `INSTALLATION_ID` identifies a LAN node for sync envelopes; it is not an authentication secret.

## Backup and rollback guardrails

1. Take an encrypted database/media backup before migrations or upgrades.
2. Run migrations as a release step and verify `/health/` before serving traffic.
3. Roll back the application image only when migrations are backward compatible; never delete exam attempts or audit events to recover from a failed release.
4. Test restore on a separate node before calling a backup usable.

The compose setup is intentionally a development baseline. TLS termination, managed secrets, object storage and worker scaling require environment-specific configuration and manual review.
