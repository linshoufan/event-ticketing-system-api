# Deployment Guide

This repository is structured as a monorepo, but the runtime deployment is split into an independent frontend unit and one backend unit.

## 1. Frontend deployment

The frontend lives in [frontend/](../frontend).

Build it independently:

```bash
cd frontend
npm install
npm run build
```

Set the production API endpoint with `VITE_API_BASE_URL` so the frontend talks to the deployed backend, not to itself.

Example production environment values:

```bash
VITE_API_BASE_URL=https://api.your-domain.com/v1
VITE_USE_MOCK=false
```

## 2. Backend deployment

The backend lives in [backend/](../backend) and is deployed and started as one backend unit.

In local development, start the backend from the repo's backend entrypoints and let the backend code handle its internal modules under `backend/account`, `backend/event`, and `backend/transaction`.

The backend unit is responsible for authentication, event data, and transaction workflows as part of the same runtime deployment.

## 3. Environment separation

Frontend and backend should not share the same runtime deployment unit.

Frontend needs:

- `VITE_API_BASE_URL`
- optional `VITE_USE_MOCK` for local development only

Backend needs:

- database connection settings
- JWT and internal API secrets
- internal service URLs if the backend code calls them at runtime

## 4. Local development mapping

- Frontend: `cd frontend && npm run dev`
- Backend local startup, current temporary workflow:
	- Account: `cd backend/account && pip install -r ../../requirements.txt && uvicorn app.main:app --reload --port 8000`
	- Event: `cd backend/event && npm install && npm run dev`
	- Transaction: `cd backend/transaction && pip install -r ../../requirements.txt && uvicorn app.main:app --reload --port 8002`

Start the local databases from the repo root:

```bash
docker compose up -d account-db event-db transaction-db
```

- Databases: use the top-level `docker-compose.yaml` for local PostgreSQL only (`account-db`, `event-db`, `transaction-db`)

This local backend startup flow is temporary and will be adjusted later once a unified backend launcher is added.

## 5. Deployment rule of thumb

If a change only affects the frontend bundle, redeploy the frontend only.

If a change only affects backend code, redeploy the backend unit.

If a shared contract changes, redeploy the affected frontend and backend unit together.