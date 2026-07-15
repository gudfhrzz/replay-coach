"""비교 엔진 v0 — 유저 결정 지점(JSONL) vs 프로 패턴 DB.

사용법:
    uv run python -m analysis.compare user_out.jsonl data/pro_patterns_csgo_v0.json

유저 파일의 각 경제 결정에 대해, 같은 상황(사이드·연패 수)에서 프로가 보인
바이 분포와 선택별 승률을 붙여 출력한다. LLM 리뷰 레이어의 입력이 될 데이터다.

v0 한계 (알고 쓰기):
- 프로 DB는 CS:GO(MR15), 유저는 CS2(MR12) — 경제 상수가 달라 방향성 참고용.
- 유저 쪽 연패 수는 사이드 기준으로 재구성하며 하프 경계(13라운드)에서 리셋.
"""

from __future__ import annotations

import argparse
import json

from analysis.patterns import describe_cell, load_pattern_db

MR12_SECOND_HALF_START = 13
LOSS_STREAK_CAP = 4


def load_user_points(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def attach_loss_streaks(points: list[dict]) -> None:
    """사이드별 직전 라운드 결과에서 연패 수를 재구성해 context에 넣는다."""
    streak: dict[str, int] = {}
    for p in sorted(points, key=lambda p: (p["round"], p["actor"])):
        if p["round"] == 1 or p["round"] == MR12_SECOND_HALF_START:
            streak[p["actor"]] = 0
        p["context"]["loss_streak"] = min(streak.get(p["actor"], 0), LOSS_STREAK_CAP)
        won = p["outcome"].get("round_won")
        if won is not None:
            streak[p["actor"]] = 0 if won else streak.get(p["actor"], 0) + 1


def build_comparison(points: list[dict], db: dict) -> list[dict]:
    """경제 결정별로 프로 분포를 붙인 비교 레코드를 만든다 (피스톨 제외).

    LLM 리뷰 레이어의 입력이자 CLI 출력의 데이터 소스.
    """
    attach_loss_streaks(points)
    records = []
    for p in sorted(points, key=lambda p: (p["round"], p["actor"])):
        buy = p["decision"]["buy_type"]
        if buy == "pistol":
            continue
        cell = describe_cell(db, p["context"]["side"], p["context"]["loss_streak"])
        pro_top = next(iter(cell["buys"])) if cell else None
        records.append(
            {
                "round": p["round"],
                "side": p["context"]["side"],
                "loss_streak": p["context"]["loss_streak"],
                "user_buy": buy,
                "user_won": p["outcome"].get("round_won"),
                "pro_top": pro_top,
                "agrees_with_pro": (buy == pro_top) if pro_top else None,
                "pro_dist": cell,
            }
        )
    return records


def format_pro_dist(cell: dict | None) -> str:
    if not cell:
        return "(프로 데이터 없음)"
    parts = []
    for buy_type, b in list(cell["buys"].items())[:3]:
        wr = f", 승률 {b['win_rate']:.0%}" if b["win_rate"] is not None else ""
        parts.append(f"{buy_type} {b['share']:.0%}{wr}")
    return " / ".join(parts) + f"  (표본 {cell['n']})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("user_jsonl", help="cli.py가 만든 유저 결정 지점 JSONL")
    ap.add_argument("pattern_db", help="프로 패턴 DB JSON")
    args = ap.parse_args()

    db = load_pattern_db(args.pattern_db)
    points = load_user_points(args.user_jsonl)

    print(f"프로 DB: {db['meta']['source']} — 결정 {db['meta']['total_decisions']}개\n")
    for r in build_comparison(points, db):
        agree = ""
        if r["pro_top"]:
            agree = "✓ 프로 다수와 일치" if r["agrees_with_pro"] else f"✗ 프로 다수는 {r['pro_top']}"
        print(f"R{r['round']:>2} {r['side']:>2} (연패 {r['loss_streak']}): 당신 = {r['user_buy']:<9} {agree}")
        print(f"      프로: {format_pro_dist(r['pro_dist'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
