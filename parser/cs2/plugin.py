"""CS2 파서 플러그인 — demoparser2로 .dem을 읽어 결정 지점을 추출한다.

현재 지원 도메인: economy (라운드별 팀 바이 결정)

추출 방식:
- round_freeze_end 이벤트 틱에서 각 플레이어의 잔고(balance)·이번 라운드 지출
  (cash_spent_this_round)·장비 가치(current_equip_value)를 읽는다.
  프리즈 타임에 대부분의 구매가 끝나므로 이 시점을 "바이 결정이 내려진 순간"으로 본다.
- 시작 자금 = 잔고 + 이번 라운드 지출 (프리즈 종료 시점 기준 역산).
- round_end 이벤트의 winner로 결과 라벨을 붙인다.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from core.schema import DecisionPoint
from parser.base import ReplayParser
from parser.cs2.economy import classify_buy

TEAM_NUM_T = 2
TEAM_NUM_CT = 3
SIDE_NAME = {TEAM_NUM_T: "T", TEAM_NUM_CT: "CT"}

_TICK_PROPS = [
    "balance",
    "cash_spent_this_round",
    "current_equip_value",
    "team_num",
    "total_rounds_played",
]


class CS2Parser(ReplayParser):
    game = "cs2"
    domains = ["economy"]

    def extract(self, replay_path: str, domains: list[str] | None = None) -> list[DecisionPoint]:
        from demoparser2 import DemoParser  # 무거운 import는 사용 시점으로 지연

        wanted = domains or self.domains
        unknown = set(wanted) - set(self.domains)
        if unknown:
            raise ValueError(f"cs2 파서가 지원하지 않는 도메인: {sorted(unknown)}")

        demo = DemoParser(replay_path)
        match_id = _match_id(replay_path)

        points: list[DecisionPoint] = []
        if "economy" in wanted:
            points += self._extract_economy(demo, match_id)
        return points

    def _extract_economy(self, demo, match_id: str) -> list[DecisionPoint]:
        freeze_ends = demo.parse_event("round_freeze_end")
        round_ends = demo.parse_event("round_end")

        freeze_ticks = sorted(freeze_ends["tick"].tolist())
        if not freeze_ticks:
            return []

        # 각 라운드의 승자: freeze_end 틱 이후 첫 round_end의 winner
        end_rows = sorted(
            zip(round_ends["tick"].tolist(), round_ends.get("winner", []).tolist())
        ) if "winner" in round_ends.columns else []

        ticks_df = demo.parse_ticks(_TICK_PROPS, ticks=freeze_ticks)

        points: list[DecisionPoint] = []
        for round_no, ftick in enumerate(freeze_ticks, start=1):
            snap = ticks_df[ticks_df["tick"] == ftick]
            if snap.empty:
                continue

            winner = _winner_after(end_rows, ftick)

            for team_num, side in SIDE_NAME.items():
                team = snap[snap["team_num"] == team_num]
                if team.empty:
                    continue

                spend = int(team["cash_spent_this_round"].fillna(0).sum())
                balance = int(team["balance"].fillna(0).sum())
                equip = int(team["current_equip_value"].fillna(0).sum())
                start_money = balance + spend

                buy = classify_buy(
                    round_number=round_no,
                    team_equip_value=equip,
                    team_spend=spend,
                    team_start_money=start_money,
                )

                points.append(
                    DecisionPoint(
                        game=self.game,
                        match_id=match_id,
                        domain="economy",
                        actor=side,
                        round=round_no,
                        tick=int(ftick),
                        context={
                            "side": side,
                            "team_start_money": start_money,
                            "players": int(len(team)),
                        },
                        decision={
                            "buy_type": buy.buy_type,
                            "is_forced": buy.is_forced,
                            "team_spend": spend,
                            "team_equip_value": equip,
                            "money_left": balance,
                        },
                        outcome={"round_won": (winner == side) if winner else None},
                    )
                )
        return points


def _winner_after(end_rows: list[tuple[int, object]], freeze_tick: int) -> str | None:
    """freeze_tick 직후에 오는 round_end의 승자 사이드("CT"/"T")를 돌려준다."""
    for tick, winner in end_rows:
        if tick > freeze_tick:
            w = str(winner).upper()
            if w in ("CT", "T"):
                return w
            if w in ("2", "TERRORIST"):
                return "T"
            if w == "3":
                return "CT"
            return None
    return None


def _match_id(replay_path: str) -> str:
    """매치 식별자 — 파일 내용 앞부분 해시 (같은 데모 재업로드 시 중복 감지용)."""
    h = hashlib.sha256()
    with open(replay_path, "rb") as f:
        h.update(f.read(1 << 20))
    return f"{Path(replay_path).stem}-{h.hexdigest()[:12]}"
