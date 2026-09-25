#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

start_service() {
  local name="$1"
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start "$name" 2>/dev/null || true
  fi
  sudo service "$name" start 2>/dev/null || true
}

start_service postgresql
start_service redis-server

for _ in $(seq 1 30); do
  if redis-cli ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'mission_control'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE mission_control;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" >/dev/null 2>&1 || true

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

cd backend
AUTH_MODE="${AUTH_MODE:-local}" \
LOCAL_AUTH_TOKEN="${LOCAL_AUTH_TOKEN:-openclaw_local_dev_token_very_secure_key_for_mission_control_2026}" \
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/mission_control" \
uv run alembic upgrade head
