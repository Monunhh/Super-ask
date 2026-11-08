#!/usr/bin/env python3
"""Build the Demo 1 documents in ../5_documentation/ from the HTML here.

    python3 docs/demo-1/documents/build.py

Needs Google Chrome (or Chromium). If the pypdf package is installed
(pip install pypdf), the table of contents gets page numbers: the page is
printed once, the page of each heading is read back from the PDF, and the page
is printed again with the numbers filled in. Without pypdf, the contents list
is printed without page numbers.

The Gantt chart in individual_contributions.html is drawn here (see gantt_svg)
and put in place of the {{GANTT}} marker.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "5_documentation"))
DOCS = ["technical_documentation", "user_documentation", "individual_contributions"]


def find_chrome():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def print_pdf(chrome, html_path, pdf_path):
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={profile}",
             "--no-pdf-header-footer", "--virtual-time-budget=10000", f"--print-to-pdf={pdf_path}",
             "file://" + html_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180,
        )


# ── Gantt chart ──────────────────────────────────────────────────────────────

GANTT_TASKS = [
    # (label, start, end, done)  end == start draws a milestone
    ("Requirements and Report 1", date(2026, 9, 21), date(2026, 9, 30), True),
    ("Report 2 Part 1", date(2026, 10, 1), date(2026, 10, 6), True),
    ("Report 2 Part 2", date(2026, 10, 7), date(2026, 10, 12), True),
    ("Full Report 2", date(2026, 10, 13), date(2026, 10, 21), True),
    ("Demo 1 implementation", date(2026, 10, 22), date(2026, 11, 1), True),
    ("Demo 1 tests, slides, documents", date(2026, 11, 2), date(2026, 11, 8), True),
    ("Demo 1", date(2026, 11, 9), date(2026, 11, 9), True),
    ("Report 3 Part 1", date(2026, 11, 10), date(2026, 11, 16), False),
    ("Full Report 3", date(2026, 11, 17), date(2026, 11, 23), False),
    ("Final refinements", date(2026, 11, 24), date(2026, 12, 3), False),
    ("Demo 2", date(2026, 12, 4), date(2026, 12, 4), False),
]
GANTT_START, GANTT_END = date(2026, 9, 21), date(2026, 12, 7)
GANTT_TICKS = [date(2026, 9, 21), date(2026, 10, 5), date(2026, 10, 19), date(2026, 11, 2),
               date(2026, 11, 16), date(2026, 11, 30)]
TODAY = date(2026, 11, 9)


def gantt_svg():
    W, label_w, row_h, top = 680, 190, 22, 28
    plot_w = W - label_w - 10
    span = (GANTT_END - GANTT_START).days
    x = lambda d: label_w + (d - GANTT_START).days / span * plot_w
    H = top + row_h * len(GANTT_TASKS) + 44
    bottom = top + row_h * len(GANTT_TASKS)
    done, planned, ink, muted, rule = "#4b3fa8", "#c9c4ec", "#16161f", "#55556a", "#d9d9e3"
    font = 'font-family="Helvetica Neue, Arial, sans-serif"'
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-label="Gantt chart of the project schedule, 21 September to 4 December 2026">']
    for t in GANTT_TICKS:
        out.append(f'<line x1="{x(t):.1f}" y1="{top - 6}" x2="{x(t):.1f}" y2="{bottom}" stroke="{rule}"/>')
        out.append(f'<text x="{x(t):.1f}" y="{bottom + 14}" font-size="10" fill="{muted}" text-anchor="middle" {font}>'
                   f'{t.strftime("%b")} {t.day}</text>')
    out.append(f'<line x1="{label_w}" y1="{bottom}" x2="{label_w + plot_w}" y2="{bottom}" stroke="{ink}"/>')
    out.append(f'<text x="{label_w + plot_w / 2:.1f}" y="{bottom + 34}" font-size="10.5" fill="{ink}" '
               f'text-anchor="middle" font-weight="600" {font}>Date (2026, ticks every two weeks)</text>')
    tx = x(TODAY)
    out.append(f'<line x1="{tx:.1f}" y1="{top - 14}" x2="{tx:.1f}" y2="{bottom}" stroke="#c0392b" stroke-dasharray="3 3"/>')
    out.append(f'<text x="{tx + 4:.1f}" y="{top - 16}" font-size="10" fill="#c0392b" {font}>Today: Demo 1, Nov 9</text>')
    for i, (label, s, e, is_done) in enumerate(GANTT_TASKS):
        y = top + i * row_h
        cy = y + row_h / 2
        out.append(f'<text x="0" y="{cy + 3.5:.1f}" font-size="10.5" fill="{ink}" {font}>{label}</text>')
        fill = done if is_done else planned
        if s == e:
            cx = x(s)
            out.append(f'<path d="M{cx:.1f} {cy - 6:.1f} L{cx + 6:.1f} {cy:.1f} L{cx:.1f} {cy + 6:.1f} '
                       f'L{cx - 6:.1f} {cy:.1f} Z" fill="{fill}" stroke="{done}"/>')
        else:
            x0, x1 = x(s), x(e + (date(2000, 1, 2) - date(2000, 1, 1)))
            out.append(f'<rect x="{x0:.1f}" y="{y + 5}" width="{x1 - x0:.1f}" height="{row_h - 10}" rx="2" fill="{fill}"/>')
    out.append("</svg>")
    return "\n".join(out)


# ── Table of contents page numbers ───────────────────────────────────────────

def squash(s):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s)).lower()


def toc_pages(pdf_path, entries):
    """Map each TOC entry id to the first page (1-based) after the contents
    page whose text contains that heading."""
    from pypdf import PdfReader
    pages = [squash(p.extract_text() or "") for p in PdfReader(pdf_path).pages]
    found, start = {}, 2  # page 1 is the cover, page 2 the contents
    for ident, title in entries:
        key = squash(title)
        for i in range(start, len(pages)):
            if key in pages[i]:
                found[ident] = i + 1
                start = i
                break
    return found


def build(chrome, name):
    src = os.path.join(HERE, name + ".html")
    pdf = os.path.join(OUT_DIR, name + ".pdf")
    with open(src, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{GANTT}}", gantt_svg())
    # TOC entries: <a href="#id">Title</a> ... <span class="pg" data-for="id"></span>
    entries = re.findall(r'<a href="#([\w-]+)">([^<]+)</a>', html.split('class="toc"', 1)[-1].split("</nav>", 1)[0])
    tmp = os.path.join(HERE, f".{name}.tmp.html")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html)
        print_pdf(chrome, tmp, pdf)
        try:
            found = toc_pages(pdf, entries)
        except ImportError:
            found = {}
            print("  (pypdf not installed: contents printed without page numbers)")
        if found:
            for ident, page in found.items():
                html = html.replace(f'<span class="pg" data-for="{ident}"></span>',
                                    f'<span class="pg" data-for="{ident}">{page}</span>')
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(html)
            print_pdf(chrome, tmp, pdf)
            missing = [i for i, _ in entries if i not in found]
            if missing:
                print("  headings not found in the PDF:", ", ".join(missing))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"Wrote {pdf}")


def main():
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome not found: install Google Chrome or Chromium to make the PDFs.")
    names = [a for a in sys.argv[1:] if a in DOCS] or DOCS
    for name in names:
        build(chrome, name)


if __name__ == "__main__":
    main()
