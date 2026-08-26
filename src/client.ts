import type { Avatar, PipelineState, Turn } from "./chaser/types.ts";

export interface TactikClientOptions {
  baseUrl: string;
  fetchImpl?: typeof fetch;
}

/**
 * Thin client for TACTIK 6 (see README) — talks to the Chaser 6.3 endpoint
 * over HTTP so callers never need to know the engine's internals, only the
 * documented request/response contract (doc section 11).
 */
export class TactikClient {
  readonly #baseUrl: string;
  readonly #fetch: typeof fetch;

  constructor(options: TactikClientOptions) {
    this.#baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.#fetch = options.fetchImpl ?? fetch;
  }

  async chaser(state: PipelineState, avatar: Avatar, lastTurn: Turn): Promise<Turn> {
    const res = await this.#fetch(`${this.#baseUrl}/chaser_6_3`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ state, avatar, last_turn: lastTurn }),
    });

    if (!res.ok) {
      throw new Error(`chaser_6_3 request failed: ${res.status} ${await res.text()}`);
    }

    const payload = (await res.json()) as { last_turn: Turn };
    return payload.last_turn;
  }
}
