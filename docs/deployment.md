# Deployment Guide

This repository now covers the backend deployment only. The frontend has been moved to a separate repository.

## 1. Backend deployment

The backend lives in [backend/](../backend) and is deployed and started as one backend unit.

In local development, start the backend from the repo's backend entrypoints and let the backend code handle its internal modules under `backend/account`, `backend/event`, `backend/transaction`, and `backend/ticket`.

The backend unit is responsible for authentication, event data, transaction workflows, and ticket management.

## 2. Environment separation

Backend needs:

- database connection settings
- JWT and internal API secrets
- internal service URLs for cross-service calls

## 3. Local development mapping

### 3.1 Start Databases

Start the local databases from the repo root:

```bash
docker compose up -d
```
This will start:
- `account-db` (Port 5433)
- `event-db` (Port 5432)
- `transaction-db` (Port 5434)
- `ticket-db` (Port 5435)

### 3.2 Initialize Data (Optional)

Run the global seed script to populate mock data for all services (Users, Events, Transactions, Tickets):

```bash
# From root directory
python scripts/seed_all.py
```

### 3.3 Start Services

- **Account Service** (Port 8000):
  `cd backend/account && uvicorn main:app --reload --port 8000`
- **Event Service** (Port 3000):
  `cd backend/event && npm install && npm run dev`
- **Transaction Service** (Port 8002):
  `cd backend/transaction && uvicorn main:app --reload --port 8002`
- **Ticket Service** (Port 8001):
  `cd backend/ticket && uvicorn main:app --reload --port 8001`

Note: Ensure all services share the same `JWT_SECRET_KEY` and `INTERNAL_API_KEY` in their respective `.env` files.

## 4. Deployment rule of thumb

If a change only affects backend code, redeploy the backend unit.

If a shared contract changes with the separate frontend repo, redeploy the affected frontend and backend units together.
