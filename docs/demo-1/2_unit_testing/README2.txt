SuperAsk.AI - Demo 1 unit tests (Team AO3)
==========================================

Where the tests are
-------------------
The unit tests live in the tests/ folder at the root of the repository
(https://github.com/Monunhh/Super-ask). They are not copied here, because the
test runner and the code they test are configured from the repository root.
The folder layout mirrors lib/:

    tests/engine/      guardrails, curated answers, glossary, tiers,
                       verification, freshness, topicality, rationale
    tests/retrieval/   BM25 + rank fusion, query handling
    tests/khmer/       Khmer normalisation and romanisation
    tests/lang/        language detection, shared content words, stemming
    tests/llm/         model gateway, prompts, providers, SEA-LION adapter
    tests/kb/          knowledge-base corpus integrity
    tests/log/         audit log and answer trace
    tests/api/         API route integration tests (33): drive the real
                       /api/ask, /api/feedback and /api/health routes end to end
    tests/crawl/       soft-block detection
    tests/ui/          conversation history

Tests use Vitest. No model is called and no API key is needed.

How to run the unit tests
-------------------------
From the repository root, after "npm install" (see 1_code/README1.txt):

    npm test                  run all unit tests once
    npm run test:coverage     the same, with a coverage report; fails if
                              coverage drops below the thresholds in
                              vitest.config.ts
    npm run test:watch        re-run on every file change
    npm run typecheck         TypeScript type check

Additional quality checks used in CI:

    npm run eval              retrieval recall and refusal precision
    npm run verify-check      claim-verification gate
    npm run curated-check     curated-answer matching
    npm run scope-check       in-scope / out-of-scope routing
    npm run rationale-check   rationale answers
    npm run check             all of the above together

Every push to main runs these automatically in GitHub Actions
(.github/workflows/ci.yml).

Last local run (2026-11-09): 24 test files, 643 tests, all passing:
610 unit tests plus the 33 API route integration tests in tests/api/.
Line coverage: 89.6%.
