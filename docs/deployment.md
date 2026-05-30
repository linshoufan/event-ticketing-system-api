# Deployment Guide

This repository now covers the backend deployment only. The frontend has been moved to a separate repository.

## 1. Backend deployment

The backend lives in [backend/](../backend) and is deployed and started as one backend unit.

In local development, start the backend from the repo's backend entrypoints and let the backend code handle its internal modules under `backend/account`, `backend/event`, and `backend/transaction`.

The backend unit is responsible for authentication, event data, and transaction workflows as part of the same runtime deployment.

## 2. Environment separation

Backend needs:

- database connection settings
- JWT and internal API secrets
- internal service URLs if the backend code calls them at runtime

## 3. Local development mapping

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

## 4. Deployment rule of thumb

If a change only affects backend code, redeploy the backend unit.

If a shared contract changes with the separate frontend repo, redeploy the affected frontend and backend units together.