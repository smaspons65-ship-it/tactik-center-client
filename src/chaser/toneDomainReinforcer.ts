import type { Avatar, Turn } from "./types.ts";

export interface ToneDomainResult {
  turn: Turn;
  changed: boolean;
  notes?: string;
}

// Safe, meaning-preserving register swaps only — the reinforcer nudges
// surface register, it never rewrites content.
const REGISTER_SUBSTITUTIONS: Record<string, Array<[RegExp, string]>> = {
  formal: [
    [/\bhey\b/gi, "Hello"],
    [/\bgonna\b/gi, "going to"],
    [/\bwanna\b/gi, "want to"],
    [/\byeah\b/gi, "yes"],
    [/\bkinda\b/gi, "somewhat"],
  ],
  casual: [
    [/\bhowever\b/gi, "but"],
    [/\btherefore\b/gi, "so"],
    [/\butilize\b/gi, "use"],
  ],
};

/**
 * 4.2 Tone & Domain Micro-Reinforcer (TDMR-L)
 * Applies lightweight register substitutions matching avatar.tone, and
 * flags (without rewriting) when the avatar's domain vocabulary is absent
 * from the turn — a signal for downstream stages, not a content change.
 */
export function toneDomainReinforcer(turn: Turn, avatar: Avatar): ToneDomainResult {
  let text = turn.text;
  const original = text;

  const rules = avatar.tone ? REGISTER_SUBSTITUTIONS[avatar.tone.toLowerCase()] : undefined;
  if (rules) {
    for (const [pattern, replacement] of rules) {
      text = text.replace(pattern, replacement);
    }
  }

  let notes: string | undefined;
  if (avatar.domain && avatar.vocabulary?.length) {
    const present = avatar.vocabulary.some((term) =>
      new RegExp(`\\b${escapeRegExp(term)}\\b`, "i").test(text),
    );
    if (!present) {
      notes = `domain vocabulary for "${avatar.domain}" not detected in turn`;
    }
  }

  return { turn: { ...turn, text }, changed: text !== original, notes };
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
