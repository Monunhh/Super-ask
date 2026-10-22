"use client";

/**
 * One assistant turn: the answer, its persistent source receipt, the decline
 * notice where no source covered the question, the controls, and the
 * non-binding notice.
 *
 * Ordering here is a requirement, not a layout preference. The answer, then the
 * sources (FR-62), then the decline notice (UC-4), then the notice (FR-65). The
 * notice is last because it applies to everything above it.
 */

import { useState } from "react";
import { AlertTriangle, Flag, ShieldCheck, Terminal } from "lucide-react";
import type { AskResponse } from "@/lib/types";
import { T } from "@/lib/ui/theme";
import { UI, UNVERIFIED_NOTICE } from "@/lib/ui/copy";
import { AnswerText } from "./AnswerText";
import { SourceCard } from "./SourceCard";
import { ReportDialog } from "./ReportDialog";

export function AnswerBlock({
  answer,
  onOpenTrace,
}: {
  answer: AskResponse;
  onOpenTrace: (a: AskResponse) => void;
}) {
  const [reporting, setReporting] = useState(false);
  const lang = answer.lang;
  const hasSources = answer.citations.length > 0;

  /*
    The engine appends UNVERIFIED_NOTICE to the answer string so that consumers
    which render only the text still carry the warning. This interface renders
    it as a banner above the answer instead — earlier in the reading order,
    where a qualification is actually read — so the trailing copy of it comes
    off first. Both strings come from lib/ui/copy.ts, so the match is exact.
  */
  const body =
    answer.unverified && answer.answer.endsWith(UNVERIFIED_NOTICE[lang])
      ? answer.answer.slice(0, -UNVERIFIED_NOTICE[lang].length).trimEnd()
      : answer.answer;

  return (
    <div className="ag-fade mb-10">
      {/*
        Attribution header.

        The answer tier used to be printed here as "SuperAsk · Tier 2". Tier is
        PRD vocabulary (§10.2) describing which internal path produced the
        answer; it means nothing to a citizen and invites them to wonder whether
        a "Tier 3" answer is worse than a "Tier 1" one. It remains in the
        diagnostics payload for operators.
      */}
      <div className="mb-2.5 flex items-center gap-2">
        <div
          className="flex items-center justify-center rounded-md"
          style={{
            width: 21,
            height: 21,
            background: T.deep,
            boxShadow: T.shadowSm,
          }}
          aria-hidden
        >
          <ShieldCheck size={12.5} color="#fff" />
        </div>
        <span
          className="ag-mono"
          style={{
            fontSize: 9.5,
            letterSpacing: "0.09em",
            color: T.inkFaint,
            textTransform: "uppercase",
          }}
        >
          SuperAsk
        </span>
      </div>

      {/*
        FR-62 inverted: where there is no source to attribute, say so before the
        answer rather than attributing nothing and letting it read as official.
      */}
      {answer.unverified && (
        <div
          className="mb-3 rounded-lg px-3 py-2.5"
          style={{
            background: T.noticeWash,
            border: `1px solid ${T.noticeLine}`,
          }}
        >
          <div className="flex items-start gap-2">
            <AlertTriangle
              size={13}
              color={T.noticeText}
              className="mt-0.5 shrink-0"
              aria-hidden
            />
            <div>
              <div
                className="km"
                style={{ fontSize: 12.5, fontWeight: 600, color: T.noticeText }}
              >
                {UI.unverifiedLabel[lang]}
              </div>
              <div
                className="km mt-0.5"
                style={{ fontSize: 12, lineHeight: 1.55, color: T.inkSoft }}
              >
                {UI.unverifiedBody[lang]}
              </div>
            </div>
          </div>
        </div>
      )}

      <AnswerText text={body} />

      {/* FR-62: persistent, not behind a control. */}
      {hasSources && (
        <div className="mt-4">
          <div
            className="ag-mono mb-2"
            style={{
              fontSize: 9.5,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: T.inkFaint,
            }}
          >
            {answer.citations.length === 1
              ? UI.sourceOne[lang]
              : `${UI.sourceMany[lang]} · ${answer.citations.length}`}
          </div>
          <div className="flex flex-col gap-2">
            {answer.citations.map((c) => (
              <SourceCard key={c.id} citation={c} lang={lang} />
            ))}
          </div>
        </div>
      )}

      {/*
        UC-4 — the decline notice. SuperAsk says it has no approved source and
        stops there. There is no handover: the citizen can rephrase, pick a
        suggested question, or confirm with the responsible office themselves.
      */}
      {answer.coverageGap && (
        <div className="mt-3.5">
          <span
            className="km inline-flex items-center gap-1.5"
            style={{ fontSize: 12.5, color: T.inkSoft }}
          >
            <AlertTriangle
              size={13}
              color={T.noticeText}
              className="shrink-0"
              aria-hidden
            />
            {UI.noSourceNotice[lang]}
          </span>
        </div>
      )}

      {/* Controls */}
      <div className="mt-3 flex flex-wrap items-center gap-4">
        {answer.diagnostics && (
          <button
            onClick={() => onOpenTrace(answer)}
            className="ag-mono flex items-center gap-1.5 transition-colors"
            style={{ fontSize: 10, color: T.inkFaint }}
            onMouseEnter={(e) => (e.currentTarget.style.color = T.deep)}
            onMouseLeave={(e) => (e.currentTarget.style.color = T.inkFaint)}
          >
            <Terminal size={10} aria-hidden /> {UI.trace[lang]}
          </button>
        )}

        {/* FR-67 */}
        <button
          onClick={() => setReporting(true)}
          className="ag-mono flex items-center gap-1.5 transition-colors"
          style={{ fontSize: 10, color: T.inkFaint }}
          onMouseEnter={(e) => (e.currentTarget.style.color = T.deep)}
          onMouseLeave={(e) => (e.currentTarget.style.color = T.inkFaint)}
        >
          <Flag size={10} aria-hidden /> {UI.reportError[lang]}
        </button>
        {/* The response time in milliseconds was removed from here. It is
            engineering telemetry, it changes on every answer, and it draws the
            eye away from the sources directly above it. Still in diagnostics. */}
      </div>

      {/* FR-65: with every answer. */}
      <div
        className="km"
        style={{
          fontSize: 10.5,
          color: T.inkFaint,
          marginTop: 10,
          paddingTop: 8,
          borderTop: `1px solid ${T.lineSoft}`,
        }}
      >
        {UI.notBinding[lang]}
      </div>

      {reporting && (
        <ReportDialog
          answerId={answer.id}
          citedIds={answer.citations.map((c) => c.id)}
          ministries={[...new Set(answer.citations.map((c) => c.ministry))]}
          lang={lang}
          onClose={() => setReporting(false)}
        />
      )}
    </div>
  );
}
