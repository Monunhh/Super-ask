/**
 * Per-institution crawl database (data/crawl/db/*.json) → one SQLite file.
 *
 *   npx tsx scripts/build-sqlite.ts            (or: npm run build-sqlite)
 *   npx tsx scripts/build-sqlite.ts --search   also build the full-text index
 *   → data/crawl/superask-sites.db
 *
 * The committed copy is built WITHOUT --search. The trigram index is half the
 * file (about 29 MB of 57), every rebuild would add it to git history again,
 * and at this size a plain LIKE scan of every page is already instant:
 *
 *   SELECT s.institution_folder, p.url, p.title
 *   FROM pages p JOIN sites s ON s.id = p.site_id
 *   WHERE p.text LIKE '%ប័ណ្ណបើកបរ%' LIMIT 20;
 *
 * Run scripts/build-site-db.ts first; this reads its output, plus the registry
 * (data/sources.json) and the last reachability check (verification.json), so
 * every registered site is present, crawled or not, with why it was not.
 *
 * Tables
 *   institutions   the 36 bodies of data/registry/institutions.json (in list
 *                  order) plus every other parent body, one row each
 *   sites          all 138 registered websites, their institution, and the
 *                  reachability outcome (live / blocked / dead / empty / …)
 *   pages          every crawled page: url, title, fetch time, extracted text
 *   page_links     links and document links (PDF/Office) found on each page
 *   site_chrome    menu/footer text removed from a site's pages, kept once
 *   pages_fts      full-text index over page title and text (--search only)
 * Views
 *   institution_summary   sites registered / crawled and pages per institution
 *
 * With --search, pages_fts uses the trigram tokenizer: Khmer is written without spaces
 * between words, so a word tokenizer would index whole phrases as one token
 * and a search for a single Khmer word would miss. Trigram matches any
 * substring of 3+ characters, in either script:
 *
 *   SELECT s.institution_folder, p.url, p.title
 *   FROM pages_fts f JOIN pages p ON p.id = f.rowid JOIN sites s ON s.id = p.site_id
 *   WHERE pages_fts MATCH '"ប័ណ្ណបើកបរ"' LIMIT 20;
 *
 * Like data/crawl/db/, this is crawled material that no steward has approved.
 * SuperAsk retrieval does not read it; data/kb/ is the only answer source.
 */

import { DatabaseSync } from "node:sqlite";
import { existsSync, readFileSync, readdirSync, rmSync, statSync } from "node:fs";
import { join } from "node:path";

const ROOT = process.cwd();
const DB_DIR = join(ROOT, "data", "crawl", "db");
const OUT = join(ROOT, "data", "crawl", "superask-sites.db");
const SEARCH = process.argv.includes("--search");

const readJson = <T>(...p: string[]) =>
  JSON.parse(readFileSync(join(ROOT, ...p), "utf8")) as T;

interface IndexInstitution {
  order: number | null;
  institution: string;
  onOfficialList: boolean;
  folder: string;
  registry: Array<{ id: string; organization: string; host: string }>;
  sites: Array<{ id: string; file: string }>;
}

interface SiteFile {
  chrome: string[];
  pages: Array<{
    url: string;
    title: string;
    fetchedAt: string;
    sha256: string;
    rawPath: string;
    textLength: number;
    text: string;
    links: string[];
    documents: string[];
  }>;
}

interface Source {
  id: string;
  org: string;
  orgKm?: string;
  abbr?: string;
  category: string;
  parentMinistry?: string;
  url: string;
  host: string;
  priority: number;
  verified: string;
  enabled: boolean;
  disabledReason?: string;
  notes?: string;
}

interface Verification {
  sourceId: string;
  outcome: string;
  httpStatus?: number;
  homepageTitle?: string;
  checkedAt: string;
  error?: string;
}

function main() {
  const { institutions } = readJson<{ institutions: IndexInstitution[] }>(
    "data", "crawl", "db", "index.json",
  );
  const { sources } = readJson<{ sources: Source[] }>("data", "sources.json");
  const verification = existsSync(join(ROOT, "data", "crawl", "verification.json"))
    ? readJson<Verification[]>("data", "crawl", "verification.json")
    : [];
  const sourceById = new Map(sources.map((s) => [s.id, s]));
  const verifyById = new Map(verification.map((v) => [v.sourceId, v]));

  rmSync(OUT, { force: true });
  const db = new DatabaseSync(OUT);

  db.exec(`
    PRAGMA journal_mode = OFF;
    PRAGMA synchronous = OFF;
    PRAGMA foreign_keys = ON;

    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

    CREATE TABLE institutions (
      id               INTEGER PRIMARY KEY,
      list_order       INTEGER,            -- position on the MFAIC list; NULL if not on it
      name             TEXT NOT NULL UNIQUE,
      on_official_list INTEGER NOT NULL,   -- 1 = one of the 36 listed bodies
      folder           TEXT NOT NULL       -- folder under data/crawl/db/
    );

    CREATE TABLE sites (
      id                 TEXT PRIMARY KEY,  -- SRC-001 …
      institution_id     INTEGER NOT NULL REFERENCES institutions(id),
      institution_folder TEXT NOT NULL,
      organization       TEXT NOT NULL,
      organization_km    TEXT,
      abbreviation       TEXT,
      category           TEXT,
      parent_ministry    TEXT,
      url                TEXT NOT NULL,
      host               TEXT NOT NULL,
      priority           INTEGER,
      provenance         TEXT,              -- how the domain was found
      enabled            INTEGER NOT NULL,
      disabled_reason    TEXT,
      reachability       TEXT,              -- live / blocked / dead / empty / redirect / NULL
      http_status        INTEGER,
      homepage_title     TEXT,
      checked_at         TEXT,
      reachability_error TEXT,
      crawled            INTEGER NOT NULL,  -- 1 if pages are in this database
      page_count         INTEGER NOT NULL DEFAULT 0,
      first_fetched      TEXT,
      last_fetched       TEXT,
      notes              TEXT
    );

    CREATE TABLE pages (
      id          INTEGER PRIMARY KEY,
      site_id     TEXT NOT NULL REFERENCES sites(id),
      url         TEXT NOT NULL UNIQUE,
      title       TEXT,
      fetched_at  TEXT NOT NULL,
      sha256      TEXT NOT NULL,
      text_length INTEGER NOT NULL,
      text        TEXT NOT NULL,
      raw_path    TEXT                       -- retained raw copy (not in git)
    );
    CREATE INDEX pages_site ON pages(site_id);

    CREATE TABLE page_links (
      page_id INTEGER NOT NULL REFERENCES pages(id),
      url     TEXT NOT NULL,
      kind    TEXT NOT NULL CHECK (kind IN ('link', 'document')),
      PRIMARY KEY (page_id, url)
    ) WITHOUT ROWID;

    CREATE TABLE site_chrome (
      site_id TEXT NOT NULL REFERENCES sites(id),
      text    TEXT NOT NULL
    );

    CREATE VIEW institution_summary AS
      SELECT i.list_order, i.name AS institution, i.on_official_list, i.folder,
             COUNT(s.id)                                   AS sites_registered,
             COALESCE(SUM(s.crawled), 0)                   AS sites_crawled,
             COALESCE(SUM(s.page_count), 0)                AS pages,
             COALESCE(SUM(s.reachability = 'blocked'), 0)  AS sites_blocked,
             COALESCE(SUM(s.reachability = 'dead'), 0)     AS sites_dead,
             COALESCE(SUM(s.reachability = 'empty'), 0)    AS sites_empty
      FROM institutions i LEFT JOIN sites s ON s.institution_id = i.id
      GROUP BY i.id
      ORDER BY i.list_order IS NULL, i.list_order, i.name;
  `);

  const insInstitution = db.prepare(
    "INSERT INTO institutions (list_order, name, on_official_list, folder) VALUES (?, ?, ?, ?)",
  );
  const insSite = db.prepare(`
    INSERT INTO sites (id, institution_id, institution_folder, organization, organization_km,
      abbreviation, category, parent_ministry, url, host, priority, provenance, enabled,
      disabled_reason, reachability, http_status, homepage_title, checked_at,
      reachability_error, crawled, page_count, first_fetched, last_fetched, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`);
  const insPage = db.prepare(`
    INSERT INTO pages (site_id, url, title, fetched_at, sha256, text_length, text, raw_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(url) DO NOTHING`);
  const insLink = db.prepare(
    "INSERT OR IGNORE INTO page_links (page_id, url, kind) VALUES (?, ?, ?)",
  );
  const insChrome = db.prepare("INSERT INTO site_chrome (site_id, text) VALUES (?, ?)");

  let pageCount = 0;
  let linkCount = 0;
  db.exec("BEGIN");

  for (const inst of institutions) {
    const { lastInsertRowid: instId } = insInstitution.run(
      inst.order, inst.institution, inst.onOfficialList ? 1 : 0, inst.folder,
    );
    const crawledFile = new Map(inst.sites.map((s) => [s.id, s.file]));

    for (const member of inst.registry) {
      const src = sourceById.get(member.id);
      if (!src) continue;
      const v = verifyById.get(member.id);
      const file = crawledFile.get(member.id);
      const site: SiteFile | null = file
        ? (JSON.parse(readFileSync(join(DB_DIR, file), "utf8")) as SiteFile)
        : null;
      const fetched = site?.pages.map((p) => p.fetchedAt).sort() ?? [];

      insSite.run(
        src.id, instId, inst.folder, src.org, src.orgKm ?? null, src.abbr ?? null,
        src.category, src.parentMinistry ?? null, src.url, src.host, src.priority,
        src.verified, src.enabled ? 1 : 0, src.disabledReason ?? null,
        v?.outcome ?? null, v?.httpStatus ?? null, v?.homepageTitle || null,
        v?.checkedAt ?? null, v?.error ?? null, site ? 1 : 0, site?.pages.length ?? 0,
        fetched[0] ?? null, fetched[fetched.length - 1] ?? null, src.notes ?? null,
      );

      if (!site) continue;
      for (const c of site.chrome) insChrome.run(src.id, c);
      for (const p of site.pages) {
        const r = insPage.run(
          src.id, p.url, p.title, p.fetchedAt, p.sha256, p.textLength, p.text, p.rawPath,
        );
        if (r.changes === 0) continue;
        pageCount += 1;
        const pageId = r.lastInsertRowid;
        for (const l of p.links) linkCount += Number(insLink.run(pageId, l, "link").changes);
        for (const d of p.documents) linkCount += Number(insLink.run(pageId, d, "document").changes);
      }
    }
  }

  if (SEARCH) {
    db.exec(`
      CREATE INDEX page_links_kind ON page_links(kind, url);
      CREATE VIRTUAL TABLE pages_fts USING fts5(
        title, text, content = 'pages', content_rowid = 'id', tokenize = 'trigram'
      );
      INSERT INTO pages_fts (pages_fts) VALUES ('rebuild');
    `);
  }
  const meta = db.prepare("INSERT INTO meta (key, value) VALUES (?, ?)");
  meta.run("builtAt", new Date().toISOString());
  meta.run("source", "data/crawl/db/ (scripts/build-site-db.ts) + data/sources.json + data/crawl/verification.json");
  meta.run("institutionList", "data/registry/institutions.json (MFAIC list of ministries and institutions)");
  meta.run("fullTextIndex", SEARCH ? "yes" : "no (rebuild with --search, or use LIKE)");
  meta.run("status", "Crawled material, not steward-approved. Not read by SuperAsk retrieval.");
  db.exec("COMMIT");
  db.exec("VACUUM");

  const counts = db
    .prepare(
      "SELECT (SELECT COUNT(*) FROM institutions) i, (SELECT COUNT(*) FROM sites) s, (SELECT SUM(crawled) FROM sites) c",
    )
    .get() as { i: number; s: number; c: number };
  db.close();

  const mb = (statSync(OUT).size / 1024 / 1024).toFixed(1);
  console.log(`data/crawl/superask-sites.db — ${mb} MB`);
  console.log(`  institutions ${counts.i}`);
  console.log(`  sites        ${counts.s} (${counts.c} crawled)`);
  console.log(`  pages        ${pageCount}`);
  console.log(`  links        ${linkCount}`);
}

if (!existsSync(join(DB_DIR, "index.json")) || readdirSync(DB_DIR).length < 2) {
  console.error("data/crawl/db/ is empty. Run: npx tsx scripts/build-site-db.ts");
  process.exit(1);
}
main();
