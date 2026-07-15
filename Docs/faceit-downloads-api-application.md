# FACEIT Downloads API 신청서 — 제출용 텍스트 (2026-07-15)

> **진행 상황**: 개발자 계정 가입이 2FA 활성화 + identity verification을 요구해서
> 노트북에서 막힘 (2026-07-15). CS2 설치된 데스크탑에서 이어서 진행 —
> 체크리스트: https://github.com/gudfhrzz/replay-coach/issues/1
>
> 신청 폼: https://fce.gg/downloads-api-application (심사 약 30일)
> **제출 전 필수**: developers.faceit.com/terms 를 브라우저로 열어 상업적 이용·
> 데이터 보관·파생물(통계 모델) 조항 확인 — Cloudflare 챌린지 때문에 자동 열람 불가.
> (`Docs/pro-demo-collection-tos.md` §2 참고)

아래는 폼에 그대로 붙여 넣을 수 있는 영문 텍스트. 폼 문항이 다르면 섹션을 재조합해서
사용. `[대괄호]` 부분만 실제 정보로 채우면 됨.

---

## Section 0 — 사전 준비: App ID + Server-Sided API Key (폼 필수 입력값)

신청 폼이 **App ID**와 **Server-Sided API Key 이름**을 요구함 — Downloads API
승인이 기존 앱/키에 스코프를 붙여주는 방식이기 때문. 아래 순서로 만들면 됨
(전부 브라우저 작업, 5분 정도):

1. https://developers.faceit.com 접속 → FACEIT 계정으로 로그인
   (계정 없으면 faceit.com에서 먼저 생성)
2. **App Studio** 섹션 → **Create App** (새 앱 생성)
   - 앱 이름: `Replay Coach` ← 신청서 본문의 working title과 일치시킬 것
   - 설명은 Section 1 첫 문단을 한 줄로 요약해서 입력
3. 생성된 앱의 상세 페이지에서 **App ID** (UUID 형식) 복사 → 폼에 입력
4. 같은 앱 상세 페이지의 **API Keys** 패널 → 새 키 생성
   - 타입: **Server side** (Python 백엔드에서 쓸 것이므로)
   - 키 이름: `replay-coach-downloads` ← 이 이름을 폼의
     "Server-Sided API Key name"에 입력
5. 발급된 키 값은 로컬에 안전하게 보관 (`.env` 등 — **절대 git에 커밋 금지**;
   `.gitignore`에 `.env` 추가돼 있는지 확인)

> 참고: 승인 전에도 이 키로 Data API(매치 목록·데모 URL 조회)는 바로 쓸 수 있음.
> Downloads API(실제 .dem 다운로드)만 승인 후 열림. 급하면 developers@faceit.com.

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
- [ ] Section 0 수행: 개발자 계정 → App Studio에서 `Replay Coach` 앱 생성 →
      App ID 확보 → server-side 키 `replay-coach-downloads` 생성
- [ ] API 키 값 로컬 `.env`에 보관 (git 커밋 금지)
- [ ] 폼에 App ID + 키 이름 입력, `[대괄호]` 채우고 섹션 재조합해 제출
- [ ] 제출일 기록 → 30일 후 팔로업
