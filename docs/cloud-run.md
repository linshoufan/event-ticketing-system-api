# Cloud Run Deployment

This project should be deployed as four Cloud Run services running at the same time:

- `account-service`
- `event-service`
- `transaction-service`
- `ticket-service`

Cloud Run runs one ingress container per service. The local PostgreSQL containers from `docker-compose.yaml` should not be deployed to Cloud Run; use Cloud SQL for PostgreSQL instead.

## Container Runtime

The shared `Dockerfile` builds the same image shape for every backend service. At runtime, set `SERVICE` to choose which FastAPI app to start.

Cloud Run provides `PORT` automatically. The container entrypoint starts:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

## Build Images

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
    --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE:latest" \
    .
done
```

## Cloud SQL

Create Cloud SQL PostgreSQL databases for:

- `account_db`
- `event_db`
- `transaction_db`
- `ticket_db`

The app uses Unix socket connections when `ENV=production`. Set each service's `*_DB_HOST` to:

```text
/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
```

Example for account:

```bash
ACCOUNT_DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
ACCOUNT_DB_PORT=5432
ACCOUNT_DB_USER=postgres
ACCOUNT_DB_PASSWORD=...
ACCOUNT_DB_NAME=account_db
EMPLOYEE_AUTH_MODE=database
EMPLOYEE_DB_HOST=/cloudsql/PROJECT_ID:REGION:EMPLOYEE_INSTANCE_NAME
EMPLOYEE_DB_PORT=5432
EMPLOYEE_DB_USER=postgres
EMPLOYEE_DB_PASSWORD=...
EMPLOYEE_DB_NAME=employee_db
ENV=production
```

## Deploy Services

Deploy each service with its own env vars and the same shared secrets.

```bash
gcloud run deploy account-service \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/account:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --add-cloudsql-instances "PROJECT_ID:REGION:INSTANCE_NAME" \
  --set-env-vars "SERVICE=account,ENV=production,EMPLOYEE_AUTH_MODE=database,ACCOUNT_DB_HOST=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME,ACCOUNT_DB_PORT=5432,ACCOUNT_DB_USER=postgres,ACCOUNT_DB_PASSWORD=CHANGE_ME,ACCOUNT_DB_NAME=account_db,EMPLOYEE_DB_HOST=/cloudsql/PROJECT_ID:REGION:EMPLOYEE_INSTANCE_NAME,EMPLOYEE_DB_PORT=5432,EMPLOYEE_DB_USER=postgres,EMPLOYEE_DB_PASSWORD=CHANGE_ME,EMPLOYEE_DB_NAME=employee_db,JWT_SECRET_KEY=CHANGE_ME,JWT_ALGORITHM=HS256,INTERNAL_API_KEY=CHANGE_ME"
```

Repeat for the other services with their matching image and DB variables:

- `SERVICE=event`, `EVENT_DB_*`
- `SERVICE=transaction`, `TRANSACTION_DB_*`
- `SERVICE=ticket`, `TICKET_DB_*`

After deployment, update cross-service URLs:

- `TRANSACTION_SERVICE_URL` is not currently needed by other services.
- `ACCOUNT_SERVICE_URL=https://account-service-...run.app`
- `EVENT_SERVICE_URL=https://event-service-...run.app`
- `TICKET_SERVICE_URL=https://ticket-service-...run.app`

Set those on the services that call each other:

```bash
gcloud run services update event-service \
  --region "$REGION" \
  --update-env-vars "TICKET_SERVICE_URL=https://ticket-service-...run.app"

gcloud run services update transaction-service \
  --region "$REGION" \
  --update-env-vars "ACCOUNT_SERVICE_URL=https://account-service-...run.app,EVENT_SERVICE_URL=https://event-service-...run.app,TICKET_SERVICE_URL=https://ticket-service-...run.app"

gcloud run services update ticket-service \
  --region "$REGION" \
  --update-env-vars "ACCOUNT_SERVICE_URL=https://account-service-...run.app,EVENT_SERVICE_URL=https://event-service-...run.app"
```

## Migrations And Seed Data

Run migrations from a trusted environment that can connect to Cloud SQL. Do not run migrations automatically in every Cloud Run container startup.

For local initialization:

```bash
python scripts/migrate_all.py --seed
```

For production, run each service's Alembic migration with production environment variables set, or create a separate Cloud Run Job for migrations.

## Notes

- Keep `JWT_SECRET_KEY` identical across services.
- Keep `INTERNAL_API_KEY` identical across services that make internal calls.
- Prefer Secret Manager for passwords and keys instead of inline `--set-env-vars`.
- If services should not be public, remove `--allow-unauthenticated` and grant Cloud Run invoker permissions only to the frontend or calling service accounts.

## References

- Cloud Run container runtime contract: <https://docs.cloud.google.com/run/docs/container-contract>
- `gcloud run deploy`: <https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy>
- Cloud Run to Cloud SQL for PostgreSQL: <https://docs.cloud.google.com/sql/docs/postgres/connect-run>
