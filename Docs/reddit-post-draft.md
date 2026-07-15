# 레딧 포스트 초안 — 아이디어 검증 + 초기 관심 확보 (2026-07-15)

> 목적: 출시 전 수요 검증 + 피드백 수집. 아직 보여줄 링크/스크린샷이 없으므로
> "만들고 있는데 의견 달라" 포맷이 자연스럽고 자기홍보 규정에도 안전함.
>
> 후보 서브레딧 (규칙은 게시 직전에 브라우저로 재확인):
> - **r/LearnCSGO** — 코칭 주제와 정확히 일치, 규칙 느슨. 1순위.
> - **r/GlobalOffensive** — 트래픽 최대지만 자기홍보 엄격(9:1 규칙, 데브 포스트는
>   dev-flair 필요할 수 있음). 프로토타입 스크린샷이 생긴 뒤가 나음.
> - r/cs2 — 소규모지만 부담 없음.
>
> 팁: 링크 넣지 말 것(아직 없기도 함). 질문으로 끝내면 댓글이 잘 달림.
> 게시 시간대는 EU 저녁~미국 오후(한국 새벽~아침)가 CS 서브레딧 피크.

---

## 제목 후보 (하나 선택)

1. I'm building a tool that compares your demo decisions to what pros did in
   the same situation — what decisions would you want reviewed?
2. Would you use this? Upload your demo → see how pros handled the exact same
   buy-round situations
3. Building an AI demo-review tool that answers "what would a pro have done
   here?" — looking for feedback before I go further

## 본문

Hey everyone,

I've been working on a replay-coaching tool and I'd love a sanity check from
actual players before I sink more months into it.

**The idea:** you upload your demo, and instead of the usual stat dashboard
(ADR, K/D graphs, heatmaps), the tool pulls out individual *decisions* you
made and shows you the distribution of what pros did in the same spot. First
domain I built is buy decisions. Example output from my prototype:

> Round 3, T side, 1-round loss streak — you full-eco'd.
> Pros in this spot: full-buy 56% (wins 37% of rounds), semi-buy 22%
> (wins 46%), semi-eco 11% (wins 10%).

So it's not "you did X wrong," it's "here's what the people who are best at
this game actually do here, and how often it works." An LLM layer on top
turns that into readable coaching notes.

The stats engine works end-to-end already (built the pro distribution from
~1,900 pro-match buy decisions). Two things I'm deliberately doing
differently from existing tools:

1. **Decision-level, not stat-level.** Leetify/Scope tell you your numbers
   are low; I want to point at the specific round and say what the
   alternatives were.
2. **Rank context (planned).** Blindly copying pros can be wrong at lower
   ranks — a pro-approved eco assumes teammates who actually save. Long-term
   I want "pros do X, but at your rank Y wins more."

**My questions for you:**

- Beyond buy decisions, what decisions would you actually want reviewed?
  (retake vs. save? rotation timing? utility usage?)
- Do you trust "pros do X% of the time" as coaching evidence, or does it feel
  like noise without more context?
- What did existing tools (Leetify etc.) fail to tell you that made you stop
  using them — or what keeps you using them?

Not selling anything, nothing to link yet — genuinely trying to figure out if
this is worth building before I build the web app around it. Brutal honesty
welcome.

---

## 짧은 버전 (r/cs2 등 가벼운 서브레딧용)

**Title:** Building a demo-review tool that shows what pros did in your exact
situation — what would you want it to review?

Working on a tool where you upload a demo and it compares your in-round
decisions (starting with buys) to the actual distribution of pro choices in
the same situation — side, economy, loss streak. E.g. "you eco'd here; pros
full-buy 56% in this spot and it wins 37% of rounds."

Stats engine already works on ~1,900 pro-match decisions. Before I build the
rest: what decisions would *you* want reviewed — retakes, saves, rotations,
utility? And would pro-distribution numbers actually change how you play, or
is it just trivia?

---

## 게시 후 할 일

- [ ] 게시 첫 2시간 내 댓글에 성실히 답변 (초기 참여가 노출을 결정)
- [ ] 반복해서 나오는 요청 도메인 → `Docs/`에 기록, MVP 도메인 확정 근거로 사용
- [ ] 관심 표한 유저는 추후 베타 테스터 후보로 (DM 리스트)
