import { createServer, type IncomingMessage } from "node:http";
import { chaser6_3 } from "./chaser/chaser.ts";
import type { Avatar, PipelineState, Turn } from "./chaser/types.ts";

/**
 * Realizes doc section 11 — "POST /chaser_6_3 → {state, avatar, last_turn}
 * → retorna ajustes cognitivos." Dependency-free by design: the Chaser is
 * meant to be ultraliviano, so its transport shouldn't need a framework.
 */

interface ChaserRequestBody {
  state: PipelineState;
  avatar: Avatar;
  last_turn: Turn;
}

const MAX_BODY_BYTES = 1_000_000;

export function createChaserServer() {
  return createServer(async (req, res) => {
    if (req.method !== "POST" || req.url !== "/chaser_6_3") {
      res.writeHead(404, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "not_found" }));
      return;
    }

    try {
      const body = await readJsonBody(req);
      if (!isChaserRequestBody(body)) {
        res.writeHead(400, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: "invalid_request" }));
        return;
      }

      const lastTurn = chaser6_3(body.state, body.avatar, body.last_turn);
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ last_turn: lastTurn }));
    } catch (err) {
      res.writeHead(400, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "bad_request", message: (err as Error).message }));
    }
  });
}

function isChaserRequestBody(value: unknown): value is ChaserRequestBody {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.state === "string" &&
    typeof v.avatar === "object" &&
    v.avatar !== null &&
    typeof v.last_turn === "object" &&
    v.last_turn !== null &&
    typeof (v.last_turn as Record<string, unknown>).text === "string"
  );
}

function readJsonBody(req: IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk: Buffer) => {
      raw += chunk;
      if (raw.length > MAX_BODY_BYTES) {
        reject(new Error("payload_too_large"));
        req.destroy();
      }
    });
    req.on("end", () => {
      try {
        resolve(raw.length ? JSON.parse(raw) : {});
      } catch {
        reject(new Error("invalid_json"));
      }
    });
    req.on("error", reject);
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const port = Number(process.env.PORT ?? 4306);
  createChaserServer().listen(port, () => {
    console.log(`TACTIK 6.3 Chaser Engine listening on :${port}`);
  });
}
