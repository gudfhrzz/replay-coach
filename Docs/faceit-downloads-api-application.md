# FACEIT Downloads API 신청서 초안 (2026-07-15)

> 신청 폼: https://fce.gg/downloads-api-application (심사 약 30일)
> **제출 전 필수**: developers.faceit.com/terms 를 브라우저로 열어 상업적 이용·
> 데이터 보관·파생물(통계 모델) 조항 확인 — Cloudflare 챌린지 때문에 자동 열람 불가.
> (`Docs/pro-demo-collection-tos.md` §2 참고)

아래는 신청 폼의 유스케이스 서술 섹션에 붙여 넣을 영문 초안. 폼 실제 문항 구성에
맞춰 조정해서 사용.

## Use case description

We are building a replay-coaching web service for CS2 players. A user uploads
their own demo; our pipeline extracts discrete decision points (currently:
team buy decisions per round) and compares each decision against the
statistical distribution of choices professional and semi-professional players
made in the same situation (side, economy state, loss streak). An LLM layer
then explains the comparison in plain language — "in this spot, pros full-buy
88% of the time" — rather than raw stats.

We need the Downloads API to obtain match demos from FACEIT's professional
and semi-professional competitions (e.g. FPL) to build this reference
distribution. We do not redistribute demo files; demos are parsed once into
aggregate per-round statistics and then can be deleted.

## Data usage & storage

- Demos are downloaded, parsed into round-level economic decision records
  (equipment value, spend, buy classification, round outcome), and aggregated
  into conditional distributions. Raw .dem files are not redistributed and can
  be deleted after parsing.
- Aggregated statistics are stored in our own database and served to end users
  as coaching feedback (distribution shares and win rates), with player/team
  identity used only where we offer "compare against this pro's style"
  filtering.
- Expected volume: initial backfill of a few thousand demos, then incremental
  downloads of new pro-league matches (tens per day at most).

## About us

- Solo developer / early-stage project, pre-launch. (필요 시 실명·연락처 기입)
- Prototype pipeline already working end-to-end against the public ESTA
  CS:GO dataset (CC BY-SA 4.0); FACEIT demos are needed for current CS2 data.

## 제출 체크리스트

- [ ] developers.faceit.com/terms 브라우저 확인 (상업적 이용·보관·파생물 조항)
- [ ] FACEIT 개발자 계정 생성 + Data API 앱 등록 (Downloads API는 그 위에 승인)
- [ ] 위 초안을 폼 문항에 맞게 조정해 제출
- [ ] 제출일 기록 → 30일 후 팔로업
