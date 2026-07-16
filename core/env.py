"""리포 루트 .env 로더 — 각 엔트리 포인트(CLI·웹)에서 한 번 호출한다.

이미 설정된 환경변수는 덮어쓰지 않는다 (dotenv 기본 동작).
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env() -> None:
    load_dotenv(REPO_ROOT / ".env")
