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

## 현재 상태 (2026-07-14)
- **시작 게임 = CS2 확정.** 확장 트랙 = Riot 계열(LoL+TFT 묶음, API 인프라 공유).
  오버워치는 데이터 접근성 문제로 제외. 근거: `Docs/game-selection.md`
- **파이프라인 v0 완료**: .dem → 라운드별 팀 바이 결정(DecisionPoint JSONL).
  demoparser2 공식 테스트 데모로 E2E 검증됨. 실행법은 README 참고.
- 미정: 서비스명(폴더명 replay-coach는 가칭), MVP 도메인 확정(경제 판단으로 v0
  구현했으나 공식 확정은 아직).
- 프로 데모 수집 약관 확인 완료: HLTV 자동 수집 금지(제외), FACEIT Downloads API가
  공식 경로(신청 후 30일 심사), ESTA 데이터셋(CC BY-SA 4.0)은 즉시 사용 가능.
  상세: `Docs/pro-demo-collection-tos.md`
- 다음 단계: ESTA로 경제 결정 프로 분포 프로토타입(`analysis/`) + FACEIT
  Downloads API 신청(사용자가 개발자 ToS 브라우저 확인 후 제출).

## 환경 제약 (이 개발 PC)
- **Windows Smart App Control이 켜져 있어 demoparser2 네이티브 모듈(.pyd)이
  차단됨** (DLL load failed). SAC 끄기는 비가역(재설치 필요)이라 하지 않음.
- 우회: 파싱 실행은 WSL Ubuntu에서. `wsl -e bash scripts/wsl-run.sh <args>`
  (WSL 쪽 venv는 `~/.venvs/replay-coach`, uv는 `~/.local/bin/uv`).
- 순수 파이썬 부분(스키마, 분류 로직, 테스트)은 Windows에서도 그대로 돌아감
  (`uv run pytest -q` 가능 — demoparser2 import가 지연 로딩이라 안 걸림).

## 구조
| 경로 | 용도 |
|------|------|
| `Docs/` | 조사·설계 문서 |
| `core/` | 결정 지점(DecisionPoint) 스키마 — 게임 무관 공통 계약 |
| `parser/` | 게임별 리플레이 파서 플러그인 (`parser/cs2/`) |
| `cli.py` | 리플레이 → 결정 지점 추출 CLI |
| `scripts/` | WSL 실행 래퍼 등 |
| `tests/` | pytest (분류 로직·스키마 단위 테스트) |
| (예정) `analysis/` | 프로 패턴 DB 구축·비교 엔진 |
| (예정) `web/` | 업로드·리뷰 UI |

## 규칙
- 확정 안 된 사항은 문서에 "미정"으로 명시 (Rpg-on-Earth에서 승계한 관행).
- 외부 데이터 수집(HLTV/FACEIT 등)은 착수 전 약관 확인을 먼저 한다.
