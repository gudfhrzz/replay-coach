from analysis.compare import build_comparison
from analysis.esta import extract_economy
from analysis.patterns import build_pattern_db
from analysis.review import build_prompt


def _demo():
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

    return {
        "demoId": "test-demo",
        "mapName": "de_test",
        "gameRounds": [
            _round(1, 4000, 4000, "CT"),
            _round(2, 22000, 3000, "CT"),
            _round(3, 24000, 21000, "T"),
        ],
    }


def _user_points_and_db():
    points = [p.to_dict() for p in extract_economy(_demo())]
    db = build_pattern_db(extract_economy(_demo()))
    return points, db


def test_build_comparison_excludes_pistol():
    points, db = _user_points_and_db()
    records = build_comparison(points, db)
    assert all(r["user_buy"] != "pistol" for r in records)
    assert len(records) == 4  # 2·3라운드 × 2팀


def test_build_comparison_agreement_flag():
    points, db = _user_points_and_db()
    r2_t = next(r for r in build_comparison(points, db) if r["round"] == 2 and r["side"] == "T")
    # 유저 데이터로 DB를 만들었으니 자기 자신과는 일치해야 함
    assert r2_t.get("agrees_with_pro") is True
    assert r2_t["pro_dist"] is not None


def test_build_prompt_contains_key_facts():
    points, db = _user_points_and_db()
    records = build_comparison(points, db)
    prompt = build_prompt(records, db["meta"])
    assert "2라운드 T" in prompt
    assert "full_eco" in prompt
    assert "표본" in prompt
    assert db["meta"]["source"] in prompt
