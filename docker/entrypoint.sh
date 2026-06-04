#!/bin/sh
set -eu

SERVICE="${SERVICE:-}"

if [ -z "$SERVICE" ]; then
  echo "SERVICE must be set to one of: account, event, transaction, ticket" >&2
  exit 1
fi

case "$SERVICE" in
  account|event|transaction|ticket)
    cd "/app/backend/$SERVICE"
    ;;
  *)
    echo "Unsupported SERVICE: $SERVICE" >&2
    echo "SERVICE must be one of: account, event, transaction, ticket" >&2
    exit 1
    ;;
esac

alembic upgrade head

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
