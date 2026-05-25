# Event Ticketing System API

API for a cloud-native ticketing system that enables streamlined, fair, and transparent corporate event registration.

This project currently uses a monolith backend structure. The backend code lives in `backend/`, and PostgreSQL is started with Docker Compose.

## Requirements

- Python 3.11
- Docker Desktop / Docker Engine
- Docker Compose v2

## Setup

Create the local Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Then review `.env` and adjust values if needed.

## Run Locally

Start PostgreSQL:

```bash
docker compose up -d account-db
```

Apply database migrations:

```bash
cd backend
../.venv/bin/alembic upgrade head
```

Start the backend:

```bash
../.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API root: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## Testing

Tests use `test_account_db`. If the test database does not exist yet, create it first:

```bash
docker compose exec -T account-db psql -U postgres -d postgres -c "CREATE DATABASE test_account_db;"
```

If the database already exists, this command will fail. That is fine; you can ignore it or verify the database with your preferred DB tool.

Run tests:

```bash
cd backend
../.venv/bin/pytest -q
```

Run lint:

```bash
cd backend
../.venv/bin/ruff check app tests
```

## Useful Commands

Check DB container status:

```bash
docker compose ps
```

Stop the DB:

```bash
docker compose down
```

If you previously started the old `ticket-db` service, remove unused orphan containers:

```bash
docker compose down --remove-orphans
docker compose up -d account-db
```
