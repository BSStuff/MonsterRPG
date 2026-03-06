#!/usr/bin/env bash
# start.sh -- Run Alembic migrations then start uvicorn.
# Used as the entrypoint for production deployments (Render, Docker).
set -euo pipefail

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting uvicorn..."
exec uv run uvicorn elements_rpg.api.app:create_app \
    --factory \
    --host 0.0.0.0 \
    --port "${ELEMENTS_PORT:-8000}"
