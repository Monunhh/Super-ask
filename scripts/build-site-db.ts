/**
 * Crawled pages → one JSON database file per website.
 *
 *   npx tsx scripts/build-site-db.ts                 every source with crawled pages
 *   npx tsx scripts/build-site-db.ts --only=SRC-034  one source
 *
 * Reads the raw copies the monitor retained under data/crawl/raw/<SRC-ID>/
 * (each carries a provenance header with its URL and fetch time), keeps the
 * newest copy of every URL, extracts title, text and links, and writes
 *
 *   data/crawl/db/<institution>/<SRC-ID>-<host>.json   one per website
 *   data/crawl/db/index.json   every institution, its sites and page counts
 *
 * Sorted by Cambodian ministry or institution, using the official list in
 * data/registry/institutions.json (the 36 bodies of the MFAIC list, in its
 * order). Folders are numbered by that order, e.g. 13-ministry-of-commerce/.
 * A site is filed by, in turn:
 *   1. a pin in institutions.json `sources` (e.g. the e-Tax portal → Taxation),
 *   2. its own name, when it is one of the listed bodies (so the General
 *      Department of Taxation is filed under Taxation, not under MEF),
 *   3. provincial and capital administrations (formally under Interior) go
 *      together in other/provincial-and-capital-administrations/, so 25 sites
 *      do not swamp the ministry's own folder,
 *   4. its parentMinistry,
 *   5. otherwise its own name, under other/.
 *
 * ── THIS IS NOT THE KNOWLEDGE BASE ─────────────────────────────────────────
 * Output goes under data/crawl/, which retrieval never reads (data/README.md).
 * These files are a structured record of what each site published, for search,
 * analysis and later ingestion. Nothing here can reach a citizen answer until
 * it is turned into steward-reviewed chunks in data/kb/.
 * ───────────────────────────────────────────────────────────────────────────
 *
 * Boilerplate: a line that appears on at least 3 pages and on 40% or more of a
 * site's pages is treated as navigation/footer and stored once per site under
 * `chrome`, not repeated in every page's `text`.
 */

import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { join } from "node:path";
import { extract } from "../lib/crawl/extract";

const ROOT = process.cwd();
const RAW_DIR = join(ROOT, "data", "crawl", "raw");
const DB_DIR = join(ROOT, "data", "crawl", "db");
const SOURCES = join(ROOT, "data", "sources.json");
const VERIFICATION = join(ROOT, "data", "crawl", "verification.json");

const HEADER = /^<!-- SuperAsk monitor[^>]*?url=(\S+)[^>]*?fetched=(\S+)[^>]*?sha256=([0-9a-f]+)[^>]*-->\n/;

interface Source {
  id: string;
  registryId: number;
  org: string;
  orgKm?: string;
  abbr?: string;
  category: string;
  parentMinistry?: string;
  url: string;
  host: string;
  priority: number;
  verified: string;
  notes?: string;
}

interface Page {
  url: string;
  title: string;
  fetchedAt: string;
  sha256: string;
  rawPath: string;
  textLength: number;
  text: string;
  links: string[];
  documents: string[];
}

interface Institution {
  order: number;
  short: string;
  name: string;
  matches: string[];
  sources?: string[];
}

const INSTITUTIONS = (
  JSON.parse(
    readFileSync(join(ROOT, "data", "registry", "institutions.json"), "utf8"),
  ) as { institutions: Institution[] }
).institutions;

const SUBNATIONAL = new Set(["Provincial Administration", "Municipal Administration"]);
const norm = (n: string) => n.toLowerCase().replace(/&/g, "and").replace(/\s+/g, " ").trim();

function listed(name: string | undefined): Institution | undefined {
  if (!name) return undefined;
  const n = norm(name);
  return INSTITUTIONS.find(
    (i) => norm(i.name) === n || i.matches.some((m) => norm(m) === n),
  );
}

function slug(name: string): string {
  return norm(name)
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80);
}

interface Placement {
  institution: string;
  official: boolean;
  order: number | null;
  folder: string;
}

function place(name: string, inst?: Institution): Placement {
  return inst
    ? {
        institution: inst.name,
        official: true,
        order: inst.order,
        folder: `${String(inst.order).padStart(2, "0")}-${slug(inst.name)}`,
      }
    : { institution: name, official: false, order: null, folder: join("other", slug(name)) };
}

export function institutionOf(s: Source): Placement {
  const pinned = INSTITUTIONS.find((i) => i.sources?.includes(s.id));
  if (pinned) return place(pinned.name, pinned);
  const self = listed(s.org);
  if (self) return place(self.name, self);
  if (SUBNATIONAL.has(s.category)) return place("Provincial and Capital Administrations");
  const parent = listed(s.parentMinistry);
  if (parent) return place(parent.name, parent);
  return place(s.parentMinistry || s.org);
}

function arg(name: string): string | undefined {
  const hit = process.argv.find((a) => a.startsWith(`--${name}=`));
  return hit?.split("=").slice(1).join("=");
}

function readPages(sourceId: string): Page[] {
  const dir = join(RAW_DIR, sourceId);
  if (!existsSync(dir)) return [];

  const newest = new Map<string, Page>();
  for (const file of readdirSync(dir).filter((f) => f.endsWith(".html"))) {
    const raw = readFileSync(join(dir, file), "utf8");
    const m = HEADER.exec(raw);
    if (!m) continue;
    const [header, url, fetchedAt, sha256] = m;

    const prior = newest.get(url);
    if (prior && prior.fetchedAt >= fetchedAt) continue;

    const { title, text, links } = extract(raw.slice(header.length), url);
    newest.set(url, {
      url,
      title,
      fetchedAt,
      sha256,
      rawPath: join("data", "crawl", "raw", sourceId, file),
      textLength: text.length,
      text,
      links: links.filter((l) => !/\.(pdf|docx?|xlsx?|pptx?)$/i.test(l)),
      documents: links.filter((l) => /\.(pdf|docx?|xlsx?|pptx?)$/i.test(l)),
    });
  }
  return [...newest.values()].sort((a, b) => a.url.localeCompare(b.url));
}

/**
 * Word runs repeated across most of a site's pages: menus, footers, banners.
 *
 * Many of these CMSs emit the whole page as one line, so a line-level
 * comparison finds nothing. Instead every run of SHINGLE consecutive words is
 * counted across pages; a word covered by any run that appears on at least 3
 * pages and 40% of the site is chrome. The removed runs are kept once per site
 * so nothing is lost.
 */
const SHINGLE = 6;

function stripChrome(pages: Page[]): string[] {
  if (pages.length < 3) return [];
  const threshold = Math.max(3, Math.ceil(pages.length * 0.4));

  const tokenised = pages.map((p) =>
    p.text.split("\n").map((line) => line.split(/ +/).filter(Boolean)),
  );
  const key = (words: string[], i: number) => words.slice(i, i + SHINGLE).join(" ");

  const seen = new Map<string, number>();
  for (const lines of tokenised) {
    const onPage = new Set<string>();
    for (const words of lines) {
      for (let i = 0; i + SHINGLE <= words.length; i += 1) onPage.add(key(words, i));
    }
    for (const k of onPage) seen.set(k, (seen.get(k) ?? 0) + 1);
  }

  const chromeRuns = new Set<string>();
  tokenised.forEach((lines, n) => {
    const kept: string[] = [];
    for (const words of lines) {
      const drop = new Array<boolean>(words.length).fill(false);
      for (let i = 0; i + SHINGLE <= words.length; i += 1) {
        if ((seen.get(key(words, i)) ?? 0) >= threshold) {
          for (let j = i; j < i + SHINGLE; j += 1) drop[j] = true;
        }
      }
      let run: string[] = [];
      const out: string[] = [];
      words.forEach((w, i) => {
        if (drop[i]) run.push(w);
        else {
          if (run.length) chromeRuns.add(run.join(" "));
          run = [];
          out.push(w);
        }
      });
      if (run.length) chromeRuns.add(run.join(" "));
      if (out.length) kept.push(out.join(" "));
    }
    pages[n].text = kept.join("\n");
    pages[n].textLength = pages[n].text.length;
  });

  // Keep the distinct runs, longest first, without ones contained in another.
  const runs = [...chromeRuns].sort((a, b) => b.length - a.length);
  return runs.filter((r, i) => !runs.slice(0, i).some((longer) => longer.includes(r)));
}

function main() {
  const { sources } = JSON.parse(readFileSync(SOURCES, "utf8")) as {
    sources: Source[];
  };
  const verification = existsSync(VERIFICATION)
    ? (JSON.parse(readFileSync(VERIFICATION, "utf8")) as Array<{
        sourceId: string;
        outcome: string;
        httpStatus?: number;
        homepageTitle?: string;
        checkedAt: string;
      }>)
    : [];
  const verifyById = new Map(verification.map((v) => [v.sourceId, v]));

  const only = arg("only")?.split(",");
  // A full rebuild owns the whole directory, so a site that moved institution
  // or stopped being crawled does not leave a stale file behind.
  if (!only) rmSync(DB_DIR, { recursive: true, force: true });
  mkdirSync(DB_DIR, { recursive: true });

  const index: Array<Record<string, unknown>> = [];
  for (const s of sources) {
    if (only && !only.includes(s.id)) continue;
    const pages = readPages(s.id);
    if (pages.length === 0) continue;

    const chrome = stripChrome(pages);
    const v = verifyById.get(s.id);
    const { institution, official, order, folder } = institutionOf(s);
    mkdirSync(join(DB_DIR, folder), { recursive: true });
    const file = join(folder, `${s.id}-${s.host.replace(/[^a-z0-9.-]/gi, "_")}.json`);
    const fetched = pages.map((p) => p.fetchedAt).sort();

    const record = {
      _note:
        "Crawled material, not steward-approved. Not read by SuperAsk retrieval (see data/README.md).",
      institution: { name: institution, onOfficialList: official, order },
      source: {
        id: s.id,
        registryId: s.registryId,
        organization: s.org,
        organizationKm: s.orgKm ?? null,
        abbreviation: s.abbr ?? null,
        category: s.category,
        parentMinistry: s.parentMinistry ?? null,
        url: s.url,
        host: s.host,
        priority: s.priority,
        provenance: s.verified,
        notes: s.notes ?? null,
      },
      reachability: v
        ? {
            outcome: v.outcome,
            httpStatus: v.httpStatus ?? null,
            homepageTitle: v.homepageTitle ?? null,
            checkedAt: v.checkedAt,
          }
        : null,
      crawl: {
        pageCount: pages.length,
        documentLinks: [...new Set(pages.flatMap((p) => p.documents))].length,
        firstFetched: fetched[0],
        lastFetched: fetched[fetched.length - 1],
        builtAt: new Date().toISOString(),
      },
      chrome,
      pages,
    };

    writeFileSync(join(DB_DIR, file), JSON.stringify(record, null, 2) + "\n", "utf8");
    index.push({
      institution,
      folder,
      id: s.id,
      organization: s.org,
      host: s.host,
      file,
      pages: pages.length,
      documentLinks: record.crawl.documentLinks,
      lastFetched: record.crawl.lastFetched,
    });
    console.log(`${String(pages.length).padStart(4)} pages  ${file}`);
  }

  if (!only) {
    // Every listed institution appears, and every registry site, crawled or
    // not, so the index also shows where coverage is missing (EDC has no
    // registered site at all).
    type Group = Placement & { members: Array<{ id: string; organization: string; host: string }>; sites: typeof index };
    const groups = new Map<string, Group>();
    const group = (p: Placement) => {
      const g = groups.get(p.institution) ?? { ...p, members: [], sites: [] };
      groups.set(p.institution, g);
      return g;
    };
    for (const i of INSTITUTIONS) group(place(i.name, i));
    for (const s of sources) group(institutionOf(s)).members.push({ id: s.id, organization: s.org, host: s.host });
    for (const row of index) groups.get(row.institution as string)!.sites.push(row);

    const institutions = [...groups.values()]
      .map((g) => ({
        order: g.order,
        institution: g.institution,
        onOfficialList: g.official,
        folder: g.folder,
        registeredSites: g.members.length,
        crawledSites: g.sites.length,
        pages: g.sites.reduce((n, r) => n + (r.pages as number), 0),
        sites: g.sites,
        registry: g.members,
      }))
      .sort((a, b) =>
        a.order !== null && b.order !== null
          ? a.order - b.order
          : a.order !== null
            ? -1
            : b.order !== null
              ? 1
              : a.institution.localeCompare(b.institution),
      );

    writeFileSync(
      join(DB_DIR, "index.json"),
      JSON.stringify({ builtAt: new Date().toISOString(), institutions }, null, 2) + "\n",
      "utf8",
    );
    console.log(`\n${index.length} site files across ${institutions.filter((i) => i.crawledSites).length} of ${institutions.length} institutions in data/crawl/db/`);
  }
}

main();
