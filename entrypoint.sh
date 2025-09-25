#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}/${DB_NAME} ..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

echo "Applying migrations (if any)..."
poetry run flask db upgrade || true

echo "Starting Flask dev server..."
exec poetry run flask run --host=0.0.0.0 --port=5000 --debug
