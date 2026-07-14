"""CS2 경제 판단(바이 결정) 분류 — 순수 함수, .dem 파일 불필요.

팀 장비 가치 구간은 HLTV/BO3 관행을 따른다 (5인 팀 기준 달러):
  full_eco < 5,000 ≤ semi_eco < 10,000 ≤ semi_buy < 20,000 ≤ full_buy

여기에 "포스 바이" 여부를 별도 플래그로 얹는다: 풀바이 장비에 못 미치는데
시작 자금의 대부분을 써버렸다면 강제 매수(force)로 본다.
"""

from __future__ import annotations

from dataclasses import dataclass

# 팀(5인) 장비 가치 기준 경계값
SEMI_ECO_MIN = 5_000
SEMI_BUY_MIN = 10_000
FULL_BUY_MIN = 20_000

# 시작 자금 대비 이 비율 이상을 썼는데 풀바이가 아니면 포스 바이로 판정
FORCE_SPEND_RATIO = 0.8

# MR12 기준 피스톨 라운드 (1라운드, 후반전 첫 라운드)
PISTOL_ROUNDS_MR12 = frozenset({1, 13})


@dataclass(frozen=True)
class BuyDecision:
    buy_type: str  # pistol | full_eco | semi_eco | semi_buy | full_buy
    is_forced: bool  # 풀바이 미달인데 가진 돈 대부분을 태웠는가
    team_equip_value: int  # 바이 타임 종료 시점 팀 장비 가치 합
    team_spend: int  # 이번 라운드 팀 지출 합
    team_start_money: int  # 라운드 시작 시점 팀 보유 자금 합


def classify_buy(
    round_number: int,
    team_equip_value: int,
    team_spend: int,
    team_start_money: int,
) -> BuyDecision:
    if round_number in PISTOL_ROUNDS_MR12:
        buy_type = "pistol"
    elif team_equip_value >= FULL_BUY_MIN:
        buy_type = "full_buy"
    elif team_equip_value >= SEMI_BUY_MIN:
        buy_type = "semi_buy"
    elif team_equip_value >= SEMI_ECO_MIN:
        buy_type = "semi_eco"
    else:
        buy_type = "full_eco"

    is_forced = (
        buy_type in ("semi_eco", "semi_buy")
        and team_start_money > 0
        and team_spend / team_start_money >= FORCE_SPEND_RATIO
    )

    return BuyDecision(
        buy_type=buy_type,
        is_forced=is_forced,
        team_equip_value=team_equip_value,
        team_spend=team_spend,
        team_start_money=team_start_money,
    )
