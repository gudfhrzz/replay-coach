import json

from fastapi.testclient import TestClient

from web.app import app
from web.pipeline import UPLOAD_DIR

client = TestClient(app)


def _point(round_, side, buy, won):
    return {
        "game": "cs2",
        "match_id": "m1",
        "domain": "economy",
        "actor": side,
        "round": round_,
        "tick": None,
        "context": {"side": side},
        "decision": {
            "buy_type": buy,
            "is_forced": False,
            "team_spend": 20000,
            "team_equip_value": 22000,
        },
        "outcome": {"round_won": won},
    }


def _jsonl(points) -> bytes:
    return "\n".join(json.dumps(p) for p in points).encode()


def test_index_has_upload_form():
    r = client.get("/")
    assert r.status_code == 200
    assert "multipart/form-data" in r.text
    assert ".dem" in r.text


def test_review_jsonl_renders_comparison_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    body = _jsonl(
        [
            _point(1, "T", "pistol", True),
            _point(2, "T", "full_buy", True),
            _point(3, "CT", "full_eco", False),
        ]
    )
    r = client.post("/review", files={"file": ("match.jsonl", body)})
    assert r.status_code == 200
    assert "full_buy" in r.text
    assert "ANTHROPIC_API_KEY" in r.text  # 키 없음 안내가 떠야 함
    assert "pistol" not in r.text  # 피스톨 라운드는 비교에서 제외
    assert "m1" in r.text  # 매치 ID 표시
    assert "2/2" in r.text or "/2" in r.text  # 일치율 요약


def test_review_deletes_uploaded_file():
    body = _jsonl([_point(2, "T", "full_buy", True)])
    before = set(UPLOAD_DIR.glob("*")) if UPLOAD_DIR.exists() else set()
    r = client.post("/review", files={"file": ("match.jsonl", body)})
    assert r.status_code == 200
    after = set(UPLOAD_DIR.glob("*")) if UPLOAD_DIR.exists() else set()
    assert after == before  # 업로드 원본은 처리 직후 삭제


def test_review_calls_llm_when_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("web.app.generate_review", lambda records, meta: "리뷰 본문입니다")
    body = _jsonl([_point(2, "T", "full_buy", True)])
    r = client.post("/review", files={"file": ("match.jsonl", body)})
    assert r.status_code == 200
    assert "리뷰 본문입니다" in r.text
    assert "ANTHROPIC_API_KEY" not in r.text


def test_review_survives_llm_failure(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def _boom(records, meta):
        raise ValueError("authentication_error")

    monkeypatch.setattr("web.app.generate_review", _boom)
    body = _jsonl([_point(2, "T", "full_buy", True)])
    r = client.post("/review", files={"file": ("match.jsonl", body)})
    assert r.status_code == 200  # LLM이 죽어도 비교 테이블은 나와야 함
    assert "리뷰 생성에 실패" in r.text
    assert "full_buy" in r.text


def test_review_rejects_unknown_extension():
    r = client.post("/review", files={"file": ("notes.txt", b"hi")})
    assert r.status_code == 400
    assert "<html" in r.text  # 에러도 JSON이 아니라 HTML 페이지로


def test_review_rejects_garbage_jsonl():
    r = client.post("/review", files={"file": ("bad.jsonl", b"not json")})
    assert r.status_code == 422
    assert "해석할 수 없습니다" in r.text


def test_db_path_env_override_and_fallback(monkeypatch, tmp_path):
    from web.app import _db_path

    override = tmp_path / "custom.json"
    monkeypatch.setenv("REPLAY_COACH_DB", str(override))
    assert _db_path() == override
    monkeypatch.delenv("REPLAY_COACH_DB")
    # cs2 v1이 아직 없으므로 ESTA v0로 폴백
    assert _db_path().name == "pro_patterns_csgo_v0.json"


def test_review_rejects_pistol_only_file():
    body = _jsonl([_point(1, "T", "pistol", True)])
    r = client.post("/review", files={"file": ("match.jsonl", body)})
    assert r.status_code == 422
