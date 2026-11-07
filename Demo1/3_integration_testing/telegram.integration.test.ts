import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AskResponse } from "@/lib/types";

const appendFile = vi.fn<
  (path: string, data: string, encoding: string) => Promise<void>
>();
const mkdir = vi.fn<(path: string, options?: { recursive?: boolean }) => Promise<void>>();
const telegramFetch = vi.fn(
  async (_input: RequestInfo | URL, _init?: RequestInit) =>
    new Response(JSON.stringify({ ok: true, result: {} }), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
);

function telegramPost(body: unknown) {
  return new Request("http://localhost/api/telegram/webhook", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-telegram-bot-api-secret-token": "integration-test-secret",
    },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("LLM_PROVIDER", "extractive");
  vi.stubEnv("DIAGNOSTICS_ENABLED", "false");
  vi.stubEnv("GENERAL_FALLBACK_ENABLED", "false");
  vi.stubEnv("RETRIEVAL_MIN_SCORE", "0.20");
  vi.stubEnv("ASK_TRACE", "false");
  vi.stubEnv("TELEGRAM_BOT_TOKEN", "test-token");
  vi.stubEnv("TELEGRAM_WEBHOOK_SECRET", "integration-test-secret");
  vi.stubEnv("TELEGRAM_MINI_APP_URL", "https://demo.example/chat");

  appendFile.mockReset().mockResolvedValue(undefined);
  mkdir.mockReset().mockResolvedValue(undefined);
  telegramFetch.mockClear();
  vi.stubGlobal("fetch", telegramFetch);

  const globalWithHistory = globalThis as typeof globalThis & {
    __superaskTgHistory?: Map<number, unknown>;
  };
  globalWithHistory.__superaskTgHistory?.clear();

  // Keep the real audit writer and Telegram client; mock only their external
  // filesystem and network boundaries.
  vi.doMock("node:fs/promises", () => ({
    appendFile,
    mkdir,
  }));
});

afterEach(() => {
  vi.doUnmock("node:fs/promises");
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("Telegram webhook", () => {
  it("generates an answer and sends the formatted citation reply", async () => {
    const { POST } = await import("@/app/api/telegram/webhook/route");
    const response = await POST(
      telegramPost({
        update_id: 1,
        message: {
          message_id: 27,
          text: "how do i renew my driving licence",
          chat: { id: 88001, type: "private" },
          from: { id: 88001, language_code: "en" },
        },
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ ok: true });
    expect(telegramFetch).toHaveBeenCalledTimes(2);

    const [actionCall, messageCall] = telegramFetch.mock.calls;
    expect(actionCall[0]).toBe("https://api.telegram.org/bottest-token/sendChatAction");
    expect(JSON.parse(String(actionCall[1]?.body))).toEqual({
      chat_id: 88001,
      action: "typing",
    });

    expect(messageCall[0]).toBe("https://api.telegram.org/bottest-token/sendMessage");
    const sentMessage = JSON.parse(String(messageCall[1]?.body));
    const storedAudit = JSON.parse(appendFile.mock.calls[0][1]);
    const citationId = storedAudit.citedIds[0] as string;

    expect(appendFile).toHaveBeenCalledTimes(1);
    expect(appendFile.mock.calls[0][0]).toMatch(/audit\.jsonl$/);
    expect(storedAudit).toMatchObject({
      question: "how do i renew my driving licence",
      sessionId: "tg:88001",
      citedIds: [citationId],
    });
    expect(sentMessage.chat_id).toBe(88001);
    expect(sentMessage.reply_to_message_id).toBe(27);
    expect(sentMessage.text).toContain("Official sources:");
    expect(sentMessage.text).toContain("Informational only.");
    expect(sentMessage.text).toContain("https://");
    expect(sentMessage.reply_markup.keyboard[0][0]).toMatchObject({
      text: "Open SuperAsk app",
      web_app: { url: "https://demo.example/chat" },
    });
    expect(sentMessage.reply_markup.keyboard[1][0].text).toBe("Ask by text");
  });

  it("formats a Khmer question and answer for Telegram", async () => {
    const { POST } = await import("@/app/api/telegram/webhook/route");
    const response = await POST(
      telegramPost({
        update_id: 3,
        message: {
          message_id: 28,
          text: "តើការប្តូរ ឬពន្យារបណ្ណបើកបរត្រូវការឯកសារអ្វីខ្លះ?",
          chat: { id: 88002, type: "private" },
          from: { id: 88002, language_code: "km" },
        },
      }),
    );

    expect(response.status).toBe(200);
    expect(telegramFetch).toHaveBeenCalledTimes(2);
    const sentMessage = JSON.parse(String(telegramFetch.mock.calls[1][1]?.body));
    expect(sentMessage.text).toContain("ប្រភពផ្លូវការ:");
    expect(sentMessage.text).toContain("ជាព័ត៌មានតែប៉ុណ្ណោះ");
    expect(sentMessage.reply_to_message_id).toBe(28);
  });

  it("rejects a request with the wrong webhook secret", async () => {
    const { POST } = await import("@/app/api/telegram/webhook/route");
    const request = new Request("http://localhost/api/telegram/webhook", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ update_id: 2 }),
    });
    const response = await POST(request);

    expect(response.status).toBe(401);
    expect(telegramFetch).not.toHaveBeenCalled();
  });

  it("shows a Mini App launch button for the start command", async () => {
    const { POST } = await import("@/app/api/telegram/webhook/route");
    const response = await POST(
      telegramPost({
        update_id: 4,
        message: {
          message_id: 29,
          text: "/start",
          chat: { id: 88003, type: "private" },
        },
      }),
    );

    expect(response.status).toBe(200);
    expect(telegramFetch).toHaveBeenCalledTimes(1);
    const sentMessage = JSON.parse(String(telegramFetch.mock.calls[0][1]?.body));
    expect(sentMessage.text).toContain("SuperAsk");
    expect(sentMessage.reply_markup.keyboard[0][0]).toMatchObject({
      text: "Open SuperAsk app",
      web_app: { url: "https://demo.example/chat" },
    });
    expect(sentMessage.reply_markup.keyboard[1][0].text).toBe("Ask by text");
  });
});