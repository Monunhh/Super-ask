/**
 * Search over crawled official-website content.
 *
 * This is the SECOND corpus, and it is kept apart from the first on purpose.
 * data/kb/ is the approved corpus and lib/retrieval/index.ts searches it; this
 * module searches the passages scripts/build-crawl-index.ts cut out of the
 * crawl database. The engine only comes here when the approved corpus has no
 * answer (lib/engine/crawl-answer.ts), and what it finds is labelled to the
 * citizen as unreviewed website content.
 *
 * The index is a prebuilt file, loaded lazily on the first question that needs
 * it — so a question the approved corpus answers never pays for it, and a
 * deployment without the file simply runs without this corpus.
 */

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { Chunk } from "@/lib/types";
import { normalizeFold } from "@/lib/khmer/normalize";
import { crawlTokens } from "./crawl-tokens";

/** On-disk shape. Written by scripts/build-crawl-index.ts. */
export interface CrawlIndexFile {
  version: 1;
  builtAt: string;
  pages: number;
  sites: Array<{
    id: string;
    org: string;
    orgKm: string;
    institution: string;
    host: string;
  }>;
  /** [siteIdx, id, url, title, fetchedDate, text] */
  chunks: Array<[number, string, string, string, string, string]>;
  docLen: number[];
  /** term → flat [docIdx, tf, docIdx, tf, …] */
  postings: Record<string, number[]>;
}

/** CRAWL_INDEX_PATH exists for tests, which run against a small fixture. */
function indexPath(): string {
  return (
    process.env.CRAWL_INDEX_PATH ||
    join(process.cwd(), "data", "crawl", "index", "crawl-index.json")
  );
}

const K1 = 1.5;
const B = 0.75;

/** How long a crawled page is treated as current before it is flagged. */
const REVIEW_AFTER_DAYS = 90;

interface Loaded {
  file: CrawlIndexFile;
  avgLen: number;
}

let cache: Loaded | null | undefined;

export function crawlEnabled(): boolean {
  return (process.env.CRAWL_KB_ENABLED ?? "true").toLowerCase() !== "false";
}

function load(): Loaded | null {
  if (cache !== undefined) return cache;
  if (!crawlEnabled() || !existsSync(indexPath())) {
    cache = null;
    return cache;
  }
  try {
    const file = JSON.parse(readFileSync(indexPath(), "utf8")) as CrawlIndexFile;
    const avgLen =
      file.docLen.reduce((a, b) => a + b, 0) / (file.docLen.length || 1);
    cache = { file, avgLen };
  } catch (err) {
    console.error("[crawl-index] could not load", err);
    cache = null;
  }
  return cache;
}

/** For tests: forget the loaded index so the next call re-reads the file. */
export function resetCrawlIndex(): void {
  cache = undefined;
}

/** What /api/health reports, without forcing anything the caller did not ask for. */
export function crawlStats(): {
  enabled: boolean;
  loaded: boolean;
  sites: number;
  pages: number;
  passages: number;
  builtAt: string | null;
} {
  const idx = load();
  return {
    enabled: crawlEnabled(),
    loaded: Boolean(idx),
    sites: idx?.file.sites.length ?? 0,
    pages: idx?.file.pages ?? 0,
    passages: idx?.file.chunks.length ?? 0,
    builtAt: idx?.file.builtAt ?? null,
  };
}

function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return date;
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/**
 * A crawled passage in the shape the rest of the engine already handles.
 *
 * The honesty conventions of data/README.md apply: no instrument or article is
 * invented for a web page, `stewardApproved` is explicitly false, and
 * `verified` is the day the crawler fetched the page — which is all that
 * "verified" can mean for content no person has read.
 */
function toChunk(file: CrawlIndexFile, docIdx: number): Chunk {
  const [siteIdx, id, url, title, fetched, text] = file.chunks[docIdx];
  const site = file.sites[siteIdx];
  return {
    id,
    ministry: site.org,
    ministryKm: site.orgKm,
    doc: title || site.host,
    instrument: "Website page (not reviewed)",
    article: site.host,
    url,
    effective: fetched,
    verified: fetched,
    reviewDue: addDays(fetched, REVIEW_AFTER_DAYS),
    geoScope: "KH",
    sensitivity: "public",
    stewardApproved: false,
    origin: "crawl",
    ingestedAt: fetched,
    ingestedFrom: url,
    text,
    keywords: [],
    questions: [],
  };
}

export interface CrawlHit {
  chunk: Chunk;
  /** Raw BM25 score. Comparable within one query only. */
  score: number;
  /**
   * Share of the question the passage (or its page title) contains, with each
   * content word weighted by how rare it is across the crawl.
   */
  coverage: number;
  /** How many distinct content words that is. */
  covered: number;
  /** Content words found in the page title or the institution's name. */
  inTitle: number;
}

/**
 * BM25 over the crawl passages, then a coverage check on each hit.
 *
 * BM25 alone ranks; it cannot say whether the best passage is any good, and its
 * raw score has no fixed scale to put a floor on. Coverage can: of the content
 * words the citizen used, how many does this passage actually contain?
 *
 * The words are weighted by rarity, and that weighting is the point. Counted
 * equally, "how do I apply for a fishing permit" was 67% covered by a rooftop
 * solar page — "apply" and "permit", everything except what the question was
 * about. "Fishing" is the rare word and so carries most of the weight; a
 * passage without it now covers well under half. A word the crawl has never
 * seen is the rarest of all, so a question about something no site mentions
 * cannot be covered by anything.
 */
export function searchCrawl(query: string, topK = 5): CrawlHit[] {
  const idx = load();
  if (!idx) return [];
  const { file, avgLen } = idx;
  const n = file.chunks.length;

  const terms = [...new Set(crawlTokens(query))];
  if (terms.length === 0) return [];

  const scores = new Map<number, number>();
  for (const term of terms) {
    const list = file.postings[term];
    if (!list) continue;
    const df = list.length / 2;
    const idf = Math.log(1 + (n - df + 0.5) / (df + 0.5));
    for (let i = 0; i < list.length; i += 2) {
      const doc = list[i];
      const f = list[i + 1];
      const norm =
        (f * (K1 + 1)) / (f + K1 * (1 - B + B * (file.docLen[doc] / avgLen)));
      scores.set(doc, (scores.get(doc) ?? 0) + idf * norm);
    }
  }

  const wanted = terms.map((term) => {
    const df = (file.postings[term]?.length ?? 0) / 2;
    return { term, weight: Math.log(1 + (n - df + 0.5) / (df + 0.5)) };
  });
  const totalWeight = wanted.reduce((sum, w) => sum + w.weight, 0);

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    // Look a little past topK: the best-covering passage is often not the
    // top-scoring one, and coverage is what decides whether to answer.
    .slice(0, topK * 4)
    .map(([doc, score]) => {
      const chunk = toChunk(file, doc);
      const site = file.sites[file.chunks[doc][0]];
      const haystack = normalizeFold(
        `${chunk.text} ${chunk.doc} ${site.org} ${site.orgKm} ${site.institution}`,
      );
      const head = normalizeFold(
        `${chunk.doc} ${site.org} ${site.orgKm} ${site.institution}`,
      );
      const hit = wanted.filter((w) => haystack.includes(w.term));
      return {
        chunk,
        score,
        coverage:
          totalWeight === 0
            ? 0
            : hit.reduce((sum, w) => sum + w.weight, 0) / totalWeight,
        covered: hit.length,
        inTitle: wanted.filter((w) => head.includes(w.term)).length,
      };
    })
    .sort((a, b) => b.coverage * b.score - a.coverage * a.score)
    .slice(0, topK);
}
