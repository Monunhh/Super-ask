SuperAsk.AI - Demo 1 integration tests (Team AO3)
==================================================

Purpose
-------
These tests check that the main parts of SuperAsk work together. They cover
the web API, answer engine, sample knowledge base, feedback route, audit writer,
and Telegram webhook and client.

The answer engine, knowledge base, audit writer, and Telegram client are real.
Only file writes and Telegram's HTTP requests are mocked, so the tests do not
write project data or contact Telegram.

How to run
----------
From the repository root, run:

    npm run test:integration

This uses vitest.integration.config.ts in this folder. These suites are not
part of "npm test"; run them with the command above.

What we test
------------
1. Web Q&A and citations: Check that the API and answer engine find an answer
   in the knowledge base, return source details, and create the expected audit
   record.
2. Khmer and English: Send a question in each language and check the response
   language.
3. Unsupported questions: Check that out-of-scope questions are declined and
   that questions without a good source are marked as a coverage gap.
4. Feedback: Ask a question, then report that answer. Check that the feedback
   route and audit writer keep the answer ID, citations, ministry, and redacted
   comment together.
5. Telegram: Check that the webhook uses the answer engine, formats English
   and Khmer replies, and sends them through the Telegram client. Also check
   the webhook secret and the Mini App launch button.

Results
-------
Test files passed: 2
Tests passed: 9
Tests failed: 0

Limitations
-----------
These tests cover backend routes, not the web chat screen in a browser. They
check the Mini App launch button, but do not open Telegram or run the Mini App
in a browser. File writes and Telegram HTTP requests are mocked, so actual
external services and log files are not tested.

Conclusion
----------
All 9 tests passed. The results show that the tested Demo 1 features work
together in the cases covered by these tests.

Other integration tests
-----------------------
The 33 API route integration tests in tests/api/routes.test.ts run with
"npm test" (see 2_unit_testing/README2.txt). Together with the 9 tests here,
SuperAsk has 42 integration tests and 610 unit tests (652 in total).
