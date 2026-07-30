#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/mnt/d/cc项目/ai+medicine}"
PYTHON_BIN="${MUSETALK_PYTHON:-/home/zojer/ai-avatar/env/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "MuseTalk Python environment not found: $PYTHON_BIN" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"
exec "$PYTHON_BIN" -m uvicorn services.liveact_service.server:app \
  --host 0.0.0.0 \
  --port 8090
