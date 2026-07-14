#!/usr/bin/env bash
# Windows Smart App Control이 demoparser2 네이티브 모듈을 차단하므로,
# .dem 파싱은 WSL(Ubuntu)에서 실행한다. 사용법:
#   wsl -e bash scripts/wsl-run.sh cli.py demo.dem -o out.jsonl
#   wsl -e bash scripts/wsl-run.sh -m pytest -q
set -euo pipefail
cd "$(dirname "$0")/.."
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/replay-coach"
UV="$HOME/.local/bin/uv"
"$UV" sync --quiet
exec "$UV" run python "$@"
