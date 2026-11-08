SuperAsk.AI - Demo 1 data collection (Team AO3)
===============================================

What data SuperAsk collects
---------------------------
1. A registry of Cambodian government websites (132 entries): ministries,
   provincial administrations and public bodies, each with its source of
   evidence and crawl priority.
2. Monitoring results from crawling those websites: which are reachable,
   and which pages changed since the last run.
3. The knowledge base the assistant answers from (data/kb/*.json, curated
   answers, glossary, aliases). This is written and checked by hand from
   official ministry pages; crawled text is never answerable automatically.

Where the scripts are
---------------------
The scripts live in the repository (https://github.com/Monunhh/Super-ask),
not in this folder, because they read and write the data/ folder at the root:

    data/registry/seed_registry.py     hand-built seed list of government sites,
                                       with provenance for each entry
    data/registry/build_dataset.py     builds the registry CSV deliverables
                                       from the seed list
    data/registry/websites_master.csv  the registry the crawler reads
    scripts/build-sources.ts           registry CSV -> data/sources.json
    scripts/crawl.ts                   crawler: verify and monitor modes
    lib/crawl/                         fetching, robots.txt, extraction,
                                       change classification, storage

See data/README.md for a full description of every data file.

How to run them
---------------
From the repository root, after "npm install" (see 1_code/README1.txt):

    npm run build-sources     regenerate data/sources.json from the registry
    npm run crawl:verify      probe every registered site; writes
                              data/crawl/verification.json
    npm run crawl:monitor     detect changed pages on confirmed sites
    npm run crawl:weekly      monitor priority 1 and 2 sites only

    npx tsx scripts/crawl.ts --mode=monitor --dry-run
                              fetch and compare without saving anything

The crawler respects robots.txt, identifies itself with a user agent, and
waits at least 2 seconds between requests to the same host.

The Python registry builder needs Python 3 and pandas:

    pip install pandas
    cd data/registry
    python build_dataset.py

Note: build_dataset.py currently writes to /mnt/user-data/outputs (the
folder it was first run in). Change the OUT variable at the top of the file
to a local folder before running it.
