import { isHumanPause } from "./gate.ts";
import { contextCleanerLite } from "./contextCleanerLite.ts";
import { toneDomainReinforcer } from "./toneDomainReinforcer.ts";
import { creativityRegulator } from "./creativityRegulator.ts";
import { microDriftDetector } from "./microDriftDetector.ts";
import { consistencyHarmonizer } from "./consistencyHarmonizer.ts";
import type { Avatar, ChaserTrace, PipelineState, Turn } from "./types.ts";

/**
 * TACTIK 6.3 — Chaser Engine.
 *
 * Cognitive micro-stabilization layer that runs exclusively during Human
 * Pause (doc section 3's golden rule). Mirrors the official pseudocode
 * (doc section 6) one micro-process at a time; outside Human Pause it is a
 * no-op passthrough so it never touches the main pipeline.
 */
export function chaser6_3(state: PipelineState, avatar: Avatar, lastTurn: Turn): Turn {
  if (!isHumanPause(state)) {
    return lastTurn;
  }

  const trace: ChaserTrace[] = [];

  const cleaned = contextCleanerLite(lastTurn);
  trace.push({ step: "context_cleaner_lite", changed: cleaned.changed });

  const reinforced = toneDomainReinforcer(cleaned.turn, avatar);
  trace.push({ step: "tone_domain_reinforcer", changed: reinforced.changed, notes: reinforced.notes });

  const regulated = creativityRegulator(reinforced.turn, avatar);
  trace.push({
    step: "creativity_regulator",
    changed: regulated.changed,
    notes: `score=${regulated.reading.score.toFixed(2)} target=${regulated.reading.target.toFixed(2)}`,
  });

  const driftFixed = microDriftDetector(regulated.turn, lastTurn);
  trace.push({
    step: "micro_drift_detector",
    changed: driftFixed.changed,
    notes: `drift=${driftFixed.drift.toFixed(2)}`,
  });

  const harmonized = consistencyHarmonizer(driftFixed.turn);
  trace.push({ step: "consistency_harmonizer", changed: harmonized.changed });

  return {
    ...harmonized.turn,
    metadata: {
      ...harmonized.turn.metadata,
      chaser6_3: { trace },
    },
  };
}
