import type { Turn } from "./types.ts";

export interface DriftResult {
  turn: Turn;
  changed: boolean;
  drift: number;
}

// Beyond this Jaccard distance, the cumulative edits from CC-L/TDMR-L/CTR-L
// are considered too aggressive for a "lite" preventive pass. Set high
// enough that a couple of legitimate register swaps in a short sentence
// (which swing Jaccard distance a lot on a small token set) don't trip it,
// while genuinely unrelated content still does.
const DRIFT_CEILING = 0.75;

/**
 * 4.4 Micro Drift Detector (MDD-L)
 * Compares the regulated turn against the true original last_turn. If the
 * earlier micro-steps drifted too far from the source, roll back to the
 * original rather than compound the divergence — this stage is a safety
 * net, not a rewriter.
 */
export function microDriftDetector(regulated: Turn, original: Turn): DriftResult {
  const drift = 1 - jaccardSimilarity(tokenize(regulated.text), tokenize(original.text));

  if (drift <= DRIFT_CEILING) {
    return { turn: regulated, changed: false, drift };
  }

  const rolledBack: Turn = { ...original, text: original.text.trim() };
  return { turn: rolledBack, changed: true, drift };
}

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-zà-ÿ0-9']+/g) ?? [];
}

function jaccardSimilarity(a: string[], b: string[]): number {
  if (a.length === 0 && b.length === 0) return 1;

  const setA = new Set(a);
  const setB = new Set(b);

  let intersection = 0;
  for (const token of setA) {
    if (setB.has(token)) intersection++;
  }

  const union = new Set([...setA, ...setB]).size;
  return union === 0 ? 1 : intersection / union;
}
