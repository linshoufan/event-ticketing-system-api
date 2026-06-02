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

### 3.2 Start Databases

To start only the local databases from the repo root, run:

```bash
docker compose up -d account-db event-db transaction-db ticket-db
```

This will start:
- `account-db` (Port 5433)
- `event-db` (Port 5432)
- `transaction-db` (Port 5434)
- `ticket-db` (Port 5435)

This command does **not** run `seed-data`, because it explicitly starts only the four database services.

If you run the full Compose stack instead:

```bash
docker compose up
```

or:

```bash
docker compose up -d
```

Compose includes the `seed-data` one-shot service. It runs once, applies migrations/seeding, then exits.

### 3.3 Initialize Data (Optional)

Run the one-shot seed service from the repo root to apply Python service migrations and populate mock data for all services:

```bash
docker compose run --rm seed-data
```

Use this command when you started only the DB services, when `seed-data` previously failed, or when you want to sync updated mock data into an existing local database.

The `seed-data` service runs:

- Account migrations
- Transaction migrations
- Ticket migrations
- `python scripts/seed_all.py`

By default, the seed script upserts the records in `scripts/mock_data.yaml` and does not clear existing data.

If you only need to sync mock data from the host machine after the databases are already migrated, you can run:

```bash
python scripts/seed_all.py
```

To explicitly reset the target mock tables first, run:

```bash
python scripts/seed_all.py --reset
```

Run seeding again when initializing a fresh environment, after deleting database volumes, or after changing `scripts/mock_data.yaml`.

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

1. **Volume Persistence**: Using `docker compose down -v` will **delete all persistent database volumes**. If you do this, you must wait for the `seed-data` service to finish or run it manually to repopulate your data.
2. **Seed Status Verification**: If data is missing (e.g., getting 404 for seeded records), check the status of the initialization container:
   ```bash
   docker ps -a --filter name=seed_data_init
   ```
   Look for `Exited (0)`. If it exited with a non-zero code, it means migrations or seeding failed.
3. **Local Execution Sync**: If you run services locally via `uvicorn` (outside Docker) but connect to Docker-hosted databases:
   - When the Docker database is reset or cleared, you must manually run the seed script from your host machine:
     ```bash
     python scripts/seed_all.py
     ```
   - Ensure your host environment has all dependencies installed (`pip install -r requirements.txt`).

## 4. Deployment rule of thumb

If a change only affects backend code, redeploy the backend unit.

If a shared contract changes with the separate frontend repo, redeploy the affected frontend and backend units together.
