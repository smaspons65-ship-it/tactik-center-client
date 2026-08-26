# tactik-center-client

Thin client for TACTIK 6 (Episteme-first intelligence center).

This repo currently ships the **TACTIK 6.3 — Chaser Engine**: a cognitive
micro-stabilization layer that runs exclusively during the pipeline's
Human Pause, plus the thin HTTP client this repo is named for.

## What the Chaser does

> "El Chaser solo se ejecuta si el sistema entra en modo Pausa Humana."

The Chaser is an ultra-light, preventive pass over the *last turn* that
runs only while the system is paused for the user (`human_pause`,
`thinking`, `thinking_longer`, `searching`). It stabilizes tone, trims
noise, and catches small drift *before* generation continues — without
duplicating the heavier work Episteme, Guardian, and Backflow already do.

Pipeline position:

```
User Input → Gating → Human Pause → Chaser 6.3 → Ferrari Generation → Episteme → Guardian → Backflow → User
```

### The five micro-processes

| Stage | Module | Does |
|---|---|---|
| 4.1 | Context Cleaner Lite (`CC-L`) | Strips leaked pause markers ("Thinking…"), collapses whitespace, dedupes repeated sentences |
| 4.2 | Tone & Domain Micro-Reinforcer (`TDMR-L`) | Lightweight register substitutions toward `avatar.tone`; flags (never rewrites) missing domain vocabulary |
| 4.3 | Creativity Temperature Regulator (`CTR-L`) | Estimates a cheap creativity heuristic and dampens runaway punctuation flourish if it overshoots `avatar.creativityTarget` |
| 4.4 | Micro Drift Detector (`MDD-L`) | Compares the regulated turn against the true original; rolls back if cumulative drift is too aggressive for a "lite" pass |
| 4.5 | Consistency Harmonizer (`CH-L`) | Normalizes punctuation spacing and guarantees terminal punctuation |

`src/chaser/chaser.ts` wires these together exactly as the official
pseudocode (doc section 6) does — same gating check, same five named
intermediate values (`cleaned`, `reinforced`, `regulated`, `drift_fixed`,
`harmonized`).

Outside a Human Pause state, `chaser6_3` is a no-op passthrough: it never
touches the main pipeline.

## Layout

```
src/
  chaser/           the five micro-processes + orchestrator (pure functions, no I/O)
  server.ts         POST /chaser_6_3 — dependency-free node:http server
  client.ts         TactikClient — thin HTTP client for the endpoint above
  index.ts          public entry point
test/               node:test coverage for every module + an HTTP integration test
```

## Usage

```ts
import { chaser6_3 } from "./src/chaser/chaser.ts";

const stabilized = chaser6_3(
  "thinking",
  { tone: "formal", creativityTarget: 0.4 },
  { text: "Hey, we're gonna ship it!!! Thinking… almost done." },
);
```

Or over HTTP, via the thin client:

```ts
import { TactikClient } from "./src/client.ts";

const client = new TactikClient({ baseUrl: "http://localhost:4306" });
const stabilized = await client.chaser("thinking", { tone: "formal" }, lastTurn);
```

## Running it

Requires Node 22+ (uses native TypeScript execution — no build step).

```bash
npm install     # only needed for @types/node + typescript (dev-time typechecking)
npm test        # runs every unit + integration test
npm run typecheck
npm start       # serves POST /chaser_6_3 on :4306 (override with PORT)
```

## API

`POST /chaser_6_3`

```jsonc
// request
{ "state": "thinking", "avatar": { "tone": "formal" }, "last_turn": { "text": "…" } }

// response
{ "last_turn": { "text": "…", "metadata": { "chaser6_3": { "trace": [...] } } } }
```

Matches doc section 11: `{state, avatar, last_turn} → cognitive adjustments`.
The `trace` in the response is additive observability (which micro-steps
fired) — it never changes pipeline behavior.
