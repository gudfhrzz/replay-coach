"""리플레이 → 결정 지점 추출 CLI.

사용법:
    uv run python cli.py <리플레이 파일> [--game cs2] [-o out.jsonl]
"""

from __future__ import annotations

import argparse
import sys

from core.schema import write_jsonl
from parser import get_parser


def main() -> int:
    ap = argparse.ArgumentParser(description="리플레이에서 결정 지점을 추출한다.")
    ap.add_argument("replay", help="리플레이 파일 경로 (예: match.dem)")
    ap.add_argument("--game", default="cs2", help="게임 식별자 (기본: cs2)")
    ap.add_argument("-o", "--out", default=None, help="JSONL 출력 경로")
    args = ap.parse_args()

    points = get_parser(args.game).extract(args.replay)
    if not points:
        print("결정 지점을 찾지 못했습니다. (워밍업만 있는 데모이거나 파싱 실패)")
        return 1

    print(f"결정 지점 {len(points)}개 추출 (match_id={points[0].match_id})\n")
    print(f"{'라운드':>4} {'사이드':>4} {'바이':>10} {'포스':>4} {'지출':>7} {'장비가치':>8} {'승리':>4}")
    for p in points:
        d, o = p.decision, p.outcome
        won = {True: "O", False: "X", None: "?"}[o.get("round_won")]
        forced = "F" if d["is_forced"] else ""
        print(
            f"{p.round:>5} {p.actor:>5} {d['buy_type']:>10} {forced:>4}"
            f" {d['team_spend']:>7,} {d['team_equip_value']:>8,} {won:>4}"
        )

    if args.out:
        write_jsonl(points, args.out)
        print(f"\nJSONL 저장: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
