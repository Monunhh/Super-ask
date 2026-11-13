/**
 * Tokens for the crawl index — the shared segmenter, minus the noise.
 *
 * `segment()` emits every Khmer orthographic cluster on its own as well as in
 * bigrams. Over 45 hand-written chunks that is harmless. Over thousands of
 * crawled passages a single cluster (roughly a syllable) is in nearly every
 * document: it doubles the index and adds no signal. So single clusters are
 * dropped here, and so are bare numbers and the English function words.
 *
 * The same function runs when the index is built and when it is queried —
 * the contract that matters more than what it keeps.
 */

import { segment, clusters } from "@/lib/khmer/segment";
import { STOPWORDS } from "@/lib/lang/content";
import { normaliseWord } from "@/lib/lang/stem";

const KHMER = /[ក-៿]/;
const STOP = new Set([...STOPWORDS].map((w) => normaliseWord(w)));

export function crawlTokens(text: string): string[] {
  return segment(text).filter((t) => {
    if (KHMER.test(t)) return clusters(t).length > 1;
    return t.length > 1 && !/^\d+$/.test(t) && !STOP.has(t);
  });
}
