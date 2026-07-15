import json

from analysis.build_cs2_db import collect_points
from analysis.patterns import META_FACEIT_CS2, build_pattern_db


def _point(match_id, round_, side, buy, won):
    return {
        "game": "cs2",
        "match_id": match_id,
        "domain": "economy",
        "actor": side,
        "round": round_,
        "tick": None,
        "context": {"side": side},
        "decision": {
            "buy_type": buy,
            "is_forced": False,
            "team_spend": 4000,
            "team_equip_value": 5000,
        },
        "outcome": {"round_won": won},
    }


def _write_jsonl(path, points):
    path.write_text("\n".join(json.dumps(p) for p in points), encoding="utf-8")


def test_collect_points_attaches_loss_streak_per_match(tmp_path):
    # 매치 A: T가 1-2라운드 연패 → 3라운드 loss_streak=2
    _write_jsonl(
        tmp_path / "a.jsonl",
        [
            _point("A", 1, "T", "pistol", False),
            _point("A", 2, "T", "full_eco", False),
            _point("A", 3, "T", "full_buy", True),
        ],
    )
    # 매치 B: 같은 라운드 번호지만 독립적으로 streak 계산돼야 함
    _write_jsonl(
        tmp_path / "b.jsonl",
        [
            _point("B", 1, "T", "pistol", True),
            _point("B", 2, "T", "full_buy", True),
            _point("B", 3, "T", "full_buy", True),
        ],
    )

    points = collect_points(tmp_path)
    streaks = {(p.match_id, p.round): p.context["loss_streak"] for p in points}
    assert streaks[("A", 3)] == 2
    assert streaks[("B", 3)] == 0


def test_build_pattern_db_with_cs2_meta(tmp_path):
    _write_jsonl(
        tmp_path / "a.jsonl",
        [
            _point("A", 2, "T", "full_buy", True),
            _point("A", 2, "CT", "full_eco", False),
        ],
    )
    points = collect_points(tmp_path)
    db = build_pattern_db(points, meta={**META_FACEIT_CS2, "n_matches": 1})
    assert db["meta"]["game"] == "cs2"
    assert db["meta"]["n_matches"] == 1
    assert db["meta"]["total_decisions"] == 2
    assert db["cells"]["T|0"]["buys"]["full_buy"]["n"] == 1
