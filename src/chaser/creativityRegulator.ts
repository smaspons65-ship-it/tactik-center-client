import type { Avatar, Turn } from "./types.ts";

export interface CreativityReading {
  score: number;
  target: number;
}

export interface CreativityResult {
  turn: Turn;
  changed: boolean;
  reading: CreativityReading;
}

const OVERSHOOT_MARGIN = 0.25;

/**
 * 4.3 Creativity Temperature Regulator (CTR-L)
 * Estimates a cheap creativity heuristic (lexical diversity + punctuation
 * flourish) and, only when it overshoots the avatar's target by a wide
 * margin, dampens runaway punctuation. It never pushes creativity up —
 * that would be generation, not stabilization.
 */
export function creativityRegulator(turn: Turn, avatar: Avatar): CreativityResult {
  const target = clamp(avatar.creativityTarget ?? 0.5, 0, 1);
  let text = turn.text;
  const original = text;

  const score = estimateCreativityTemperature(text);
  if (score > target + OVERSHOOT_MARGIN) {
    text = dampenFlourish(text);
  }

  return { turn: { ...turn, text }, changed: text !== original, reading: { score, target } };
}

function estimateCreativityTemperature(text: string): number {
  const words = text.match(/[A-Za-zÀ-ÿ']+/g) ?? [];
  if (words.length === 0) return 0;

  const unique = new Set(words.map((w) => w.toLowerCase()));
  const lexicalDiversity = unique.size / words.length;

  const exclamations = text.match(/!/g)?.length ?? 0;
  const exclamationDensity = clamp(exclamations / Math.max(1, words.length / 20), 0, 1);

  return clamp(lexicalDiversity * 0.7 + exclamationDensity * 0.3, 0, 1);
}

function dampenFlourish(text: string): string {
  return text.replace(/!{2,}/g, "!").replace(/\?{2,}/g, "?").replace(/\.{4,}/g, "...");
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
