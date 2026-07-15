"""CS2 데모 디렉터리 → 프로 패턴 DB JSON.

collect/backfill.py가 내려받은 FACEIT .dem(또는 cli.py가 만든 .jsonl)들을
결정 지점으로 모아 (side, loss_streak) 조건부 분포 DB를 만든다.

사용법:
    uv run python -m analysis.build_cs2_db data/faceit -o data/pro_patterns_cs2_v1.json

CS2 파서는 loss_streak를 넣지 않으므로, 비교 엔진과 같은 로직으로 매치별로
재구성한다 (MR12 하프 경계 리셋 포함). ESTA 빌더(build_esta_db.py)와 달리
게임이 CS2이므로 유저 데모와 경제 상수가 같다 — 실서비스용 분포는 이걸로 만든다.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from analysis.compare import attach_loss_streaks, load_user_points
from analysis.patterns import META_FACEIT_CS2, build_pattern_db, save_pattern_db
from core.schema import DecisionPoint


def collect_points(data_dir: str | Path) -> list[DecisionPoint]:
    """디렉터리의 .dem/.jsonl을 결정 지점으로 모으고 매치별 loss_streak를 붙인다."""
    data_dir = Path(data_dir)
    dicts: list[dict] = []

    dem_files = sorted(data_dir.glob("*.dem"))
    if dem_files:
        from parser import get_parser  # 지연 임포트 — demoparser2가 없는 환경 배려

        cs2 = get_parser("cs2")
        for dem in dem_files:
            dicts += [p.to_dict() for p in cs2.extract(str(dem))]
    for jl in sorted(data_dir.glob("*.jsonl")):
        dicts += load_user_points(str(jl))

    # loss_streak 재구성은 매치 단위 (라운드 번호가 매치마다 1부터 시작하므로)
    by_match: dict[str, list[dict]] = defaultdict(list)
    for d in dicts:
        by_match[d["match_id"]].append(d)
    for match_points in by_match.values():
        attach_loss_streaks(match_points)

    return [DecisionPoint(**d) for d in dicts]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", help=".dem/.jsonl 파일들이 있는 디렉터리")
    ap.add_argument("-o", "--out", default="data/pro_patterns_cs2_v1.json")
    args = ap.parse_args()

    points = collect_points(args.data_dir)
    n_matches = len({p.match_id for p in points})
    print(f"결정 지점 {len(points)}개 추출 (매치 {n_matches}개)")

    db = build_pattern_db(points, meta={**META_FACEIT_CS2, "n_matches": n_matches})
    save_pattern_db(db, args.out)
    print(f"패턴 DB 저장: {args.out} (결정 {db['meta']['total_decisions']}개)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
