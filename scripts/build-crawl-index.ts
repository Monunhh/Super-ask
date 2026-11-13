/**
 * Crawl database → the search index the answer engine reads.
 *
 *   npx tsx scripts/build-crawl-index.ts        (also runs as `prebuild`)
 *
 * Reads data/crawl/db/<institution>/SRC-*.json (written by build-site-db.ts),
 * cuts every page into passages, and writes one file:
 *
 *   data/crawl/index/crawl-index.json
 *
 * holding the passages, the site they came from, and a prebuilt BM25 inverted
 * index over them. The index is prebuilt because segmenting ~10 million
 * characters of Khmer takes far too long to do on a serverless cold start; at
 * request time lib/retrieval/crawl-index.ts only parses this file.
 *
 * ── WHAT THIS CONTENT IS ───────────────────────────────────────────────────
 * Text fetched from official websites by a crawler. Nobody has reviewed it.
 * The engine consults it only when the approved corpus in data/kb/ has no
 * answer, and every answer served from it is labelled as unreviewed website
 * content with a link to the page (see lib/engine/crawl-answer.ts).
 * ───────────────────────────────────────────────────────────────────────────
 *
 * The output is a build product: gitignored, and regenerated from
 * data/crawl/db/ on every `npm run build`.
 */

import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";
import { crawlTokens } from "../lib/retrieval/crawl-tokens";
import type { CrawlIndexFile } from "../lib/retrieval/crawl-index";

const ROOT = process.cwd();
const DB_DIR = join(ROOT, "data", "crawl", "db");
const OUT_DIR = join(ROOT, "data", "crawl", "index");
const OUT_FILE = join(OUT_DIR, "crawl-index.json");

/** Passage size, in characters. Small enough to quote, large enough to answer. */
const TARGET = 700;
const MAX = 1000;
/** Pages and passages shorter than this say nothing worth retrieving. */
const MIN_PAGE = 200;
const MIN_PASSAGE = 120;
/** A term in more than this share of passages carries no signal; drop it. */
const MAX_DF_SHARE = 0.35;

interface SiteFile {
  institution: { name: string };
  source: {
    id: string;
    organization: string;
    organizationKm?: string;
    abbreviation?: string;
    parentMinistry?: string;
    url: string;
    host: string;
  };
  pages: Array<{
    url: string;
    title: string;
    fetchedAt: string;
    text: string;
  }>;
}

function siteFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...siteFiles(full));
    else if (/^SRC-.*\.json$/.test(entry.name)) out.push(full);
  }
  return out.sort();
}

/** Undo the HTML entities the extractor left in place. */
function clean(text: string): string {
  return text
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#0?39;|&rsquo;|&lsquo;/g, "'")
    .replace(/&[lr]dquo;/g, '"')
    .replace(/&[mn]dash;/g, "-")
    .replace(/&hellip;/g, "...")
    .replace(/&[a-z]{2,8};/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Cut page text into passages at sentence ends.
 *
 * The extracted text has no line breaks, so sentence terminators are the only
 * structure left: the Khmer full stop (។), and Latin . ? ! before a space.
 * A "sentence" with none of those inside MAX characters is cut at a space.
 */
function passages(text: string): string[] {
  const sentences = text.split(/(?<=[។៕?!])\s*|(?<=[a-z0-9)\]]\.)\s+(?=[A-Zក-៿])/);
  const out: string[] = [];
  let current = "";

  const flush = () => {
    const t = current.trim();
    if (t.length >= MIN_PASSAGE) out.push(t);
    else if (t.length > 0 && out.length > 0 && out[out.length - 1].length + t.length <= MAX + MIN_PASSAGE) {
      out[out.length - 1] += ` ${t}`;
    }
    current = "";
  };

  for (let sentence of sentences) {
    sentence = sentence.trim();
    if (!sentence) continue;

    while (sentence.length > MAX) {
      if (current) flush();
      let cut = sentence.lastIndexOf(" ", TARGET);
      if (cut < TARGET / 2) cut = TARGET;
      current = sentence.slice(0, cut);
      flush();
      sentence = sentence.slice(cut).trim();
    }

    if (current.length + sentence.length + 1 > MAX) flush();
    current = current ? `${current} ${sentence}` : sentence;
    if (current.length >= TARGET) flush();
  }
  flush();

  return out;
}

function main() {
  if (!existsSync(DB_DIR)) {
    // Not an error: a checkout without the crawl database still builds, and the
    // engine runs on the approved corpus alone.
    console.log("[crawl-index] data/crawl/db/ not found — skipping.");
    return;
  }

  const started = Date.now();
  const sites: CrawlIndexFile["sites"] = [];
  const chunks: CrawlIndexFile["chunks"] = [];
  const docLen: number[] = [];
  const postings = new Map<string, number[]>();
  let pagesUsed = 0;

  for (const file of siteFiles(DB_DIR)) {
    const site = JSON.parse(readFileSync(file, "utf8")) as SiteFile;
    const s = site.source;
    const siteIdx = sites.length;
    sites.push({
      id: s.id,
      org: s.organization,
      orgKm: s.organizationKm ?? "",
      institution: site.institution.name,
      host: s.host,
    });

    // Indexed with every passage of the site, so a question that names the
    // institution finds its pages even when the passage itself does not.
    const siteTokens = crawlTokens(
      [s.organization, s.organizationKm, s.abbreviation, site.institution.name]
        .filter(Boolean)
        .join(" "),
    );

    // The same news teaser appears on the home page, the news list and the
    // article. Keep the first copy per site.
    const seen = new Set<string>();
    let n = 0;

    for (const page of site.pages) {
      const text = clean(page.text ?? "");
      if (text.length < MIN_PAGE) continue;
      const title = clean(page.title ?? "");
      const titleTokens = crawlTokens(title);
      let used = false;

      for (const passage of passages(text)) {
        const key = createHash("sha1").update(passage).digest("hex");
        if (seen.has(key)) continue;
        seen.add(key);

        const body = crawlTokens(passage);
        if (body.length < 8) continue;

        const docIdx = chunks.length;
        n += 1;
        used = true;
        chunks.push([
          siteIdx,
          `${s.id}-${String(n).padStart(4, "0")}`,
          page.url,
          title,
          page.fetchedAt.slice(0, 10),
          passage,
        ]);

        // Title counts twice: it is the page's own statement of its subject.
        const tf = new Map<string, number>();
        for (const t of body) tf.set(t, (tf.get(t) ?? 0) + 1);
        for (const t of titleTokens) tf.set(t, (tf.get(t) ?? 0) + 2);
        for (const t of siteTokens) tf.set(t, (tf.get(t) ?? 0) + 1);

        docLen.push(body.length + titleTokens.length * 2 + siteTokens.length);
        for (const [t, f] of tf) {
          let list = postings.get(t);
          if (!list) postings.set(t, (list = []));
          list.push(docIdx, f);
        }
      }
      if (used) pagesUsed += 1;
    }
  }

  const maxDf = Math.floor(chunks.length * MAX_DF_SHARE);
  const kept: Record<string, number[]> = {};
  for (const [term, list] of postings) {
    if (list.length / 2 > maxDf) continue;
    kept[term] = list;
  }

  const index: CrawlIndexFile = {
    version: 1,
    builtAt: new Date().toISOString(),
    pages: pagesUsed,
    sites,
    chunks,
    docLen,
    postings: kept,
  };

  mkdirSync(OUT_DIR, { recursive: true });
  const json = JSON.stringify(index);
  writeFileSync(OUT_FILE, json);

  console.log(
    `[crawl-index] ${sites.length} sites, ${pagesUsed} pages, ${chunks.length} passages, ` +
      `${Object.keys(kept).length} terms, ${(Buffer.byteLength(json) / 1e6).toFixed(1)} MB, ` +
      `${((Date.now() - started) / 1000).toFixed(1)} s`,
  );
}

main();
