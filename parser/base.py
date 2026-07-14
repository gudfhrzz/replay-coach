from __future__ import annotations

from abc import ABC, abstractmethod

from core.schema import DecisionPoint


class ReplayParser(ABC):
    """파서 플러그인 인터페이스. 리플레이 파일 → 결정 지점 목록."""

    game: str

    @abstractmethod
    def extract(self, replay_path: str, domains: list[str] | None = None) -> list[DecisionPoint]:
        """replay_path의 리플레이에서 결정 지점을 추출한다.

        domains가 None이면 이 파서가 지원하는 모든 도메인을 추출한다.
        """
