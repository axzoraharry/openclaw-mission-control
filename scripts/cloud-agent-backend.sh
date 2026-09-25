#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT/backend"

export PATH="${HOME}/.local/bin:${PATH}"

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

export AUTH_MODE="${AUTH_MODE:-local}"
export LOCAL_AUTH_TOKEN="${LOCAL_AUTH_TOKEN:-openclaw_local_dev_token_very_secure_key_for_mission_control_2026}"
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/mission_control"
# Migrations run in cloud-agent-start.sh; auto-migrate on API boot breaks with asyncpg URLs.
export DB_AUTO_MIGRATE=false
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export RQ_REDIS_URL="${RQ_REDIS_URL:-redis://localhost:6379/0}"

exec uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
