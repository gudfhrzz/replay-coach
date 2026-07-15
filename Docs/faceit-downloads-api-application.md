# FACEIT Downloads API 신청서 — 제출용 텍스트 (2026-07-15)

> 신청 폼: https://fce.gg/downloads-api-application (심사 약 30일)
> **제출 전 필수**: developers.faceit.com/terms 를 브라우저로 열어 상업적 이용·
> 데이터 보관·파생물(통계 모델) 조항 확인 — Cloudflare 챌린지 때문에 자동 열람 불가.
> (`Docs/pro-demo-collection-tos.md` §2 참고)

아래는 폼에 그대로 붙여 넣을 수 있는 영문 텍스트. 폼 문항이 다르면 섹션을 재조합해서
사용. `[대괄호]` 부분만 실제 정보로 채우면 됨.

---

## Section 1 — What are you building? (Use case)

I am building a replay-coaching web service for CS2 players (working title:
Replay Coach, pre-launch). A player uploads their own demo; the pipeline
extracts discrete decision points — currently team buy decisions per round —
and compares each decision against the statistical distribution of choices
that professional and semi-professional players made in the same situation
(side, economy state, loss-bonus streak). An LLM layer then explains the
comparison in plain language, e.g. "on a 1-round loss streak as T, pros
full-buy 56% of the time and it wins 37% of rounds; your full-eco here is
the minority choice" — coaching on individual decisions rather than raw
aggregate stats.

The methodology is already validated end-to-end: I built a working prototype
against the public ESTA CS:GO dataset (Xenopoulos et al., CC BY-SA 4.0),
extracting ~1,900 economic decisions from pro matches into conditional
distributions. ESTA is CS:GO-era data, so I now need current CS2 demos from
high-level competition to build the production reference database — which is
why I am applying for Downloads API access. FACEIT hosts exactly the level of
play I need (FPL and pro-league matches).

## Section 2 — How will you use and store the data?

- Demos are downloaded via the Downloads API, parsed once into round-level
  decision records (equipment value, team spend, buy classification, round
  outcome, economy context), and aggregated into conditional probability
  distributions.
- Raw .dem files are **never redistributed or made available to end users**,
  and can be deleted after parsing; only derived aggregate statistics are
  retained and served.
- Player and team names are used only for an opt-in "compare against this
  pro's style" filter; no other personal data is extracted or stored.
- Expected volume: an initial backfill of a few thousand pro/FPL demos, then
  incremental downloads of new matches (expected tens per day at most, well
  within rate limits).

## Section 3 — About you / your company

- [이름], solo developer, South Korea. Early-stage / pre-launch project;
  contact: [이메일].
- Working prototype (parser → decision-point extraction → pro-distribution
  comparison engine) is complete and tested; FACEIT demo access is the last
  missing piece for current-game (CS2) data.
- I have reviewed the FACEIT developer terms and will comply with data-use
  and attribution requirements; happy to adjust retention or scope to
  whatever the Downloads API terms require.

---

## 제출 체크리스트

- [ ] developers.faceit.com/terms 브라우저 확인 (상업적 이용·보관·파생물 조항)
- [ ] FACEIT 개발자 계정 생성 + Data API 앱 등록 (Downloads API는 그 위에 승인)
- [ ] `[대괄호]` 채우고 폼 문항에 맞게 섹션 재조합해 제출
- [ ] 제출일 기록 → 30일 후 팔로업
