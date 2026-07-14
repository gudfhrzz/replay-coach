import json

from core.schema import DecisionPoint


def test_round_trip_json():
    p = DecisionPoint(
        game="cs2",
        match_id="m-abc",
        domain="economy",
        actor="CT",
        round=3,
        tick=12345,
        context={"side": "CT", "team_start_money": 18_000},
        decision={"buy_type": "force", "team_spend": 15_000},
        outcome={"round_won": True},
    )
    d = json.loads(p.to_json())
    assert d["game"] == "cs2"
    assert d["round"] == 3
    assert d["decision"]["team_spend"] == 15_000


def test_parser_registry():
    from parser import get_parser

    assert get_parser("cs2").game == "cs2"

    import pytest

    with pytest.raises(ValueError):
        get_parser("overwatch2")
