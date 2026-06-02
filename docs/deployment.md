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

### 3.1 Install Dependencies

Install the required Python packages for all backend services:

```bash
# From root directory
pip install -r requirements.txt
```

### 3.2 Start The Local Stack

To start the local API services and databases from the repo root, run:

```bash
docker compose up -d --build
```

This will start:
- `account-api` (Port 8000)
- `event-api` (Port 8003)
- `transaction-api` (Port 8002)
- `ticket-api` (Port 8001)
- `account-db` (Port 5433)
- `employee-db` (Port 5436)
- `event-db` (Port 5432)
- `transaction-db` (Port 5434)
- `ticket-db` (Port 5435)

Docker Compose does not run migrations or seed data automatically.

If you only need the local databases because you want to run API services directly with `uvicorn`, start just the database services:

```bash
docker compose up -d account-db employee-db event-db transaction-db ticket-db
```

### 3.3 Initialize Data (Optional)

Apply Python service migrations manually from the repo root:

```bash
python scripts/migrate_all.py
```

Populate mock data manually after migrations:

```bash
python scripts/seed_all.py
```

To run migrations and seed mock data in one command:

```bash
python scripts/migrate_all.py --seed
```

To reset mock tables while seeding:

```bash
python scripts/migrate_all.py --reset-seed
```

By default, the seed script upserts the records in `scripts/mock_data.yaml` and does not clear existing data. To explicitly reset the target mock tables first, run:

```bash
python scripts/seed_all.py --reset
```

Run seeding again when initializing a fresh environment, after deleting database volumes, or after changing `scripts/mock_data.yaml`.

If you only need to sync updated mock data and migrations are already current, run only:

```bash
python scripts/seed_all.py
```

### 3.4 Start Services

- **Account Service** (Port 8000):
  `cd backend/account && uvicorn main:app --reload --port 8000`
- **Event Service** (Port 8003):
  `cd backend/event && uvicorn app.main:app --reload --port 8003`
- **Transaction Service** (Port 8002):
  `cd backend/transaction && uvicorn main:app --reload --port 8002`
- **Ticket Service** (Port 8001):
  `cd backend/ticket && uvicorn main:app --reload --port 8001`

Note: Ensure all services share the same `JWT_SECRET_KEY` and `INTERNAL_API_KEY` in their respective `.env` files.

### 3.5 Troubleshooting & Data Persistence

1. **Volume Persistence**: Using `docker compose down -v` will **delete all persistent database volumes**. If you do this, run migrations and `python scripts/seed_all.py` manually to repopulate your data.
2. **Local Execution Sync**: If you run services locally via `uvicorn` (outside Docker) but connect to Docker-hosted databases:
   - When the Docker database is reset or cleared, you must manually run the seed script from your host machine:
     ```bash
     python scripts/seed_all.py
     ```
   - Ensure your host environment has all dependencies installed (`pip install -r requirements.txt`).

## 4. Deployment rule of thumb

If a change only affects backend code, redeploy the backend unit.

If a shared contract changes with the separate frontend repo, redeploy the affected frontend and backend units together.

For containerized Google Cloud Run deployment, see [cloud-run.md](cloud-run.md). Cloud Run should run the API services as separate services and use Cloud SQL instead of the local Docker Compose database containers.
