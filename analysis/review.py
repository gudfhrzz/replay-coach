"""LLM 코칭 리뷰 v0 — 비교 엔진 출력 → 자연어 리뷰 (Claude API).

사용법:
    uv run python -m analysis.review user_out.jsonl data/pro_patterns_csgo_v0.json
    uv run python -m analysis.review user_out.jsonl data/pro_patterns_csgo_v0.json -o review.md

인증: ANTHROPIC_API_KEY 환경변수 또는 `ant auth login` 프로필.

v0 한계 (알고 쓰기):
- 프로 DB가 CS:GO(MR15) 기반이라 방향성 참고용 — 프롬프트에도 명시해 과신을 막는다.
- 티어 맥락화("당신 티어에선 Y가 낫다")는 아직 없음. 유저 티어 분포 확보 후 추가.
"""

from __future__ import annotations

import argparse
import json

from analysis.compare import build_comparison, load_user_points
from analysis.patterns import load_pattern_db

MODEL = "claude-opus-4-8"

SYSTEM = """\
당신은 CS2 전문 코치다. 유저의 라운드별 바이(구매) 결정을 프로 선수들의 통계 분포와 \
비교한 데이터를 받아, 한국어 코칭 리뷰를 작성한다.

원칙:
- 정답을 강요하지 말 것. "프로는 이 상황에서 X를 N% 선택했고 그 승률은 M%였다"처럼 \
분포와 근거를 보여주고, 유저의 선택이 소수 선택일 때 그 트레이드오프를 설명한다.
- 표본(n)이 작은 셀(대략 30 미만)은 근거로 단정하지 말고 참고 수준으로만 언급한다.
- 프로 데이터는 CS:GO(MR15) 시절 것이라 CS2(MR12)와 경제 상수가 다르다. 방향성 \
참고용임을 리뷰 서두에 한 문장으로 밝힌다.
- 구조: ① 한 줄 총평 → ② 잘한 판단 1-2개 → ③ 개선 여지가 큰 판단 1-3개(라운드 \
번호 명시, 프로 분포 근거 포함) → ④ 다음 게임에서 신경 쓸 것 한 가지.
- 잘난 척하는 말투 금지. 팀 동료가 데모 봐주는 톤으로.\
"""


def build_prompt(records: list[dict], db_meta: dict) -> str:
    """비교 레코드를 LLM 입력용 텍스트로 직렬화한다."""
    lines = [
        f"프로 분포 출처: {db_meta['source']} (결정 {db_meta['total_decisions']}개)",
        "",
        "유저의 라운드별 바이 결정과 같은 상황(사이드, 연패 수)의 프로 분포:",
        "",
    ]
    for r in records:
        won = {True: "승리", False: "패배", None: "결과 불명"}[r["user_won"]]
        lines.append(
            f"- {r['round']}라운드 {r['side']} (연패 {r['loss_streak']}): "
            f"유저 선택 = {r['user_buy']} → {won}"
        )
        if r["pro_dist"]:
            parts = [
                f"{buy} {b['share']:.0%} (n={b['n']}, 승률 "
                + (f"{b['win_rate']:.0%})" if b["win_rate"] is not None else "?)")
                for buy, b in r["pro_dist"]["buys"].items()
            ]
            lines.append(f"  프로 분포 (표본 {r['pro_dist']['n']}): " + " / ".join(parts))
        else:
            lines.append("  프로 데이터 없음")
    lines += ["", "위 데이터를 바탕으로 코칭 리뷰를 작성해줘."]
    return "\n".join(lines)


def generate_review(records: list[dict], db_meta: dict) -> str:
    """Claude API를 호출해 코칭 리뷰 텍스트를 생성한다."""
    import anthropic  # 지연 임포트 — 테스트·오프라인 사용 시 API 키 불필요

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(records, db_meta)}],
    )
    return next(b.text for b in response.content if b.type == "text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("user_jsonl", help="cli.py가 만든 유저 결정 지점 JSONL")
    ap.add_argument("pattern_db", help="프로 패턴 DB JSON")
    ap.add_argument("-o", "--out", default=None, help="리뷰를 저장할 파일 (기본: stdout)")
    ap.add_argument("--dry-run", action="store_true", help="API 호출 없이 프롬프트만 출력")
    args = ap.parse_args()

    db = load_pattern_db(args.pattern_db)
    records = build_comparison(load_user_points(args.user_jsonl), db)
    if not records:
        print("비교할 경제 결정이 없습니다 (피스톨 라운드만 있는 파일?)")
        return 1

    if args.dry_run:
        print(build_prompt(records, db["meta"]))
        return 0

    review = generate_review(records, db["meta"])
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(review + "\n")
        print(f"리뷰 저장: {args.out}")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
