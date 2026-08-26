import type { Turn } from "./types.ts";

export interface StepResult {
  turn: Turn;
  changed: boolean;
}

const PAUSE_MARKERS = [
  /\bThinking longer(?:\.{1,3}|…)?/gi,
  /\bThinking(?:\.{1,3}|…)?/gi,
  /\bSearching(?:\.{1,3}|…)?/gi,
];

/**
 * 4.1 Context Cleaner Lite (CC-L)
 * Strips Human Pause UX markers that leak into content and collapses
 * whitespace/duplicate-sentence noise. Deliberately shallow — it does not
 * re-parse or re-score the turn, that stays Episteme's job.
 */
export function contextCleanerLite(turn: Turn): StepResult {
  let text = turn.text;
  const original = text;

  for (const marker of PAUSE_MARKERS) {
    text = text.replace(marker, "");
  }

  text = text
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  text = dedupeConsecutiveSentences(text);

  return { turn: { ...turn, text }, changed: text !== original };
}

function dedupeConsecutiveSentences(text: string): string {
  const sentences = text.split(/(?<=[.!?])\s+/);
  const out: string[] = [];
  for (const sentence of sentences) {
    const prev = out[out.length - 1];
    if (!prev || prev.trim().toLowerCase() !== sentence.trim().toLowerCase()) {
      out.push(sentence);
    }
  }
  return out.join(" ");
}
