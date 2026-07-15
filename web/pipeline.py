"""웹 UI 파이프라인 글루 — 업로드된 .dem → 결정 지점 dict 목록.

.dem 파싱은 demoparser2 네이티브 모듈이 로드되면 그대로 인프로세스로 실행하고,
로드가 안 되는 환경(Smart App Control이 켜진 Windows — .pyd 차단)에서만
WSL 래퍼(scripts/wsl-run.sh)를 서브프로세스로 호출해 우회한다. WSL 우회 시
업로드 파일이 저장소 안(web/uploads/)에 있어야 WSL에서 같은 경로로 접근할 수 있다.
"""

from __future__ import annotations

import subprocess
from functools import cache
from pathlib import Path

from analysis.compare import load_user_points

REPO_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = REPO_ROOT / "web" / "uploads"
PARSE_TIMEOUT_SEC = 600


@cache
def _native_parser_available() -> bool:
    try:
        import demoparser2  # noqa: F401
    except ImportError:  # SAC가 켜진 Windows에서 DLL load failed
        return False
    return True


def parse_dem(dem_path: Path) -> list[dict]:
    """업로드된 .dem에서 결정 지점 dict 목록을 뽑는다. 실패 시 RuntimeError."""
    if not _native_parser_available():
        return _parse_dem_via_wsl(dem_path)
    from parser import get_parser

    return [p.to_dict() for p in get_parser("cs2").extract(str(dem_path))]


def _parse_dem_via_wsl(dem_path: Path) -> list[dict]:
    rel_dem = dem_path.relative_to(REPO_ROOT).as_posix()
    rel_out = dem_path.with_suffix(".jsonl").relative_to(REPO_ROOT).as_posix()
    proc = subprocess.run(
        ["wsl", "-e", "bash", "scripts/wsl-run.sh", "cli.py", rel_dem, "-o", rel_out],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=PARSE_TIMEOUT_SEC,
    )
    out_path = REPO_ROOT / rel_out
    if proc.returncode != 0 or not out_path.exists():
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"WSL 파싱 실패 (exit {proc.returncode}): {detail}")
    return load_user_points(str(out_path))
