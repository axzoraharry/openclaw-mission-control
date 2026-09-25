#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_ROOT/frontend"

export PATH="${HOME}/.local/bin:${PATH}"

# Prefer a recent Node 22.x (orval requires >=22.18).
if [[ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]]; then
  set +u
  # shellcheck disable=SC1090
  . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
  if [[ -f "$REPO_ROOT/frontend/.nvmrc" ]]; then
    nvm use --silent "$(tr -d ' \t\r\n' <"$REPO_ROOT/frontend/.nvmrc")" >/dev/null 2>&1 || true
  fi
  set -u
fi

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
export NEXT_PUBLIC_AUTH_MODE="${AUTH_MODE:-local}"

exec npm run dev:lan
