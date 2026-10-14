# Report Two diagram sources

Mermaid sources, rendered PNGs, and the scripts that assemble the hand-off
pages in `../reports/`.

| Files | What |
|---|---|
| `uc1-*.mmd` … `uc11-*.mmd` + `.png` | Sequence diagrams for UC-1, UC-2, UC-3, UC-7, UC-11 (Figures 8–12) |
| `class-overview.mmd` + `.png` | Full class diagram |
| `class-a-*.mmd` … `class-d-*.mmd` + `.png` | Partial class diagrams per use-case group |
| `mermaid-config.json` | Shared Mermaid theme (Arial, sequence spacing) |
| `build_handoff.py` | Writes `../reports/SuperAsk-report2-interaction-diagrams.html` |
| `build_class_handoff.py` | Writes `../reports/SuperAsk-report2-class-diagram.html` |

## Rebuild

1. Render each `.mmd` to a `.png` with Mermaid 11 (headless Chrome or the
   Mermaid CLI), passing `mermaid-config.json` as the config.
2. Run `python build_handoff.py` and `python build_class_handoff.py` from this
   folder. Each embeds the PNGs as data URIs and overwrites its page in
   `../reports/`.
