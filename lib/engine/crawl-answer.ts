/**
 * Answering from crawled website content — the step between "the approved
 * corpus has nothing" and "SuperAsk cannot answer".
 *
 * data/kb/ covers a handful of services. The crawl database covers what 58
 * official websites publish. A citizen asking about tax registration used to be
 * refused while the General Department of Taxation's own FAQ sat on disk. This
 * module is what connects the two.
 *
 * It does NOT promote crawled text to approved content:
 *
 *   - It runs only after the approved corpus failed to answer — below the
 *     retrieval floor, or a top source that is not about the question. An
 *     approved answer is never displaced by a crawled one.
 *   - Every answer carries `unreviewed: true`, the UNREVIEWED_NOTICE in its
 *     text, and citations that link to the page the text was fetched from.
 *   - The §12 guardrails, the off-domain screen and the entity-lookup boundary
 *     have all run before this is reached, and the verification gate and output
 *     moderation run on what it produces.
 *
 * Returns null whenever it has nothing good enough, and the caller carries on
 * to the general fallback and then the refusal exactly as before.
 */

import type { AskResponse, Diagnostics, Lang } from "@/lib/types";
import { UNREVIEWED_NOTICE } from "@/lib/ui/copy";
import { generate } from "@/lib/llm";
import { trace } from "@/lib/log/trace";
import { searchCrawl, type CrawlHit } from "@/lib/retrieval/crawl-index";
import { crawlTokens } from "@/lib/retrieval/crawl-tokens";
import { looksLikeEntityLookup } from "./topicality";
import { rationaleGap } from "./rationale";
import { verify } from "./verify";
import { moderateOutput } from "./guardrails";
import { toCitation } from "./citations";

/**
 * Share of the question — content words weighted by rarity, see
 * searchCrawl() — that a passage must contain.
 *
 * Stricter than the 0.34 the approved corpus uses (lib/engine/topicality.ts):
 * that gate downgrades hand-written content, this one decides whether to show
 * unreviewed text at all.
 *
 * Two floors, because the two scripts tokenise differently. A Latin question
 * is a handful of whole words and a good passage contains nearly all of them.
 * A Khmer question is dozens of overlapping cluster bigrams, some spanning
 * word boundaries that no passage will reproduce, so even the right passage
 * rarely passes 0.75. Both numbers come from reading matches against the
 * 58-site crawl: below them the top passage was about something else
 * (electricity questions landing on telecom pages); above them it was on topic.
 */
const MIN_COVERAGE = Number(process.env.CRAWL_MIN_COVERAGE ?? "0.75");
const MIN_COVERAGE_KM = Number(process.env.CRAWL_MIN_COVERAGE_KM ?? "0.6");

/** How many passages the model is given. */
const MAX_SOURCES = 4;

const LEAD: Record<Lang, (org: string) => string> = {
  en: (org) => `Closest passage found on the website of ${org}:`,
  km: (org) => `អត្ថបទដែលជិតបំផុត រកឃើញនៅលើគេហទំព័ររបស់ ${org}៖`,
};

/**
 * Is this hit about the question?
 *
 * Two content words is the minimum a coverage ratio means anything on: with
 * one, any passage that mentions "passport" in passing scores 100%. A one-word
 * question is accepted only when the page title or the institution's name
 * carries the word — a page ABOUT it, not a page that mentions it.
 */
function relevant(
  hit: CrawlHit,
  wanted: number,
  beat: number,
  floor: number,
): boolean {
  if (wanted === 0) return false;
  if (hit.coverage <= beat) return false;
  if (wanted === 1) return hit.inTitle === 1;
  return hit.coverage >= floor && hit.covered >= 2;
}

export interface CrawlAnswerInput {
  question: string;
  /** The resolved query — follow-ups already rewritten against history. */
  normalisedQuery: string;
  history: Array<{ role: "user" | "assistant"; text: string }>;
  lang: Lang;
  /**
   * Coverage the best APPROVED source already achieves on this question. A
   * crawled passage must cover strictly more of it to be served in its place.
   * Omit (0) when the approved corpus produced nothing usable.
   */
  beat?: number;
  id: string;
  retrievalDiag: Partial<Diagnostics>;
  finish: (res: AskResponse, diag: Diagnostics) => AskResponse;
  baseDiagnostics: (over: Partial<Diagnostics>) => Diagnostics;
}

export async function tryCrawlAnswer(
  input: CrawlAnswerInput,
): Promise<AskResponse | null> {
  const { question, lang } = input;

  // A named-entity record lookup has its own answer (the public registers).
  if (looksLikeEntityLookup(question)) return null;

  const tokens = [...new Set(crawlTokens(input.normalisedQuery))];
  const wanted = tokens.length;
  const khmer = tokens.filter((t) => /[ក-៿]/.test(t)).length;
  const floor = khmer > wanted / 2 ? MIN_COVERAGE_KM : MIN_COVERAGE;
  const hits = searchCrawl(input.normalisedQuery, MAX_SOURCES).filter((h) =>
    relevant(h, wanted, input.beat ?? 0, floor),
  );

  trace("crawl", {
    hits: hits.map((h) => ({
      id: h.chunk.id,
      score: Number(h.score.toFixed(2)),
      coverage: Number(h.coverage.toFixed(2)),
    })),
  });

  if (hits.length === 0) return null;

  // "Why" questions get a reason from the source or nothing — same rule the
  // approved path applies, for the same reason (lib/engine/rationale.ts).
  if (rationaleGap(question, [hits[0].chunk.text])) return null;

  const outcome = await generate({
    question,
    lang,
    history: input.history,
    sources: hits.map((h) => ({
      id: h.chunk.id,
      header: `${h.chunk.ministry} — website page "${h.chunk.doc}" (${h.chunk.url}), fetched ${h.chunk.verified}, NOT reviewed`,
      text: h.chunk.text,
    })),
  });

  if (outcome.shouldDecline || !outcome.answer) return null;

  const cited = hits
    .map((h) => h.chunk)
    .filter((c) => outcome.citations.includes(c.id));
  if (cited.length === 0) return null;

  // The extractive provider's lead says "From the approved source", which is
  // exactly what this is not. Compose the quote here instead.
  const body =
    outcome.provider.id === "extractive"
      ? `${LEAD[lang](lang === "km" && cited[0].ministryKm ? cited[0].ministryKm : cited[0].ministry)}\n\n${cited[0].text}`
      : outcome.answer;

  const verification = verify(
    body,
    outcome.citations,
    cited.map((c) => ({ id: c.id, text: `${c.text}\n${c.ministry}\n${c.ministryKm}` })),
    hits.map((h) => h.chunk.id),
  );
  trace("crawl.verify", {
    passed: verification.passed,
    unsupported: [...verification.unsupported, ...verification.invalidCitations],
  });
  if (!verification.passed) return null;

  if (moderateOutput(body)) return null;

  return input.finish(
    {
      id: input.id,
      tier: 2,
      lang,
      answer: `${body}\n\n${UNREVIEWED_NOTICE[lang]}`,
      citations: cited.map((c) => toCitation(c, lang)),
      // Still a gap in the APPROVED corpus, which is what this flag reports.
      coverageGap: true,
      unreviewed: true,
    },
    input.baseDiagnostics({
      tier: 2,
      ...input.retrievalDiag,
      provider: outcome.provider.id,
      model: outcome.provider.model,
      hosting: outcome.provider.hosting,
      residency: outcome.provider.residency,
      providerFallback: outcome.fallbackReason,
      candidates: hits.map((h) => ({
        id: h.chunk.id,
        lexical: Number(h.score.toFixed(3)),
        dense: 0,
        fused: Number(h.coverage.toFixed(3)),
        rerank: Number(h.coverage.toFixed(3)),
        cited: outcome.citations.includes(h.chunk.id),
      })),
      verification: { passed: true, unsupported: [] },
      // Never better than low: nobody has reviewed the source.
      confidence: "low",
      refusalReason: "fallback:crawled_website",
    }),
  );
}
