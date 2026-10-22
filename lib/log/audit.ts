/**
 * Audit log (FR-55) with PII redaction before storage (FR-56).
 *
 * FR-55 requires enough to reconstruct why any given answer was produced
 * (BR-010): the query, the retrieved source identifiers, the model version, the
 * prompt version, the generated answer, and the verification outcome.
 *
 * FR-56 requires personally identifiable information to be redacted BEFORE
 * storage, not on read. Redaction on read is not redaction — the raw value has
 * already been written to disk and to any backup of it.
 *
 * Storage here is append-only JSONL under var/, which is gitignored. Production
 * writes to domestic managed storage subject to the retention policy (NFR-13)
 * and data residency (NFR-11); this module is the seam where that swap happens.
 */

import { appendFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import type { AskResponse } from "@/lib/types";

const LOG_DIR = join(process.cwd(), "var");
const AUDIT_LOG = join(LOG_DIR, "audit.jsonl");
const FEEDBACK_LOG = join(LOG_DIR, "feedback.jsonl");

/**
 * PII redaction. Ordered most-specific-first so that a phone number inside a
 * longer identifier is not partly masked and left partly readable.
 *
 * This is a defence, not a guarantee. Free-text citizen input can contain PII
 * in forms no pattern anticipates, which is why NFR-13 (retention limits) and
 * NFR-14 (anonymisation before publication) exist alongside it rather than
 * relying on this function alone.
 */
const PII_PATTERNS: Array<[RegExp, string]> = [
  // Email
  [/\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g, "[EMAIL]"],
  // Cambodian national ID: 9 digits, often written with separators.
  [/\b\d{9}\b/g, "[ID]"],
  // Passport-style: 1–2 letters then 6–8 digits.
  [/\b[A-Z]{1,2}\d{6,8}\b/g, "[PASSPORT]"],
  // Phone: +855 or 0 followed by 8–10 digits, with optional separators.
  [/(?:\+855|\b0)[\s-]?\d{1,3}[\s-]?\d{3}[\s-]?\d{3,4}\b/g, "[PHONE]"],
  // Long digit runs that are not fees or day counts.
  [/\b\d{10,}\b/g, "[NUMBER]"],
  // Dates of birth written in full.
  [/\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b/g, "[DATE]"],
];

export function redact(text: string): string {
  let out = text;
  for (const [pattern, replacement] of PII_PATTERNS) {
    out = out.replace(pattern, replacement);
  }
  return out;
}

export interface AuditRecord {
  id: string;
  at: string;
  sessionId?: string;
  /** Redacted before write (FR-56). */
  question: string;
  lang: string;
  tier: number;
  provider: string;
  model: string;
  promptVersion: string;
  retrievedIds: string[];
  citedIds: string[];
  /** Redacted before write. */
  answer: string;
  confidence: string;
  verificationPassed: boolean;
  unsupportedClaims: string[];
  refusalReason?: string;
  /** True when the question was in scope but no approved source covered it. */
  coverageGap: boolean;
  /**
   * The answer came from the model's general knowledge rather than an approved
   * source (GENERAL_FALLBACK_ENABLED). Recorded as its own field because
   * "citedIds is empty" is also true of refusals, and a reviewer asking "what
   * has SuperAsk told citizens without a source behind it" needs to be able to
   * filter on exactly that.
   */
  unverified: boolean;
  latencyMs: number;
}

async function appendLine(path: string, record: unknown): Promise<void> {
  try {
    await mkdir(LOG_DIR, { recursive: true });
    await appendFile(path, `${JSON.stringify(record)}\n`, "utf8");
  } catch (err) {
    // An audit write failure must not fail the citizen's request, but it must
    // not pass silently either — an unlogged answer cannot be reconstructed.
    console.error("[audit] write failed", err);
  }
}

export async function recordAnswer(
  question: string,
  res: AskResponse,
  sessionId?: string,
): Promise<void> {
  const d = res.diagnostics;

  const record: AuditRecord = {
    id: res.id,
    at: new Date().toISOString(),
    sessionId,
    question: redact(question),
    lang: res.lang,
    tier: res.tier,
    provider: d?.provider ?? "unknown",
    model: d?.model ?? "unknown",
    promptVersion: d?.promptVersion ?? "unknown",
    retrievedIds: d?.candidates.map((c) => c.id) ?? [],
    citedIds: res.citations.map((c) => c.id),
    answer: redact(res.answer),
    confidence: d?.confidence ?? "unknown",
    verificationPassed: d?.verification.passed ?? true,
    unsupportedClaims: d?.verification.unsupported ?? [],
    refusalReason: d?.refusalReason,
    coverageGap: res.coverageGap,
    unverified: res.unverified === true,
    latencyMs: d?.latencyMs ?? -1,
  };

  await appendLine(AUDIT_LOG, record);
}

export interface FeedbackRecord {
  at: string;
  answerId: string;
  kind: "incorrect" | "helpful" | "unhelpful";
  /** Redacted before write. */
  comment?: string;
  citedIds: string[];
  /** Ministry that owns the cited content, for steward routing (FR-50). */
  ministries: string[];
}

/**
 * Citizen reports of an incorrect answer (FR-50).
 *
 * The report is routed to the steward of the ministry that owns the cited
 * content, which is why the ministry list is captured here rather than derived
 * later — the content version cited may be superseded by the time a steward
 * opens the queue.
 */
export async function recordFeedback(record: Omit<FeedbackRecord, "at">) {
  await appendLine(FEEDBACK_LOG, {
    ...record,
    comment: record.comment ? redact(record.comment) : undefined,
    at: new Date().toISOString(),
  });
}

