#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  # Local auth token (50+ chars) for AUTH_MODE=local development.
  sed -i 's/^LOCAL_AUTH_TOKEN=.*/LOCAL_AUTH_TOKEN=openclaw_local_dev_token_very_secure_key_for_mission_control_2026/' .env
  sed -i 's/^DB_AUTO_MIGRATE=.*/DB_AUTO_MIGRATE=false/' .env
fi

make setup

# Async Postgres driver for the FastAPI async session layer (see AGENTS.md).
cd backend && uv pip install asyncpg
