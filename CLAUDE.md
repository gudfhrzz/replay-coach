# Replay Coach — 프로젝트 컨텍스트

## 개요
프로 리플레이로 학습한 AI가 유저 리플레이를 분석해 "프로라면 어떻게 했을까"를
코칭해주는 웹 서비스. **Rpg-on-Earth와 무관한 완전 별개 프로젝트.**

## 핵심 설계 원칙
1. **파서만 게임별 플러그인, 나머지 파이프라인은 게임 무관** —
   결정 지점(Decision Point) 스키마 → 프로 패턴 DB → 비교 엔진 → LLM 리뷰 → 웹 UI
2. **풀 모방학습(AlphaStar류) 아님** — 파싱된 결정 지점에 대한 통계적 프로 분포 모델
   + LLM 설명 레이어. 연구가 아니라 제품.
3. **티어 맥락화** — "프로는 X를 하지만 당신 티어에선 Y가 승률이 높다"까지가 목표.
   프로 따라하기만 강요하면 저티어에선 역효과.

## 현재 상태 (2026-07-15)
- **시작 게임 = CS2 확정.** 확장 트랙 = Riot 계열(LoL+TFT 묶음, API 인프라 공유).
  오버워치는 데이터 접근성 문제로 제외. 근거: `Docs/game-selection.md`
- **파이프라인 v0 완료**: .dem → 라운드별 팀 바이 결정(DecisionPoint JSONL).
  demoparser2 공식 테스트 데모로 E2E 검증됨. 실행법은 README 참고.
- **프로 패턴 DB 프로토타입 완료** (`analysis/`): ESTA 120개 데모 →
  경제 결정 5,742개 → (side, loss_streak) 조건부 분포 DB
  (`data/pro_patterns_csgo_v0.json`) + 비교 엔진 v0 (`analysis/compare.py`).
  E2E 검증됨. CS:GO(MR15) 데이터라 방법론 검증용 — 실서비스 분포는 FACEIT
  CS2 데모로 재구축.
- **LLM 코칭 리뷰 v0 완료** (`analysis/review.py`): 비교 결과 → Claude API
  (claude-opus-4-8)로 한국어 코칭 리뷰. 프롬프트 빌드는 테스트 커버,
  실 API 호출은 이 PC에 ANTHROPIC_API_KEY가 없어 미검증 — 키 설정 후
  `--dry-run` 없이 한 번 돌려볼 것.
- **웹 UI v0 완료** (`web/`): FastAPI 업로드(.dem/.jsonl) → 매치·일치율 요약 +
  비교 테이블 + LLM 리뷰(키 없으면 테이블만). .dem 파싱은 demoparser2 네이티브
  임포트 성공 시 인프로세스, 실패 시 WSL 래퍼 폴백 (`web/pipeline.py`).
  업로드 원본은 파싱 직후 삭제(신청서의 데이터 정책과 일치). 실서버 E2E 검증됨:
  .jsonl 경로 + .dem 경로(awpy 공개 테스트 데모 112MB, 네이티브 파싱 ~1초).
  미검증: WSL 폴백 경로(노트북에서), LLM 리뷰 표시(API 키 필요).
  v0 한계: 동기 처리(큐 없음).
- 미정: 서비스명(폴더명 replay-coach는 가칭), MVP 도메인 확정(경제 판단으로 v0
  구현했으나 공식 확정은 아직).
- 프로 데모 수집 약관 확인 완료: HLTV 자동 수집 금지(제외), FACEIT Downloads API가
  공식 경로(신청 후 30일 심사), ESTA 데이터셋(CC BY-SA 4.0)은 즉시 사용 가능.
  상세: `Docs/pro-demo-collection-tos.md`
- FACEIT 가입 진행 중 — 본인인증이 "already have a verified account" 오류로
  막힘(정체불명의 기존 인증 계정 존재). 지원 티켓 **Request #14040400** 왕복 중
  (1차 매크로 답변 → 재반박 발송, 2026-07-15). 경과는 GitHub 이슈 #1에 기록,
  제출 텍스트는 `Docs/faceit-downloads-api-application.md`.
- **FACEIT 수집 클라이언트 스캐폴드 완료** (`collect/`): Data API v4(매치
  목록·demo_url) + Downloads API(signed URL→.dem.gz 다운로드·압축해제) 클라이언트
  + 백필 CLI. httpx MockTransport 테스트 커버. 실 API 미검증 — 키 발급 후
  `--list-only`부터. 인증: `FACEIT_API_KEY`(앱 생성 직후 사용 가능),
  `FACEIT_DOWNLOADS_KEY`(심사 승인 후).
- **CS2 패턴 DB 빌더 완료** (`analysis/build_cs2_db.py`): .dem/.jsonl 디렉터리 →
  매치별 loss_streak 재구성 → CS2 메타 분포 DB. 실데모 1개로 E2E 검증됨.
  FACEIT 데모가 모이면 이걸로 실서비스 분포(`pro_patterns_cs2_v1.json`) 생성 →
  웹/비교 엔진의 DB 경로 교체.
- 다음 단계: ① FACEIT 티켓 회신 확인 → 본계정 확보 → 이슈 #1 체크리스트 재개.
  ② ANTHROPIC_API_KEY 설정 후 LLM 리뷰 실 호출 검증(CLI + 웹 UI).
  ③ 웹 UI .dem 업로드 경로(WSL 파싱) 실데모로 검증. ④ 레딧 검증 포스트 게시
  (`Docs/reddit-post-draft.md`).

## 환경 제약 (개발 PC 2대 — 어느 쪽인지 먼저 확인)
- **데스크탑** (2026-07-15 현재 주 작업 PC): Smart App Control 제약 없음 —
  **demoparser2 네이티브 임포트 정상 동작**, 파싱 전부 Windows에서 그대로 실행
  가능. **WSL은 설치돼 있지 않음** (`wsl` 호출 시 "설치되어 있지 않습니다").
- **노트북**: Windows Smart App Control이 켜져 있어 demoparser2 네이티브
  모듈(.pyd)이 차단됨 (DLL load failed). SAC 끄기는 비가역(재설치 필요)이라
  하지 않음. 우회: 파싱 실행은 WSL Ubuntu에서.
  `wsl -e bash scripts/wsl-run.sh <args>` (WSL 쪽 venv는
  `~/.venvs/replay-coach`, uv는 `~/.local/bin/uv`).
- 순수 파이썬 부분(스키마, 분류 로직, 테스트)은 어느 PC에서든 Windows 그대로
  돌아감 (`uv run pytest -q` — demoparser2 import가 지연 로딩이라 안 걸림).
- `web/pipeline.py`는 demoparser2 임포트 성공 여부로 네이티브/WSL 경로를 자동
  선택하므로 두 PC 모두에서 동작.

## 구조
| 경로 | 용도 |
|------|------|
| `Docs/` | 조사·설계 문서 |
| `core/` | 결정 지점(DecisionPoint) 스키마 — 게임 무관 공통 계약 |
| `parser/` | 게임별 리플레이 파서 플러그인 (`parser/cs2/`) |
| `cli.py` | 리플레이 → 결정 지점 추출 CLI |
| `scripts/` | WSL 실행 래퍼 등 |
| `tests/` | pytest (분류 로직·스키마 단위 테스트) |
| `analysis/` | 프로 패턴 DB 구축·비교 엔진·LLM 리뷰 |
| `collect/` | FACEIT 데모 수집 (Data/Downloads API 클라이언트 + 백필 CLI) |
| `web/` | 업로드·리뷰 웹 UI (FastAPI) |

## 규칙
- 확정 안 된 사항은 문서에 "미정"으로 명시 (Rpg-on-Earth에서 승계한 관행).
- 외부 데이터 수집(HLTV/FACEIT 등)은 착수 전 약관 확인을 먼저 한다.
