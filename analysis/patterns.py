"""프로 패턴 DB v0 — 경제 결정의 조건부 분포.

조건 키: (side, loss_streak). 로스 보너스가 바이 판단의 주 변수라 v0은 이걸로 시작.
피스톨 라운드는 결정이 아니라 규칙에 가까우므로 분포에서 제외한다.

DB 포맷 (JSON):
{
  "meta": {...출처·라이선스...},
  "cells": {
    "T|2": {                       # side|loss_streak
      "n": 137,
      "buys": {"full_eco": {"n": 80, "won": 11}, ...}
    }, ...
  }
}
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from core.schema import DecisionPoint

META = {
    "source": "ESTA dataset (https://github.com/pnxenopoulos/esta)",
    "license": "CC BY-SA 4.0 — 파생 통계, 출처 표기 필수",
    "game": "csgo",
    "domain": "economy",
    "schema": "v0: cell = side|loss_streak, 피스톨 라운드 제외",
}


def cell_key(side: str, loss_streak: int) -> str:
    return f"{side}|{loss_streak}"


def build_pattern_db(points: list[DecisionPoint]) -> dict[str, Any]:
    cells: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"n": 0, "buys": defaultdict(lambda: {"n": 0, "won": 0})}
    )

    for p in points:
        if p.domain != "economy" or p.decision.get("buy_type") == "pistol":
            continue
        key = cell_key(p.context["side"], int(p.context.get("loss_streak", 0)))
        cell = cells[key]
        cell["n"] += 1
        b = cell["buys"][p.decision["buy_type"]]
        b["n"] += 1
        if p.outcome.get("round_won"):
            b["won"] += 1

    return {
        "meta": {**META, "total_decisions": sum(c["n"] for c in cells.values())},
        "cells": {k: {"n": v["n"], "buys": dict(v["buys"])} for k, v in sorted(cells.items())},
    }


def save_pattern_db(db: dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1)


def load_pattern_db(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def describe_cell(db: dict[str, Any], side: str, loss_streak: int) -> dict[str, Any] | None:
    """해당 상황에서 프로의 바이 분포와 선택별 라운드 승률을 돌려준다."""
    cell = db["cells"].get(cell_key(side, loss_streak))
    if not cell or cell["n"] == 0:
        return None
    out = {"n": cell["n"], "buys": {}}
    for buy_type, b in sorted(cell["buys"].items(), key=lambda kv: -kv[1]["n"]):
        out["buys"][buy_type] = {
            "share": b["n"] / cell["n"],
            "win_rate": (b["won"] / b["n"]) if b["n"] else None,
            "n": b["n"],
        }
    return out
