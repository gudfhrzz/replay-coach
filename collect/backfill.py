"""FACEIT 데모 백필 CLI — championship/hub의 종료 매치 데모를 수집한다.

사용법:
    # 매치·demo_url 확인만 (Data API 키만 필요 — 승인 전에도 동작)
    uv run python -m collect.backfill championship <id> --list-only

    # 데모 다운로드까지 (FACEIT_DOWNLOADS_KEY 필요 — 승인 후)
    uv run python -m collect.backfill championship <id> -n 100 -o data/faceit

내려받은 .dem은 cli.py로 파싱해 JSONL로 만들고, 프로 분포 DB 재구축은
analysis/ 쪽에서 후속 작업 (CS2용 build_faceit_db — 미구현).
"""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

from collect.faceit import FaceitClient


def main() -> int:
    ap = argparse.ArgumentParser(description="FACEIT 종료 매치 데모 백필")
    ap.add_argument("kind", choices=["championship", "hub"])
    ap.add_argument("entity_id", help="championship/hub ID")
    ap.add_argument("-n", "--max-matches", type=int, default=50)
    ap.add_argument("-o", "--out", default="data/faceit", help="데모 저장 디렉터리")
    ap.add_argument("--list-only", action="store_true", help="다운로드 없이 매치·demo_url만 출력")
    args = ap.parse_args()

    client = FaceitClient()
    out_dir = Path(args.out)
    downloaded = 0

    for m in itertools.islice(client.iter_matches(args.kind, args.entity_id), args.max_matches):
        match_id = m.get("match_id", "?")
        urls = client.demo_resource_urls(m)
        if args.list_only:
            print(f"{match_id}: {len(urls)}개 데모 — {urls}")
            continue
        for url in urls:
            dem = client.download_demo(url, out_dir)
            downloaded += 1
            print(f"{match_id}: {dem}")

    if not args.list_only:
        print(f"\n다운로드 완료: {downloaded}개 → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
