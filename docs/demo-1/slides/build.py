"""Build docs/demo-1/slides/index.html — a self-contained presentation of the Demo 1 deck.

    python3 docs/demo-1/slides/build.py          # index.html
    python3 docs/demo-1/slides/build.py --pdf    # index.html + ../5_documentation/presentation_slides.pdf (needs Chrome)

Reads deck.json (slide order, title, fonts) and every <id>.html slide in this
folder, and writes index.html: one file, no server, no install. Open it in a
browser and it starts presenting. Edit the slide files, then re-run this.
"""
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# The submitted slides PDF lives in the e-archive documentation folder.
PDF_NAME = "presentation_slides.pdf"
PDF_REL = "../5_documentation/" + PDF_NAME
# Where the PDF lives online; used when the page is not opened as a local file.
PDF_URL = "https://github.com/Monunhh/Super-ask/raw/main/docs/demo-1/5_documentation/" + PDF_NAME

# Line icons (24×24, stroke = currentColor) for the deck format's <x-icon name>.
ICONS = {
    "Book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "Chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "Check": '<polyline points="20 6 9 17 4 12"/>',
    "CheckCircle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "Clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "Code": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "Globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "Lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "PaperPlane": '<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>',
    "Play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "Search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "Settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "Users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "Warning": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "Wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
}

CSS = r"""
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: #0B0A1A; overflow: hidden; font-family: Inter, Arial, sans-serif; }
body.idle, body.idle * { cursor: none !important; }

/* ── Stage: one 1920×1080 canvas, scaled to fit and centred ─────────────── */
#stage { position: fixed; inset: 0; }
#deck { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: center center; }
.slide { position: absolute; inset: 0; opacity: 0; visibility: hidden; transition: opacity .45s ease, visibility 0s linear .45s; }
.slide.active { opacity: 1; visibility: visible; transition: opacity .45s ease; }

/* ── The slide format (inline styles carry the design; these are defaults) ─ */
.canvas section { position: relative; width: 1920px; height: 1080px; overflow: hidden; margin: 0; }
.canvas h1, .canvas h2, .canvas h3, .canvas p, .canvas ul, .canvas ol { margin: 0; }
.canvas h1 { font-size: 96px; font-weight: 600; line-height: 1.1; }
.canvas h2 { font-size: 64px; font-weight: 600; line-height: 1.15; }
.canvas h3 { font-size: 44px; font-weight: 600; line-height: 1.2; }
.canvas p { font-size: 32px; line-height: 1.4; }
/* A div with no display of its own is a column; one that sets display:flex
   keeps CSS's default row direction, as in the deck format. */
.canvas div:not([style*="display"]) { display: flex; flex-direction: column; }
.canvas ul, .canvas ol { padding-left: 1.2em; }
.canvas table { border-collapse: collapse; width: 100%; }
.canvas th, .canvas td { padding: .35em .6em; border-bottom: 1px solid #E3E9F0; text-align: left; vertical-align: top; }
.canvas th { font-weight: 600; }
.canvas aside { display: none; }
x-icon { display: inline-block; flex: none; }
x-icon svg { display: block; width: 100%; height: 100%; }
x-shape { display: inline-block; flex: none; }
x-shape[kind="arrow-right"] { clip-path: polygon(0 30%, 60% 30%, 60% 0, 100% 50%, 60% 100%, 60% 70%, 0 70%); }
x-shape[kind="arrow-left"] { clip-path: polygon(100% 30%, 40% 30%, 40% 0, 0 50%, 40% 100%, 40% 70%, 100% 70%); }
x-shape[kind="ellipse"] { border-radius: 50%; }
x-shape[kind="rounded"] { border-radius: 16px; }

/* ── HUD: progress bar + counter, fade out while idle ───────────────────── */
#progress { position: fixed; left: 0; right: 0; bottom: 0; height: 4px; background: rgba(255,255,255,.08); z-index: 5; }
#progress span { display: block; height: 100%; width: 0; background: linear-gradient(90deg, #4F3FA8, #9D8CF2); transition: width .35s ease; }
#counter { position: fixed; right: 20px; bottom: 16px; z-index: 5; font: 600 13px/1 Inter, Arial, sans-serif; color: #fff; background: rgba(23,25,54,.72); padding: 8px 12px; border-radius: 999px; letter-spacing: .02em; backdrop-filter: blur(6px); }
#hint { position: fixed; left: 50%; bottom: 18px; transform: translateX(-50%); z-index: 5; font: 500 13px/1 Inter, Arial, sans-serif; color: #fff; background: rgba(23,25,54,.72); padding: 9px 14px; border-radius: 999px; transition: opacity .6s ease; backdrop-filter: blur(6px); }
#hint.gone { opacity: 0; pointer-events: none; }
#dl { position: fixed; right: 20px; top: 16px; z-index: 5; display: inline-flex; align-items: center; gap: 8px; font: 600 13px/1 Inter, Arial, sans-serif; color: #fff; text-decoration: none; background: rgba(79,63,168,.9); padding: 9px 14px; border-radius: 999px; transition: opacity .4s ease, background .15s; backdrop-filter: blur(6px); }
#dl:hover { background: #4F3FA8; }
#dl svg { width: 15px; height: 15px; }
#counter, #progress { transition: opacity .4s ease; }
body.idle #counter, body.idle #dl { opacity: 0; }

/* ── Overlays ────────────────────────────────────────────────────────────── */
.overlay { position: fixed; inset: 0; z-index: 20; }
.overlay[hidden] { display: none !important; }
#notes { inset: auto 0 0 0; max-height: 34vh; overflow: auto; background: rgba(11,10,26,.94); color: #EDEAFB; font: 400 20px/1.6 Inter, Arial, sans-serif; padding: 20px 28px 28px; border-top: 3px solid #4F3FA8; }
#notes b { color: #B8ACF7; font-size: 13px; letter-spacing: .1em; text-transform: uppercase; display: block; margin-bottom: 6px; }
#overview { background: #0B0A1A; overflow: auto; padding: 32px; }
#overview h2 { color: #fff; font: 700 22px 'Space Grotesk', Inter, sans-serif; margin: 0 0 20px; }
#overview .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }
.thumb { position: relative; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 10px; cursor: pointer; outline: 2px solid transparent; outline-offset: 3px; transition: outline-color .15s, transform .15s; background: #fff; }
.thumb:hover { transform: translateY(-2px); outline-color: #6D5BD0; }
.thumb.current { outline-color: #9D8CF2; }
.thumb .canvas { width: 1920px; height: 1080px; transform-origin: 0 0; pointer-events: none; }
.thumb .num { position: absolute; left: 8px; top: 8px; z-index: 2; font: 600 12px/1 Inter, sans-serif; color: #fff; background: rgba(23,25,54,.8); padding: 5px 8px; border-radius: 6px; }
#help { display: grid; place-items: center; background: rgba(11,10,26,.86); }
#help .card { background: #fff; color: #101828; border-radius: 16px; padding: 28px 32px; width: min(560px, 92vw); font: 400 15px/1.5 Inter, Arial, sans-serif; box-shadow: 0 24px 80px rgba(0,0,0,.4); }
#help h2 { font: 700 22px 'Space Grotesk', Inter, sans-serif; margin: 0 0 14px; }
#help table { width: 100%; border-collapse: collapse; }
#help td { padding: 6px 0; border-bottom: 1px solid #F1F5F9; }
#help td:first-child { width: 46%; }
kbd { font: 600 12px ui-monospace, Menlo, monospace; background: #F3F0FF; color: #3F3289; border: 1px solid #D4CCF7; border-bottom-width: 2px; border-radius: 6px; padding: 2px 7px; margin-right: 4px; }
#blackout { background: #000; z-index: 30; }

/* ── Presenter view (opened with S, in its own window) ─────────────────── */
#presenter { position: fixed; inset: 0; display: grid; grid-template-columns: 1.6fr 1fr; grid-template-rows: auto 1fr; gap: 16px; padding: 16px; background: #0B0A1A; color: #EDEAFB; font-family: Inter, Arial, sans-serif; }
#presenter[hidden] { display: none; }
#presenter header { grid-column: 1 / -1; display: flex; align-items: center; gap: 16px; }
#presenter .timer { font: 700 34px/1 'Space Grotesk', Inter, sans-serif; color: #fff; min-width: 120px; }
#presenter .clock, #presenter .pos { font-size: 15px; color: #B8ACF7; }
#presenter header .spacer { flex: 1; }
#presenter button { font: 600 14px Inter, sans-serif; color: #fff; background: #2A2160; border: 1px solid #4F3FA8; border-radius: 8px; padding: 8px 14px; cursor: pointer; }
#presenter button:hover { background: #4F3FA8; }
#presenter .label { font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: #8A80B8; margin-bottom: 8px; }
#presenter .col { display: flex; flex-direction: column; min-height: 0; }
.view { position: relative; width: 100%; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 10px; background: #fff; }
.view .canvas { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }
#p-notes { flex: 1; overflow: auto; margin-top: 16px; background: #14122E; border-radius: 10px; padding: 18px 20px; font-size: 22px; line-height: 1.55; }
#p-next.end { display: grid; place-items: center; color: #8A80B8; background: #14122E; font-size: 16px; }

@media (prefers-reduced-motion: reduce) { .slide, .slide.active, #progress span { transition: none; } }

/* ── Print / Save as PDF: one slide per page ───────────────────────────── */
@page { size: 1920px 1080px; margin: 0; }
@media print {
  html, body { overflow: visible; height: auto; background: #fff; }
  #stage { position: static; }
  #deck { position: static; transform: none !important; height: auto; }
  .slide { position: relative; opacity: 1; visibility: visible; break-after: page; height: 1080px; }
  #progress, #counter, #hint, #dl, .overlay, #presenter { display: none !important; }
}
"""

JS = r"""
(function () {
  var slides = Array.prototype.slice.call(document.querySelectorAll('#deck .slide'));
  var N = slides.length, cur = 0;
  var isPresenter = /[?&]presenter\b/.test(location.search);

  // Online (any viewer or host) the PDF comes from GitHub; locally, from this folder.
  var dl = document.getElementById('dl');
  if (dl && location.protocol !== 'file:') dl.href = dl.getAttribute('data-online');

  // Real icons for <x-icon name="…">.
  document.querySelectorAll('x-icon').forEach(function (el) {
    var p = ICONS[el.getAttribute('name')];
    if (p) el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + '</svg>';
  });

  function canvasOf(i) { return slides[i].querySelector('.canvas'); }
  function fitInto(box, canvas) {
    canvas.style.transform = 'scale(' + box.clientWidth / 1920 + ')';
  }

  /* ── Navigation shared by both views ─────────────────────────────── */
  var peer = null;               // presenter window (from main) or opener (from presenter)
  function send(i) {
    try { if (peer && !peer.closed) peer.postMessage({ superaskSlides: true, i: i }, '*'); } catch (e) {}
  }
  addEventListener('message', function (e) {
    if (e.data && e.data.superaskSlides) go(e.data.i, true);
  });

  function go(i, remote) {
    i = Math.max(0, Math.min(N - 1, i));
    cur = i;
    if (isPresenter) renderPresenter(); else renderMain();
    if (!remote) send(i);
  }
  function next() { go(cur + 1); }
  function prev() { go(cur - 1); }

  /* ── Main view ───────────────────────────────────────────────────── */
  var deck = document.getElementById('deck');
  var bar = document.querySelector('#progress span');
  var counter = document.getElementById('counter');
  var notesBox = document.getElementById('notes');
  function scaleDeck() {
    var s = Math.min(innerWidth / 1920, innerHeight / 1080);
    deck.style.transform = 'translate(-50%, -50%) scale(' + s + ')';
  }
  function renderMain() {
    slides.forEach(function (s, k) { s.classList.toggle('active', k === cur); });
    bar.style.width = ((cur + 1) / N * 100) + '%';
    counter.textContent = (cur + 1) + ' / ' + N;
    notesBox.innerHTML = '<b>Speaker notes · slide ' + (cur + 1) + '</b>' + (NOTES[cur] ? esc(NOTES[cur]) : '<i>No notes.</i>');
    if (history.replaceState) history.replaceState(null, '', '#' + (cur + 1));
    document.querySelectorAll('.thumb').forEach(function (t, k) { t.classList.toggle('current', k === cur); });
  }
  function esc(s) { return s.replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }

  function toggle(id, force) {
    var el = document.getElementById(id);
    var show = force === undefined ? el.hidden : force;
    el.hidden = !show;
    if (id === 'overview' && show) buildOverview();
    return show;
  }
  var overviewBuilt = false;
  function buildOverview() {
    var grid = document.querySelector('#overview .grid');
    if (!overviewBuilt) {
      slides.forEach(function (s, k) {
        var t = document.createElement('div');
        t.className = 'thumb';
        t.innerHTML = '<span class="num">' + (k + 1) + '</span>';
        t.appendChild(canvasOf(k).cloneNode(true));
        t.addEventListener('click', function () { toggle('overview', false); go(k); });
        grid.appendChild(t);
      });
      overviewBuilt = true;
    }
    requestAnimationFrame(function () {
      document.querySelectorAll('.thumb').forEach(function (t, k) {
        fitInto(t, t.querySelector('.canvas'));
        t.classList.toggle('current', k === cur);
      });
      var c = document.querySelector('.thumb.current'); if (c) c.scrollIntoView({ block: 'center' });
    });
  }

  function fullscreen() {
    if (!document.fullscreenElement) { (document.documentElement.requestFullscreen || function () {}).call(document.documentElement); }
    else if (document.exitFullscreen) document.exitFullscreen();
  }
  function openPresenter() {
    var url = location.href.split('#')[0].split('?')[0] + '?presenter#' + (cur + 1);
    peer = window.open(url, 'superask-presenter', 'width=1280,height=800');
    setTimeout(function () { send(cur); }, 600);
  }

  /* ── Presenter view ──────────────────────────────────────────────── */
  var pNow, pNext, pNotes, pPos, t0 = null, paused = 0, pauseAt = null;
  function renderPresenter() {
    pNow.innerHTML = ''; pNow.appendChild(canvasOf(cur).cloneNode(true));
    pNext.innerHTML = '';
    if (cur + 1 < N) { pNext.classList.remove('end'); pNext.appendChild(canvasOf(cur + 1).cloneNode(true)); }
    else { pNext.classList.add('end'); pNext.textContent = 'End of deck'; }
    pNotes.textContent = NOTES[cur] || 'No notes for this slide.';
    pPos.textContent = 'Slide ' + (cur + 1) + ' of ' + N;
    requestAnimationFrame(function () {
      fitInto(pNow, pNow.querySelector('.canvas'));
      var nc = pNext.querySelector('.canvas'); if (nc) fitInto(pNext, nc);
    });
    if (t0 === null) t0 = Date.now();
  }
  function tick() {
    var el = document.querySelector('#presenter .timer'); if (!el) return;
    var ms = t0 === null ? 0 : ((pauseAt || Date.now()) - t0 - paused);
    var s = Math.floor(ms / 1000);
    el.textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
    document.querySelector('#presenter .clock').textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /* ── Input ───────────────────────────────────────────────────────── */
  var digits = '';
  addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;
    if (/^[0-9]$/.test(k)) { digits += k; return; }
    if (k === 'Enter' && digits) { go(parseInt(digits, 10) - 1); digits = ''; e.preventDefault(); return; }
    digits = '';
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].indexOf(k) >= 0) { next(); e.preventDefault(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].indexOf(k) >= 0) { prev(); e.preventDefault(); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(N - 1);
    else if (isPresenter) return;
    else if (k === 'f' || k === 'F') fullscreen();
    else if (k === 'd' || k === 'D') document.getElementById('dl').click();
    else if (k === 'n' || k === 'N') toggle('notes');
    else if (k === 'g' || k === 'G' || k === 'o' || k === 'O') toggle('overview');
    else if (k === 's' || k === 'S') openPresenter();
    else if (k === 'b' || k === 'B' || k === '.') toggle('blackout');
    else if (k === '?' || k === 'h' || k === 'H') toggle('help');
    else if (k === 'Escape') { ['overview', 'help', 'blackout'].forEach(function (id) { toggle(id, false); }); }
  });

  if (isPresenter) {
    document.getElementById('app').hidden = true;
    var P = document.getElementById('presenter'); P.hidden = false;
    pNow = document.getElementById('p-now'); pNext = document.getElementById('p-next');
    pNotes = document.getElementById('p-notes'); pPos = P.querySelector('.pos');
    peer = window.opener;
    P.querySelector('[data-a=prev]').onclick = prev;
    P.querySelector('[data-a=next]').onclick = next;
    P.querySelector('[data-a=pause]').onclick = function () {
      if (pauseAt) { paused += Date.now() - pauseAt; pauseAt = null; this.textContent = 'Pause'; }
      else { pauseAt = Date.now(); this.textContent = 'Resume'; }
    };
    P.querySelector('[data-a=reset]').onclick = function () { t0 = Date.now(); paused = 0; pauseAt = null; };
    addEventListener('resize', renderPresenter);
    setInterval(tick, 500);
    document.title = 'Presenter · ' + document.title;
  } else {
    scaleDeck();
    addEventListener('resize', function () { scaleDeck(); if (!document.getElementById('overview').hidden) buildOverview(); });
    // Click: left third goes back, the rest goes forward. Links still work.
    document.getElementById('stage').addEventListener('click', function (e) {
      if (e.target.closest('a')) return; // links (and the PDF button) keep working
      (e.clientX < innerWidth * 0.3 ? prev : next)();
    });
    var x0 = null;
    addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 50) (dx < 0 ? next : prev)();
    });
    var idleT;
    function wake() { document.body.classList.remove('idle'); clearTimeout(idleT); idleT = setTimeout(function () { document.body.classList.add('idle'); }, 2500); }
    addEventListener('mousemove', wake); wake();
    setTimeout(function () { document.getElementById('hint').classList.add('gone'); }, 4000);
    document.getElementById('blackout').addEventListener('click', function () { toggle('blackout', false); });
  }

  var start = parseInt((location.hash || '').slice(1), 10);
  go(isNaN(start) ? 0 : start - 1, true);
})();
"""

HELP_ROWS = [
    ("<kbd>→</kbd><kbd>Space</kbd>", "Next slide"),
    ("<kbd>←</kbd><kbd>Backspace</kbd>", "Previous slide"),
    ("<kbd>Home</kbd><kbd>End</kbd>", "First / last slide"),
    ("<kbd>7</kbd><kbd>Enter</kbd>", "Jump to slide 7"),
    ("<kbd>F</kbd>", "Full screen"),
    ("<kbd>S</kbd>", "Presenter view (notes, next slide, timer)"),
    ("<kbd>N</kbd>", "Show / hide speaker notes"),
    ("<kbd>G</kbd>", "Slide overview"),
    ("<kbd>D</kbd>", "Download the slides as PDF"),
    ("<kbd>B</kbd>", "Black screen"),
    ("<kbd>Esc</kbd>", "Close overlays"),
    ("<kbd>Ctrl</kbd><kbd>P</kbd>", "Print / save as PDF, one slide per page"),
]


def main():
    deck = json.load(open(os.path.join(HERE, "deck.json"), encoding="utf-8"))
    order, title = deck["order"], deck.get("title", "Slides")
    fonts = sorted({f["href"] for f in deck.get("faces", {}).values() if "href" in f})

    slides, notes = [], []
    for i, sid in enumerate(order):
        src = open(os.path.join(HERE, f"{sid}.html"), encoding="utf-8").read().strip()
        start, end = src.rfind("<aside>"), src.rfind("</aside>")
        note = ""
        if start != -1 and end > start:
            note = src[start + len("<aside>"):end].strip()
            src = src[:start] + src[end + len("</aside>"):]
        notes.append(html.unescape(note))
        slides.append(f'<div class="slide" data-id="{html.escape(sid)}" aria-label="Slide {i + 1}"><div class="canvas">\n{src}\n</div></div>')

    def js_json(v):
        return json.dumps(v, ensure_ascii=False).replace("</", "<\\/")

    help_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in HELP_ROWS)
    links = "\n".join(f'<link rel="stylesheet" href="{html.escape(h)}">' for h in fonts)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{links}
<style>{CSS}</style>
</head>
<body>
<!-- Generated by docs/demo-1/slides/build.py from deck.json and the slide files. Edit those, then re-run. -->
<div id="app">
  <div id="stage"><div id="deck">
{chr(10).join(slides)}
  </div></div>
  <div id="progress"><span></span></div>
  <div id="counter"></div>
  <a id="dl" href="{PDF_REL}" data-online="{PDF_URL}" download title="Download all slides as PDF (D)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download PDF</a>
  <div id="hint">← → to move · F full screen · S presenter view · ? shortcuts</div>
  <div id="notes" class="overlay" hidden></div>
  <div id="overview" class="overlay" hidden><h2>{html.escape(title)} · {len(order)} slides</h2><div class="grid"></div></div>
  <div id="help" class="overlay" hidden><div class="card"><h2>Keyboard shortcuts</h2><table>{help_rows}</table><p style="margin:14px 0 0;color:#4A5565">Click the right side of a slide to go forward, the left side to go back. Swipe on touch screens.</p></div></div>
  <div id="blackout" class="overlay" hidden></div>
</div>
<div id="presenter" hidden>
  <header><span class="timer">00:00</span><span class="clock"></span><span class="pos"></span><span class="spacer"></span>
    <button data-a="pause">Pause</button><button data-a="reset">Reset timer</button><button data-a="prev">← Prev</button><button data-a="next">Next →</button></header>
  <div class="col"><div class="label">Current slide</div><div class="view" id="p-now"></div></div>
  <div class="col"><div class="label">Next</div><div class="view" id="p-next"></div><div class="label" style="margin-top:16px">Speaker notes</div><div id="p-notes" style="margin-top:0"></div></div>
</div>
<script>
var ICONS = {js_json(ICONS)};
var NOTES = {js_json(notes)};
{JS}
</script>
</body>
</html>
"""
    out = os.path.join(HERE, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {out} — {len(order)} slides")
    if "--pdf" in sys.argv:
        make_pdf(out, len(order))


def find_chrome():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if os.path.exists(mac) else None


def make_pdf(index_html, count):
    """Print index.html with headless Chrome: the print stylesheet lays out
    one 1920×1080 slide per page."""
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome not found — install Google Chrome or Chromium to make the PDF.")
    pdf = os.path.normpath(os.path.join(HERE, PDF_REL))
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", f"--user-data-dir={profile}",
             "--no-pdf-header-footer", "--virtual-time-budget=15000", f"--print-to-pdf={pdf}",
             "file://" + os.path.abspath(index_html)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180,
        )
    print(f"Wrote {pdf} — expected {count} pages")


if __name__ == "__main__":
    main()
