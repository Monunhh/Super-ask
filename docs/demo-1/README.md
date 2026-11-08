# Demo 1: SuperAsk.AI (CSCI441, Team AO3)

This folder is the Demo 1 e-archive, laid out the way the
[Demo 1 requirements](https://eceweb1.rutgers.edu/~marsic/Teaching/SE/demo1.html)
ask for. Submit the link to this folder:
<https://github.com/Monunhh/Super-ask/tree/main/docs/demo-1>

```
docs/demo-1/
  1_code/                  README1.txt: where the code is and how to run it
  2_unit_testing/          README2.txt: where the unit tests are and how to run them
  3_integration_testing/   integration test code + README3.txt
  4_data_collection/       README4.txt: data collection scripts and how to run them
  5_documentation/         the five required PDFs
    technical_documentation.pdf
    user_documentation.pdf
    brochure.pdf
    presentation_slides.pdf
    individual_contributions.pdf
  slides/                  source of presentation_slides.pdf (HTML deck, build.py)
```

`1_code`, `2_unit_testing` and `4_data_collection` hold a README rather than a
copy of the code. Next.js needs its source at the repository root, so a copy
here would be a second, stale version. The requirements say anything that does
not apply must be explained in `individual_contributions.pdf`, so that PDF
needs a sentence saying so (see the checklist below).

---

## Deadlines (relative to the demo date)

| What | When |
|---|---|
| Demo video uploaded to YouTube (≤ 20 min) | 2 days **before** the demo, 11:59 PM |
| Email to instructor + TA: video link, brochure, slides | right after the upload |
| Demo slot: Q&A (10–15 min), then private discussion (15 min) | demo day |
| Contribution breakdown email, all members copied | right after the demo |
| E-archive (this folder) complete and public | 2 days **after** the demo |

The documents in this folder are dated **9 Nov 2026**. If that is the demo
date, the video was due **7 Nov** and the e-archive is due **11 Nov 2026**.

---

## Checklist: what we have and what is missing

✅ done · ⚠️ exists but does not meet the requirement · ❌ missing

### E-archive folders

| Item | Status | Notes |
|---|---|---|
| `1_code` + README1.txt | ✅ | Points to the code at the repo root, with run steps |
| `2_unit_testing` + README2.txt | ✅ | Points to `tests/`; 643 tests passing on 2026-11-09 |
| `3_integration_testing` + README3.txt | ✅ | 9 tests passing; `npm run test:integration` |
| `4_data_collection` + README4.txt | ✅ | Registry builder, crawler, how to run |
| Repo is public | ✅ | Graders must not need a login |

### Required documents (`5_documentation/`, PDF only, each with a cover page)

| Document | Status | What needs fixing |
|---|---|---|
| `technical_documentation.pdf` | ⚠️ | Has a cover page. Still says "slides/ and documentation/" and "README3.txt … after relocating", both now stale; should point to `docs/demo-1/`. Says the test counts "should be verified": replace with the real numbers (643 unit, 9 integration). Says Node.js 24; CI uses Node 22. "Codebase reviewed: … ZIP" reads like a review, not our own documentation. No table of contents. |
| `user_documentation.pdf` | ⚠️ | Content is good. Needs a table of contents; the cover says "Codebase reviewed: … ZIP", which doesn't fit a user guide. |
| `brochure.pdf` | ⚠️ | One page with title, date, team, features and URLs. **Missing "system requirements to run the system"** (required). Lists first names only: use full names. Add the GitHub URL. Says "610 unit tests and 33 integration tests", which doesn't match the archive (643 unit, 9 in `3_integration_testing`). |
| `presentation_slides.pdf` | ⚠️ | **20 slides; the requirement is at most 5** (overview and roadmap), followed by a live demo of the use cases and a short plan. 8 slides are about unit/integration testing, and `b-example` shows test source code ("avoid showing source code"). Same 610/33 count mismatch. |
| `individual_contributions.pdf` | ⚠️ | Covers all 6 members and project management (coordination, plan of work, responsibilities, Gantt). **No cover page.** **No percentages** (or a statement that everyone agrees on equal contribution). **No note on non-applicable items** (code kept at the repo root) and how to reallocate those points. |

### Demo and presentation (not in the repo, so tick these off yourselves)

| Item | Status |
|---|---|
| Demo video, one for the whole team, ≤ 20 minutes, on YouTube | ❌ not linked anywhere in the repo |
| Email to instructor + TA with the YouTube link, brochure and slides | ❌ not recorded |
| Slides cut to ≤ 5: who it's for, what it is, roadmap of the talk | ❌ |
| Live demo of the most important use cases (Reports 1–2: UC-1 ask a question, UC-2 retrieve official sources, UC-3 view citation, UC-7 office contact and location, UC-11 refresh content), **each presented by its product owner** from Report 1 | ❌ the current agenda is split by topic (architecture, unit tests, …), not by use case |
| For each use case: what it does, which business goal it serves, a user scenario, key UI and back-end points | ❌ |
| Short plan for the rest of the semester (`y-next` slide or Report 1 Plan of Work) | ✅ `y-next` slide |
| Any accounts, profiles and sample records created **before** the demo; no live record creation; little time on login | ❌ to prepare |
| Charts show labels and units on the axes | check `d-data`, `h-eval`, `b-coverage` |
| Every member can run the demo and answer questions; rehearsal done | ❌ to schedule |
| Laptop + projector / Zoom tested before the slot | ❌ to do |
| All members present at the demo (an absence needs a justified reason) | — |
| Contribution breakdown emailed after the demo, all members copied | ❌ |

---

## Rebuilding the slides

The deck source is in `slides/` (see [`slides/README.md`](slides/README.md)).
`python3 docs/demo-1/slides/build.py --pdf` rebuilds `slides/index.html` and
writes `5_documentation/presentation_slides.pdf`.
