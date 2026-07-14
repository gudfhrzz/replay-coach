"""결정 지점(Decision Point) 스키마 — 게임 무관 파이프라인의 공통 계약.

파서 플러그인은 리플레이 파일을 받아 DecisionPoint 목록을 내놓는다.
이후 단계(프로 패턴 DB 비교, LLM 리뷰)는 이 스키마만 알면 된다.

context / decision / outcome 내부 키는 게임·도메인별로 자유지만,
같은 (game, domain) 안에서는 일관돼야 프로 분포와 비교할 수 있다.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DecisionPoint:
    game: str  # 예: "cs2"
    match_id: str  # 게임별 매치 식별자 (파일 해시, 매치 ID 등)
    domain: str  # 분석 도메인. 예: "economy"
    actor: str  # 결정 주체 — 팀 단위 결정이면 팀, 개인 결정이면 플레이어
    round: int | None = None  # 라운드 기반 게임의 라운드 번호 (1부터)
    tick: int | None = None  # 리플레이 내 시점 참조 (게임별 단위)
    context: dict[str, Any] = field(default_factory=dict)  # 결정 시점의 상황
    decision: dict[str, Any] = field(default_factory=dict)  # 실제로 내린 결정
    outcome: dict[str, Any] = field(default_factory=dict)  # 결과 (승패 등, 사후 라벨)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def write_jsonl(points: list[DecisionPoint], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for p in points:
            f.write(p.to_json() + "\n")
