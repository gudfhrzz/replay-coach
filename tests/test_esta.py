from analysis.esta import extract_economy
from analysis.patterns import build_pattern_db, describe_cell


def _round(num, ct_eq, t_eq, winner_side, ct_team="Alpha", t_team="Bravo"):
    return {
        "roundNum": num,
        "isWarmup": False,
        "ctTeam": ct_team,
        "tTeam": t_team,
        "ctFreezeTimeEndEqVal": ct_eq,
        "tFreezeTimeEndEqVal": t_eq,
        "ctRoundSpendMoney": ct_eq - 1000,
        "tRoundSpendMoney": t_eq - 1000,
        "ctRoundStartEqVal": 1000,
        "tRoundStartEqVal": 1000,
        "winningTeam": ct_team if winner_side == "CT" else t_team,
        "winningSide": winner_side,
    }


def _demo():
    return {
        "demoId": "test-demo",
        "mapName": "de_test",
        "gameRounds": [
            _round(1, 4000, 4000, "CT"),  # 피스톨, T 패배
            _round(2, 22000, 3000, "CT"),  # T 풀에코, 또 패배 (연패 1→2로 가는 중)
            _round(3, 24000, 21000, "T"),  # T 풀바이 성공
        ],
    }


def test_extract_economy_basic():
    points = extract_economy(_demo())
    assert len(points) == 6  # 3라운드 × 2팀
    r2_t = next(p for p in points if p.round == 2 and p.actor == "T")
    assert r2_t.decision["buy_type"] == "full_eco"
    assert r2_t.context["loss_streak"] == 1  # 피스톨 패배 후
    assert r2_t.outcome["round_won"] is False
    r3_t = next(p for p in points if p.round == 3 and p.actor == "T")
    assert r3_t.context["loss_streak"] == 2
    assert r3_t.outcome["round_won"] is True


def test_mr15_pistol_rounds():
    demo = _demo()
    demo["gameRounds"][0]["roundNum"] = 16
    points = extract_economy(demo)
    r16 = next(p for p in points if p.round == 16 and p.actor == "CT")
    assert r16.decision["buy_type"] == "pistol"


def test_pattern_db_roundtrip():
    db = build_pattern_db(extract_economy(_demo()))
    # 피스톨(1라운드) 제외 → 2·3라운드 × 2팀 = 4개
    assert db["meta"]["total_decisions"] == 4
    cell = describe_cell(db, "T", 1)
    assert cell is not None
    assert cell["buys"]["full_eco"]["n"] == 1
    assert describe_cell(db, "CT", 4) is None
