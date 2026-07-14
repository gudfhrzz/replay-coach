"""게임별 리플레이 파서 플러그인 레지스트리."""

from __future__ import annotations

from parser.base import ReplayParser


def get_parser(game: str) -> ReplayParser:
    if game == "cs2":
        from parser.cs2 import CS2Parser

        return CS2Parser()
    raise ValueError(f"지원하지 않는 게임: {game!r} (지원: cs2)")
