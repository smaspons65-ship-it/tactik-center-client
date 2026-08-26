import type { Turn } from "./types.ts";

export interface StepResult {
  turn: Turn;
  changed: boolean;
}

const TERMINAL_PUNCTUATION = /[.!?…"'”’)\]]$/;

/**
 * 4.5 Consistency Harmonizer (CH-L)
 * Final smoothing pass: normalizes punctuation spacing and guarantees the
 * turn ends on terminal punctuation, so downstream stages (Episteme,
 * Guardian, Backflow) always see a well-formed narrative unit.
 */
export function consistencyHarmonizer(turn: Turn): StepResult {
  let text = turn.text;
  const original = text;

  text = text
    .replace(/\s+([,.;:!?])/g, "$1")
    .replace(/([,.;:!?])(?=[^\s"'”’)\]])/g, "$1 ")
    .replace(/[ \t]+/g, " ")
    .trim();

  if (text.length > 0 && !TERMINAL_PUNCTUATION.test(text)) {
    text += ".";
  }

  return { turn: { ...turn, text }, changed: text !== original };
}
