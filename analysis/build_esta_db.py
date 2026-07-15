"""ESTA 데이터 디렉터리 → 프로 패턴 DB JSON.

사용법:
    uv run python -m analysis.build_esta_db data/esta -o data/pro_patterns_csgo_v0.json
"""

from __future__ import annotations

import argparse

from analysis.esta import extract_economy_dir
from analysis.patterns import build_pattern_db, save_pattern_db


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help="ESTA .json.xz 파일들이 있는 디렉터리")
    ap.add_argument("-o", "--out", default="data/pro_patterns_csgo_v0.json")
    args = ap.parse_args()

    points = extract_economy_dir(args.data_dir)
    print(f"결정 지점 {len(points)}개 추출")

    db = build_pattern_db(points)
    save_pattern_db(db, args.out)
    print(f"패턴 DB 저장: {args.out} (결정 {db['meta']['total_decisions']}개)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
