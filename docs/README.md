# Course deliverables: CSCI441, Team AO3 (SuperAsk)

Everything submitted for the course is here, grouped by deliverable. The
prototype's code is the rest of the repository; see the
[top-level README](../README.md) for how to run it.

```
docs/
  proposal/        project proposal
  report-1/        Report One (both parts, full export, use cases)
  report-2/        Report Two (full report, diagram hand-off pages)
    diagrams/      Mermaid sources, PNGs, and the page build scripts
  demo-1/          Demo 1 brochure, documentation, contributions
    slides/        presentation source, built deck, and PDF
```

## Proposal: [`proposal/`](proposal/)

| Deliverable | File |
|---|---|
| Project proposal | `CSCI441-TeamAO3-ProjectProposal.pdf` |

## Report One: [`report-1/`](report-1/)

| Deliverable | File |
|---|---|
| Part One | `CSCI441-TeamAO3-ReportOne-PartOne.pdf` |
| Part Two | `CSCI441-TeamAO3-ReportOne-PartTwo.pdf` |
| Full Report One (team Doc export, 2026-10-22; has the user-effort estimates and Figure 11 that Report Two cites) | `CSCI441-TeamAO3-ReportOne-Full.pdf` |
| Section 3c use cases (hand-off page) | `SuperAsk-3c-use-cases.html` |
| Use case diagram | `superask-use-case-diagram.png` |

## Report Two: [`report-2/`](report-2/)

| Deliverable | File |
|---|---|
| Full Report Two (revised 2026-10-22: no officer escalation, private-project framing, corrected Sections 5 and 6) | `CSCI441-TeamAO3-ReportTwo.pdf` |
| Part One: interaction (sequence) diagrams, Figures 8–12 | `SuperAsk-report2-interaction-diagrams.html` |
| Part Two, Section 2: class diagram and interface specification | `SuperAsk-report2-class-diagram.html` |
| Diagram sources and build scripts | [`diagrams/`](report-2/diagrams/README.md) |

The `.html` pages are self-contained (images embedded), so they open directly
in a browser.

## Demo 1: [`demo-1/`](demo-1/)

| Deliverable | File |
|---|---|
| Slides (present in a browser; see [`slides/README.md`](demo-1/slides/README.md)) | `slides/index.html` |
| Slides as PDF | `slides/SuperAsk-Demo1.pdf` |
| Brochure | `SuperAsk-Demo1-brochure.pdf` |
| Technical documentation | `SuperAsk-Demo1-technical-documentation.pdf` |
| User documentation | `SuperAsk-Demo1-user-documentation.pdf` |
| Individual contributions | `SuperAsk-Demo1-individual-contributions.pdf` |
| Integration tests (code, in the test tree) | [`../tests/integration/`](../tests/integration/README.md) |

## Keeping this folder safe

`scripts/sync-from-bunkheang.ps1` resets `main` to the upstream code repo and
restores only `docs/`, `tests/integration/` and the sync script itself. Put any
new course material under `docs/` or a sync will delete it.
