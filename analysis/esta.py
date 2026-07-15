"""ESTA 데이터셋(awpy 파싱 CS:GO JSON) → 경제 결정 지점 변환.

ESTA: https://github.com/pnxenopoulos/esta (CC BY-SA 4.0, 프로 CS:GO 2021-2022)

주의:
- CS:GO(MR15) 데이터라 피스톨 라운드는 1, 16. 연장전(>30)은 경제 규칙이 달라 제외.
- ESTA에는 팀 보유 현금이 없어 start_money=0으로 두므로 is_forced는 항상 False —
  프로 분포 v0은 buy_type만 사용한다.
- 바이 분류는 awpy의 ctBuyType/tBuyType를 쓰지 않고 우리 classify_buy를 장비 가치에
  다시 적용한다. 유저(CS2) 결정과 같은 잣대로 비교하기 위해서다.
"""

from __future__ import annotations

import json
import lzma
from pathlib import Path
from typing import Any

from core.schema import DecisionPoint
from parser.cs2.economy import PISTOL_ROUNDS_MR15, classify_buy

MAX_REGULATION_ROUNDS_MR15 = 30
LOSS_STREAK_CAP = 4  # CS:GO/CS2 로스 보너스는 4연패에서 최대치


def load_esta_file(path: str | Path) -> dict[str, Any]:
    with lzma.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def extract_economy(demo: dict[str, Any], match_id: str | None = None) -> list[DecisionPoint]:
    """ESTA 파싱 데모 1개 → 팀·라운드별 경제 결정 지점."""
    match_id = match_id or demo.get("demoId") or demo.get("matchName") or "esta-unknown"
    rounds = [
        r
        for r in demo.get("gameRounds", [])
        if not r.get("isWarmup") and r.get("roundNum", 0) <= MAX_REGULATION_ROUNDS_MR15
    ]

    points: list[DecisionPoint] = []
    loss_streak: dict[str, int] = {}  # 팀 이름 → 현재 연패 수

    for r in rounds:
        round_no = int(r["roundNum"])
        winning_team = r.get("winningTeam")

        for side, prefix in (("CT", "ct"), ("T", "t")):
            team_name = (r.get(f"{prefix}Team") or f"{side}?") or f"{side}?"
            equip = int(r.get(f"{prefix}FreezeTimeEndEqVal") or 0)
            spend = int(r.get(f"{prefix}RoundSpendMoney") or 0)
            start_eq = int(r.get(f"{prefix}RoundStartEqVal") or 0)

            buy = classify_buy(
                round_number=round_no,
                team_equip_value=equip,
                team_spend=spend,
                team_start_money=0,  # ESTA에 현금 정보 없음
                pistol_rounds=PISTOL_ROUNDS_MR15,
            )
            won = (winning_team == team_name) if winning_team else None

            points.append(
                DecisionPoint(
                    game="csgo",
                    match_id=str(match_id),
                    domain="economy",
                    actor=side,
                    round=round_no,
                    context={
                        "side": side,
                        "loss_streak": min(loss_streak.get(team_name, 0), LOSS_STREAK_CAP),
                        "carryover_equip": start_eq,
                        "map": demo.get("mapName"),
                    },
                    decision={
                        "buy_type": buy.buy_type,
                        "team_spend": spend,
                        "team_equip_value": equip,
                    },
                    outcome={"round_won": won},
                )
            )

            if won is not None:
                loss_streak[team_name] = 0 if won else loss_streak.get(team_name, 0) + 1

    return points


def extract_economy_dir(data_dir: str | Path) -> list[DecisionPoint]:
    """디렉터리의 모든 ESTA .json.xz에서 경제 결정 지점을 모은다."""
    points: list[DecisionPoint] = []
    files = sorted(Path(data_dir).glob("*.json.xz"))
    for i, f in enumerate(files, 1):
        try:
            points += extract_economy(load_esta_file(f), match_id=f.stem)
        except (json.JSONDecodeError, lzma.LZMAError, KeyError) as e:
            print(f"  건너뜀 {f.name}: {e}")
        if i % 10 == 0:
            print(f"  {i}/{len(files)} 처리")
    return points
