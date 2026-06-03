#!/usr/bin/env bash
# Daily fetch wrapper — called by launchd (macOS) or cron (Linux/VPS).
# Resolves the project root from its own location so it works regardless
# of the working directory the scheduler uses.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/fetch-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

cd "$PROJECT_DIR"

# Load secrets and config from scripts/.env if not already set in the environment.
# Supported variables:
#   ANTHROPIC_API_KEY  — required for ENRICH_MODE=api
#   TELEGRAM_BOT_TOKEN — required for Telegram posting
#   TELEGRAM_CHANNEL_ID — required for Telegram posting
#   ENRICH_MODE        — api | local | mock | (empty = no enrichment)
#   LOCAL_MODEL        — Ollama model name for ENRICH_MODE=local (default: phi4-mini)
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi

# Choose enrichment mode:
#   ENRICH_MODE=api    → --enrich (requires ANTHROPIC_API_KEY)
#   ENRICH_MODE=local  → --enrich-local (requires Ollama running)
#   ENRICH_MODE=mock   → --enrich-mock (no cost, for UI testing)
#   ENRICH_MODE=       → no enrichment
ENRICH_MODE="${ENRICH_MODE:-local}"
LOCAL_MODEL="${LOCAL_MODEL:-phi4-mini}"

case "$ENRICH_MODE" in
  api)   ENRICH_FLAG="--enrich" ;;
  local) ENRICH_FLAG="--enrich-local --local-model ${LOCAL_MODEL}" ;;
  mock)  ENRICH_FLAG="--enrich-mock" ;;
  *)     ENRICH_FLAG="" ;;
esac

{
  echo "=== newAgg daily fetch: $(date '+%Y-%m-%d %H:%M:%S %Z') ==="

  python3 scripts/fetch_india_headlines.py \
    --extract-text \
    --allow-partial \
    --notify \
    ${ENRICH_FLAG} \
    "$@"

  echo "--- generating brief ---"
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHANNEL_ID:-}" ]; then
    python3 scripts/post_telegram.py
  else
    python3 scripts/post_telegram.py --save-only
  fi

  echo "=== done ==="
} 2>&1 | tee -a "$LOG_FILE"
