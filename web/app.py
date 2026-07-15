"""웹 UI v0 — 리플레이 업로드 → 프로 비교 테이블 (+ LLM 코칭 리뷰).

실행:
    uv run uvicorn web.app:app --reload
    → http://127.0.0.1:8000 에서 .dem(또는 cli.py가 만든 .jsonl) 업로드

LLM 리뷰는 ANTHROPIC_API_KEY가 설정된 경우에만 생성하고, 없으면 비교 테이블만
보여준다. v0 한계: 업로드 처리기가 동기(요청 하나가 파싱·LLM을 기다림) —
실서비스 전 작업 큐로 분리 필요.
"""

from __future__ import annotations

import html
import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from analysis.compare import build_comparison, format_pro_dist, load_user_points
from analysis.patterns import load_pattern_db
from analysis.review import generate_review
from web.pipeline import REPO_ROOT, UPLOAD_DIR, parse_dem

PATTERN_DB_PATH = REPO_ROOT / "data" / "pro_patterns_csgo_v0.json"

app = FastAPI(title="Replay Coach")

_db: dict | None = None


def _get_db() -> dict:
    global _db
    if _db is None:
        _db = load_pattern_db(str(PATTERN_DB_PATH))
    return _db


def _page(body: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Replay Coach</title>
<style>
 body {{ font-family: system-ui, sans-serif; max-width: 60rem; margin: 2rem auto; padding: 0 1rem; }}
 table {{ border-collapse: collapse; width: 100%; }}
 th, td {{ border: 1px solid #ccc; padding: .35rem .6rem; text-align: left; font-size: .9rem; }}
 th {{ background: #f2f2f2; }}
 .agree {{ color: #1a7f37; }}
 .disagree {{ color: #b35900; }}
 .notice {{ background: #fff8e1; border: 1px solid #e6c200; padding: .6rem 1rem; border-radius: 4px; }}
 pre.review {{ white-space: pre-wrap; background: #f6f8fa; padding: 1rem; border-radius: 4px; }}
</style>
</head>
<body>
<h1><a href="/" style="text-decoration:none;color:inherit">Replay Coach</a> <small>v0</small></h1>
{body}
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _page(
        """<p>CS2 데모(.dem)를 업로드하면 라운드별 바이 결정을 프로 분포와 비교해 코칭 리뷰를 만들어줍니다.<br>
        (cli.py로 이미 추출한 .jsonl도 업로드 가능 — 파싱 단계 생략)</p>
        <form action="/review" method="post" enctype="multipart/form-data">
          <input type="file" name="file" accept=".dem,.jsonl" required>
          <button type="submit">분석하기</button>
        </form>
        <p><small>프로 분포 출처: ESTA dataset (CC BY-SA 4.0, CS:GO 2021-2022) —
        CS2와 경제 상수가 달라 방향성 참고용입니다.</small></p>"""
    )


@app.post("/review", response_class=HTMLResponse)
async def review(file: UploadFile = File(...)) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dem", ".jsonl"):
        raise HTTPException(400, ".dem 또는 .jsonl 파일만 지원합니다.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    saved.write_bytes(await file.read())

    db = _get_db()
    try:
        points = parse_dem(saved) if suffix == ".dem" else load_user_points(str(saved))
        records = build_comparison(points, db)
    except RuntimeError as e:  # WSL 파싱 실패 등 실행 환경 문제
        raise HTTPException(500, str(e)) from e
    except (json.JSONDecodeError, KeyError, TypeError) as e:  # 스키마 불일치
        raise HTTPException(422, f"파일을 결정 지점으로 해석할 수 없습니다: {e}") from e
    finally:
        # 업로드 원본(및 WSL 우회가 남긴 중간 JSONL)은 파싱 즉시 삭제 —
        # "데모는 파싱 후 보관하지 않는다"가 데이터 정책이다.
        saved.unlink(missing_ok=True)
        saved.with_suffix(".jsonl").unlink(missing_ok=True)

    if not records:
        raise HTTPException(422, "비교할 경제 결정이 없습니다 (피스톨 라운드만 있거나 빈 파일).")

    review_text = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        review_text = generate_review(records, db["meta"])
    match_id = str(points[0].get("match_id", "")) if points else ""
    return _page(_render_result(records, db["meta"], review_text, match_id))


def _render_result(
    records: list[dict], db_meta: dict, review_text: str | None, match_id: str = ""
) -> str:
    rows = []
    for r in records:
        won = {True: "승", False: "패", None: "?"}[r["user_won"]]
        if r["pro_top"] is None:
            agree = "<td>-</td>"
        elif r["agrees_with_pro"]:
            agree = '<td class="agree">프로 다수와 일치</td>'
        else:
            agree = f'<td class="disagree">프로 다수는 {html.escape(r["pro_top"])}</td>'
        rows.append(
            f"<tr><td>{r['round']}</td><td>{html.escape(r['side'])}</td>"
            f"<td>{r['loss_streak']}</td><td>{html.escape(r['user_buy'])}</td>"
            f"<td>{won}</td>{agree}"
            f"<td>{html.escape(format_pro_dist(r['pro_dist']))}</td></tr>"
        )

    if review_text is not None:
        review_html = f"<h2>코칭 리뷰</h2><pre class='review'>{html.escape(review_text)}</pre>"
    else:
        review_html = (
            "<p class='notice'>ANTHROPIC_API_KEY가 설정돼 있지 않아 LLM 코칭 리뷰를 "
            "생략했습니다. 아래 비교 테이블만 표시합니다.</p>"
        )

    judged = [r for r in records if r["agrees_with_pro"] is not None]
    agreed = sum(1 for r in judged if r["agrees_with_pro"])
    header = f"<p>매치: <code>{html.escape(match_id)}</code>" if match_id else "<p>"
    header += (
        f" — 경제 결정 {len(records)}개 중 <b>{agreed}/{len(judged)}</b>가 "
        "같은 상황의 프로 다수 선택과 일치</p>"
        if judged
        else "</p>"
    )

    return f"""{header}
{review_html}
<h2>라운드별 비교</h2>
<p><small>프로 분포 출처: {html.escape(db_meta["source"])} — 결정 {db_meta["total_decisions"]}개</small></p>
<table>
<tr><th>라운드</th><th>사이드</th><th>연패</th><th>유저 선택</th><th>결과</th><th>일치</th><th>같은 상황의 프로 분포</th></tr>
{"".join(rows)}
</table>
<p><a href="/">← 다른 파일 분석</a></p>"""
