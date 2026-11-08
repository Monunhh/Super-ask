import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AskResponse } from "@/lib/types";

const appendFile = vi.fn<
  (path: string, data: string, encoding: string) => Promise<void>
>();
const mkdir = vi.fn<(path: string, options?: { recursive?: boolean }) => Promise<void>>();

function post(body: unknown) {
  return new Request("http://localhost/api", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function setEngineEnvironment() {
  vi.stubEnv("LLM_PROVIDER", "extractive");
  vi.stubEnv("DIAGNOSTICS_ENABLED", "false");
  vi.stubEnv("GENERAL_FALLBACK_ENABLED", "false");
  vi.stubEnv("RETRIEVAL_MIN_SCORE", "0.20");
  vi.stubEnv("ASK_TRACE", "false");
}

beforeEach(() => {
  vi.resetModules();
  setEngineEnvironment();
  appendFile.mockReset().mockResolvedValue(undefined);
  mkdir.mockReset().mockResolvedValue(undefined);

  // Use the real audit writer, but stop its filesystem boundary from writing
  // outside this folder.
  vi.doMock("node:fs/promises", () => ({
    appendFile,
    mkdir,
  }));
});

afterEach(() => {
  vi.doUnmock("node:fs/promises");
  vi.unstubAllEnvs();
});

describe("web ask route with the real answer engine", () => {
  it("retrieves a driving-licence answer and returns source citations", async () => {
    const { POST } = await import("@/app/api/ask/route");
    const response = await POST(post({ question: "how do i renew my driving licence" }));
    const body = (await response.json()) as AskResponse;

    expect(response.status).toBe(200);
    expect(body.tier).toBe(2);
    expect(body.lang).toBe("en");
    expect(body.answer.length).toBeGreaterThan(0);
    expect(body.citations.length).toBeGreaterThan(0);
    expect(body.citations[0]).toMatchObject({
      id: expect.stringMatching(/^MPWT-DL-/),
      ministry: expect.stringContaining("Public Works"),
      doc: expect.any(String),
      instrument: expect.any(String),
      article: expect.any(String),
      effective: expect.any(String),
      verified: expect.any(String),
      quote: expect.any(String),
    });
    expect(appendFile).toHaveBeenCalledTimes(1);
    expect(appendFile.mock.calls[0][0]).toMatch(/audit\.jsonl$/);
    expect(JSON.parse(appendFile.mock.calls[0][1])).toMatchObject({
      id: body.id,
      question: "how do i renew my driving licence",
      lang: "en",
      citedIds: body.citations.map((citation) => citation.id),
    });
  });

  it("answers Khmer and English questions in the language typed", async () => {
    const { POST } = await import("@/app/api/ask/route");

    const englishResponse = await POST(
      post({ question: "how do i renew my driving licence" }),
    );
    const english = (await englishResponse.json()) as AskResponse;
    expect(english.lang).toBe("en");
    expect(english.answer).toMatch(/[A-Za-z]/);

    const khmerResponse = await POST(
      post({ question: "ខ្ញុំចង់បន្តប័ណ្ណបើកបរ ត្រូវយកអ្វីខ្លះ" }),
    );
    const khmer = (await khmerResponse.json()) as AskResponse;
    expect(khmer.lang).toBe("km");
    expect(khmer.answer).toMatch(/[\u1780-\u17FF]/);
  });

  it("declines an out-of-scope question without calling it a coverage gap", async () => {
    const { POST } = await import("@/app/api/ask/route");
    const response = await POST(post({ question: "what is the capital of france" }));
    const body = (await response.json()) as AskResponse;

    expect(response.status).toBe(200);
    expect(body.tier).toBe(3);
    expect(body.coverageGap).toBe(false);
    expect(body.citations).toEqual([]);
  });

  it("reports a coverage gap when no source meets the retrieval threshold", async () => {
    vi.stubEnv("RETRIEVAL_MIN_SCORE", "0.99");
    const { POST } = await import("@/app/api/ask/route");
    const response = await POST(
      post({ question: "how do i apply for a fishing permit" }),
    );
    const body = (await response.json()) as AskResponse;

    expect(response.status).toBe(200);
    expect(body.tier).toBe(3);
    expect(body.coverageGap).toBe(true);
    expect(body.citations).toEqual([]);
  });
});

describe("feedback route", () => {
  it("records feedback against an answer returned by the ask route", async () => {
    const { POST: ask } = await import("@/app/api/ask/route");
    const answerResponse = await ask(
      post({ question: "how do i renew my driving licence" }),
    );
    const answer = (await answerResponse.json()) as AskResponse;
    const citation = answer.citations[0];

    expect(answerResponse.status).toBe(200);
    expect(answer.id).toBeTruthy();
    expect(citation).toBeDefined();

    const { POST: feedback } = await import("@/app/api/feedback/route");
    const feedbackResponse = await feedback(
      post({
        answerId: answer.id,
        kind: "incorrect",
        comment: "Please call me at 012 345 678.",
        citedIds: answer.citations.map((source) => source.id),
        ministries: [...new Set(answer.citations.map((source) => source.ministry))],
      }),
    );

    expect(feedbackResponse.status).toBe(200);
    await expect(feedbackResponse.json()).resolves.toEqual({ ok: true });
    expect(appendFile).toHaveBeenCalledTimes(2);

    const auditRecord = JSON.parse(appendFile.mock.calls[0][1]);
    const feedbackRecord = JSON.parse(appendFile.mock.calls[1][1]);
    expect(appendFile.mock.calls[0][0]).toMatch(/audit\.jsonl$/);
    expect(appendFile.mock.calls[1][0]).toMatch(/feedback\.jsonl$/);
    expect(auditRecord.id).toBe(answer.id);
    expect(feedbackRecord).toMatchObject({
      answerId: answer.id,
      kind: "incorrect",
      comment: "Please call me at [PHONE].",
      citedIds: answer.citations.map((source) => source.id),
      ministries: [...new Set(answer.citations.map((source) => source.ministry))],
    });
  });
});
