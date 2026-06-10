# Deployment Guide

This repository covers backend services only. The frontend is deployed from a separate repository.

The backend is split into four services:

- `account`
- `event`
- `transaction`
- `ticket`

Each service owns its own API, database settings, and runtime environment. In Cloud Run, deploy them as four separate services. In local development, use Docker Compose or run each service with `uvicorn`.

## 1. Local Development

### 1.1 Install Dependencies

Install the required Python packages for all backend services:

```bash
# From root directory
pip install -r requirements.txt
```

### 1.2 Start The Local Stack

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

### 1.3 Initialize Data (Optional)

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

### 1.4 Start Services

- **Account Service** (Port 8000):
  `cd backend/account && uvicorn main:app --reload --port 8000`
- **Event Service** (Port 8003):
  `cd backend/event && uvicorn app.main:app --reload --port 8003`
- **Transaction Service** (Port 8002):
  `cd backend/transaction && uvicorn main:app --reload --port 8002`
- **Ticket Service** (Port 8001):
  `cd backend/ticket && uvicorn main:app --reload --port 8001`

Note: Ensure all services share the same `JWT_SECRET_KEY` and `INTERNAL_API_KEY` in their respective `.env` files.

### 1.5 Troubleshooting & Data Persistence

1. **Volume Persistence**: Using `docker compose down -v` will **delete all persistent database volumes**. If you do this, run migrations and `python scripts/seed_all.py` manually to repopulate your data.
2. **Local Execution Sync**: If you run services locally via `uvicorn` (outside Docker) but connect to Docker-hosted databases:
   - When the Docker database is reset or cleared, you must manually run the seed script from your host machine:
     ```bash
     python scripts/seed_all.py
     ```
   - Ensure your host environment has all dependencies installed (`pip install -r requirements.txt`).

## 2. Cloud Run Deployment

Cloud Run should run the API services as separate services:

- `account-service`
- `event-service`
- `transaction-service`
- `ticket-service`

The local PostgreSQL containers from `docker-compose.yaml` should not be deployed to Cloud Run. Use Cloud SQL for PostgreSQL instead.

### 2.1 Container Runtime

The shared `Dockerfile` builds the same image shape for every backend service. At runtime, set `SERVICE` to choose which FastAPI app starts.

Cloud Run provides `PORT` automatically. The container entrypoint starts:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

### 2.2 Build Images

Replace these values first:

```bash
PROJECT_ID=your-project-id
REGION=asia-east1
REPOSITORY=event-ticketing
```

Create an Artifact Registry repository once:

```bash
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION"
```

Build and push one image tag per service:

```bash
for SERVICE in account event transaction ticket; do
  gcloud builds submit \
    --region "$REGION" \
    --default-buckets-behavior=regional-user-owned-bucket \
    --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE:latest" \
    .
done
```

If your project requires a user-specified Cloud Build service account, include it on the same command:

```bash
BUILD_SERVICE_ACCOUNT=cloud-build-deployer@$PROJECT_ID.iam.gserviceaccount.com

for SERVICE in account event transaction ticket; do
  gcloud builds submit \
    --region "$REGION" \
    --service-account "$BUILD_SERVICE_ACCOUNT" \
    --default-buckets-behavior=regional-user-owned-bucket \
    --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE:latest" \
    .
done
```

### 2.3 Cloud SQL

Create Cloud SQL PostgreSQL databases for:

- `account_db`
- `employee_db`
- `event_db`
- `transaction_db`
- `ticket_db`

The app uses Unix socket connections when `ENV=production`. Set each service's `*_DB_HOST` to:

```text
/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

If account users and employee auth data are in the same Cloud SQL instance, use the same instance connection name for both `ACCOUNT_DB_HOST` and `EMPLOYEE_DB_HOST`, but set different database names:

```bash
ACCOUNT_INSTANCE=PROJECT_ID:REGION:ACCOUNT_INSTANCE_NAME

ACCOUNT_DB_HOST=/cloudsql/$ACCOUNT_INSTANCE
ACCOUNT_DB_NAME=account_db
EMPLOYEE_DB_HOST=/cloudsql/$ACCOUNT_INSTANCE
EMPLOYEE_DB_NAME=employee_db
```

If employee auth data is in a separate Cloud SQL instance, attach both instances to `account-service` and point `EMPLOYEE_DB_HOST` at the employee instance.

### 2.4 Deploy Services

Deploy each service with its own env vars and the same shared secrets.

Account service, same Cloud SQL instance for `account_db` and `employee_db`:

```bash
ACCOUNT_INSTANCE=PROJECT_ID:REGION:ACCOUNT_INSTANCE_NAME

gcloud run deploy account-service \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/account:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --add-cloudsql-instances "$ACCOUNT_INSTANCE" \
  --set-env-vars "SERVICE=account,ENV=production,EMPLOYEE_AUTH_MODE=database,ACCOUNT_DB_HOST=/cloudsql/$ACCOUNT_INSTANCE,ACCOUNT_DB_PORT=5432,ACCOUNT_DB_USER=postgres,ACCOUNT_DB_PASSWORD=CHANGE_ME,ACCOUNT_DB_NAME=account_db,EMPLOYEE_DB_HOST=/cloudsql/$ACCOUNT_INSTANCE,EMPLOYEE_DB_PORT=5432,EMPLOYEE_DB_USER=postgres,EMPLOYEE_DB_PASSWORD=CHANGE_ME,EMPLOYEE_DB_NAME=employee_db,JWT_SECRET_KEY=CHANGE_ME,JWT_ALGORITHM=HS256,INTERNAL_API_KEY=CHANGE_ME"
```

Account service, separate employee Cloud SQL instance:

```bash
ACCOUNT_INSTANCE=PROJECT_ID:REGION:ACCOUNT_INSTANCE_NAME
EMPLOYEE_INSTANCE=PROJECT_ID:REGION:EMPLOYEE_INSTANCE_NAME

gcloud run deploy account-service \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/account:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --add-cloudsql-instances "$ACCOUNT_INSTANCE,$EMPLOYEE_INSTANCE" \
  --set-env-vars "SERVICE=account,ENV=production,EMPLOYEE_AUTH_MODE=database,ACCOUNT_DB_HOST=/cloudsql/$ACCOUNT_INSTANCE,ACCOUNT_DB_PORT=5432,ACCOUNT_DB_USER=postgres,ACCOUNT_DB_PASSWORD=CHANGE_ME,ACCOUNT_DB_NAME=account_db,EMPLOYEE_DB_HOST=/cloudsql/$EMPLOYEE_INSTANCE,EMPLOYEE_DB_PORT=5432,EMPLOYEE_DB_USER=postgres,EMPLOYEE_DB_PASSWORD=CHANGE_ME,EMPLOYEE_DB_NAME=employee_db,JWT_SECRET_KEY=CHANGE_ME,JWT_ALGORITHM=HS256,INTERNAL_API_KEY=CHANGE_ME"
```

Repeat for the other services with their matching image and DB variables:

- `SERVICE=event`, `EVENT_DB_*`
- `SERVICE=transaction`, `TRANSACTION_DB_*`
- `SERVICE=ticket`, `TICKET_DB_*`

Cloud Run runtime service accounts need `roles/cloudsql.client` to connect to Cloud SQL.

### 2.5 Cross-Service URLs

After deployment, update cross-service URLs:

- `ACCOUNT_SERVICE_URL=https://account-service-...run.app`
- `EVENT_SERVICE_URL=https://event-service-...run.app`
- `TICKET_SERVICE_URL=https://ticket-service-...run.app`

Set those on the services that call each other:

```bash
gcloud run services update transaction-service \
  --region "$REGION" \
  --update-env-vars "ACCOUNT_SERVICE_URL=https://account-service-...run.app,EVENT_SERVICE_URL=https://event-service-...run.app,TICKET_SERVICE_URL=https://ticket-service-...run.app"

gcloud run services update ticket-service \
  --region "$REGION" \
  --update-env-vars "ACCOUNT_SERVICE_URL=https://account-service-...run.app,EVENT_SERVICE_URL=https://event-service-...run.app"
```

### 2.6 CORS

Each public service supports CORS through these env vars:

```text
CORS_ORIGINS=https://event-ticketing-system-frontend-eight.vercel.app
CORS_METHODS=GET,POST,PATCH,DELETE,OPTIONS
CORS_HEADERS=Authorization,Content-Type,X-Internal-Key
```

In the Cloud Run Console UI, enter each variable as a separate row. Do not include CLI-only separators such as `@`.

When using `gcloud`, values that contain commas need a custom delimiter:

```bash
gcloud run services update event-service \
  --region "$REGION" \
  --update-env-vars "^@^CORS_ORIGINS=https://event-ticketing-system-frontend-eight.vercel.app@CORS_METHODS=GET,POST,PATCH,DELETE,OPTIONS@CORS_HEADERS=Authorization,Content-Type,X-Internal-Key"
```

Verify preflight against the actual Cloud Run URL:

```bash
EVENT_URL="$(gcloud run services describe event-service --region "$REGION" --format='value(status.url)')"

curl -i -X OPTIONS \
  "$EVENT_URL/v1/events" \
  -H "Origin: https://event-ticketing-system-frontend-eight.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type"
```

### 2.7 Migrations And Seed Data

Run migrations from a trusted environment that can connect to Cloud SQL. Do not run migrations automatically in every Cloud Run container startup.

For local initialization:

```bash
python scripts/migrate_all.py --seed
```

For production, run each service's Alembic migration with production environment variables set, or create a separate Cloud Run Job for migrations.

## 3. Deployment Notes

- Keep `JWT_SECRET_KEY` identical across services.
- Keep `INTERNAL_API_KEY` identical across services that make internal calls.
- Prefer Secret Manager for passwords and keys instead of inline `--set-env-vars`.
- If services should not be public, remove `--allow-unauthenticated` and grant Cloud Run invoker permissions only to the frontend or calling service accounts.
- If a change only affects one backend service, rebuild and redeploy only that service image.
- If a shared API contract changes, redeploy the affected backend service and the separate frontend together.

## 4. References

- Cloud Run container runtime contract: <https://docs.cloud.google.com/run/docs/container-contract>
- `gcloud run deploy`: <https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy>
- Cloud Run to Cloud SQL for PostgreSQL: <https://docs.cloud.google.com/sql/docs/postgres/connect-run>
