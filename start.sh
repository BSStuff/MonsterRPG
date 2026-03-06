#!/bin/sh
set -e

# Run database migrations
uv run alembic upgrade head

# Start the application server
exec uv run uvicorn elements_rpg.api.app:create_app --factory --host 0.0.0.0 --port "${ELEMENTS_PORT:-8000}"
