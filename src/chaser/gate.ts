import type { PipelineState } from "./types.ts";

/**
 * Golden rule (doc section 3): the Chaser only runs when the system is in
 * Human Pause — including its visible sub-states Thinking…, Thinking Longer…
 * and Searching….
 */
const HUMAN_PAUSE_STATES: ReadonlySet<string> = new Set([
  "human_pause",
  "thinking",
  "thinking_longer",
  "searching",
]);

export function isHumanPause(state: PipelineState): boolean {
  return HUMAN_PAUSE_STATES.has(state);
}
