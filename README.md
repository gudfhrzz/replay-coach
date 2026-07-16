    # Replay Coach (가칭 / working title)

> **English summary** — Replay Coach is a replay-coaching service (pre-launch):
> upload your demo, and instead of a stat dashboard it extracts the individual
> *decisions* you made (starting with CS2 buy decisions per round) and compares
> each one to the statistical distribution of what professional players did in
> the same situation (side, economy, loss streak), with an LLM layer turning
> that into readable coaching notes. The pipeline is game-agnostic by design —
> only the replay parser is a per-game plugin. Current status: CS2 parser →
> decision-point extraction → pro-distribution comparison engine working
> end-to-end — including a minimal upload→review web UI — with the prototype
> pro database built from the public
> [ESTA](https://github.com/pnxenopoulos/esta) dataset (CC BY-SA 4.0,
> ~5,700 pro buy decisions from 120 matches). Docs and code comments are in
> Korean.

유저가 리플레이를 업로드하면, **프로 선수들의 리플레이로 학습한 AI**가 게임 상황별로
"프로라면 어떻게 했을까"를 비교·설명해주는 코칭 웹 서비스.

## 핵심 아이디어
- 프로는 그 게임을 가장 잘하는 사람들 — 정답은 없어도 **승률 높은 선택의 분포**를 갖고 있다.
- 기존 툴(Mobalytics, Blitz.gg 등)은 *통계*를 보여주지만, 우리는 **"이 순간의 판단"**을 다룬다.
- 좋아하는 프로 선수의 패턴만 필터링해 "그 선수처럼 플레이하기" 비교도 제공.

## 제품 파이프라인 (게임 무관 공통 설계)
```
리플레이 파일 ─→ 게임별 파서(플러그인) ─→ 결정 지점(Decision Point) 추출
             ─→ 프로 패턴 DB와 비교 ─→ LLM 코칭 리뷰 생성 ─→ 웹 UI
```

## 현재 단계
- [x] 대상 게임 확정 — **CS2** (`Docs/game-selection.md`)
- [ ] MVP 분석 도메인 1개 선정 — 경제 판단(바이 결정)으로 파이프라인 v0 구현됨, 확정은 미정
- [x] 파서 → 결정 지점 추출 첫 파이프라인 (CS2 경제 판단, 아래 실행법 참고)
- [x] 프로 패턴 DB 프로토타입 — ESTA(CS:GO) 기반 경제 결정 분포 + 비교 엔진 v0
  (실서비스 분포는 FACEIT CS2 데모 확보 후 재구축 예정)
- [x] LLM 코칭 리뷰 v0 — 비교 결과 → Claude API로 한국어 코칭 리뷰 생성
- [x] 웹 UI v0 — 업로드 → 비교 테이블 + LLM 리뷰 (키 없으면 테이블만)
- [x] FACEIT 수집 클라이언트 스캐폴드 — Data/Downloads API + 백필 CLI
  (`collect/`, 키 발급 대기 중이라 실 API 미검증)
- [x] CS2 패턴 DB 빌더 — 수집한 데모 디렉터리 → 실서비스용 분포 DB
  (`analysis/build_cs2_db.py`, FACEIT 데모 확보 후 가동)

## 실행법

의존성: [uv](https://docs.astral.sh/uv/). `uv sync`로 환경 구성.

```
uv run python cli.py <매치.dem> -o out.jsonl   # 라운드별 바이 결정 요약 + JSONL
uv run pytest -q
```

### 프로 패턴 DB (ESTA 프로토타입)

```
uv run python scripts/download_esta.py -n 40 -o data/esta        # ESTA 서브셋 다운로드
uv run python -m analysis.build_esta_db data/esta \
    -o data/pro_patterns_csgo_v0.json                             # 프로 분포 DB 구축
uv run python -m analysis.compare out.jsonl \
    data/pro_patterns_csgo_v0.json                                # 유저 vs 프로 비교
uv run python -m analysis.review out.jsonl \
    data/pro_patterns_csgo_v0.json -o review.md                   # LLM 코칭 리뷰 생성
```

LLM 리뷰는 `ANTHROPIC_API_KEY` 환경변수가 필요하다 (`--dry-run`으로 프롬프트만
확인 가능). API 키는 리포 루트 `.env` 파일에 넣으면 자동 로드된다
(`FACEIT_API_KEY`, `ANTHROPIC_API_KEY` 등 — `.gitignore`에 포함).

### 웹 UI (v0)

```
uv run uvicorn web.app:app --reload
```

http://127.0.0.1:8000 에서 `.dem`(또는 cli.py가 만든 `.jsonl`) 업로드 →
비교 테이블 + LLM 코칭 리뷰. `ANTHROPIC_API_KEY`가 없으면 테이블만 표시된다.
`.dem` 파싱은 demoparser2 네이티브 임포트가 되면 그대로 실행하고, 차단된
환경(아래 Windows 주의)에서만 WSL 래퍼로 자동 폴백한다.

출처: [ESTA](https://github.com/pnxenopoulos/esta) (CC BY-SA 4.0, 프로 CS:GO 2021-2022).
CS:GO(MR15) 데이터라 CS2(MR12) 유저 결정과의 비교는 방향성 참고용 — 상세 한계는
각 모듈 docstring 참고.

**Windows 주의**: Smart App Control이 켜진 PC에서는 demoparser2 네이티브 모듈이
차단된다(DLL load failed). 이 경우 WSL로 실행:

```
wsl -e bash scripts/wsl-run.sh cli.py <매치.dem>
```
