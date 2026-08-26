import test from "node:test";
import assert from "node:assert/strict";
import { createChaserServer } from "../src/server.ts";
import { TactikClient } from "../src/client.ts";

async function withServer<T>(fn: (baseUrl: string) => Promise<T>): Promise<T> {
  const server = createChaserServer();
  await new Promise<void>((resolve) => server.listen(0, resolve));
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("expected a bound TCP address");
  }
  try {
    return await fn(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}

test("client round-trips a Human Pause turn through the real HTTP server", async () => {
  await withServer(async (baseUrl) => {
    const client = new TactikClient({ baseUrl });
    const result = await client.chaser("thinking", { tone: "formal" }, { text: "Hey, we're   gonna ship it" });
    assert.equal(result.text, "Hello, we're going to ship it.");
  });
});

test("server passes non-pause states straight through", async () => {
  await withServer(async (baseUrl) => {
    const client = new TactikClient({ baseUrl });
    const lastTurn = { text: "Already final." };
    const result = await client.chaser("responding", {}, lastTurn);
    assert.deepEqual(result, lastTurn);
  });
});

test("server rejects malformed requests with 400", async () => {
  await withServer(async (baseUrl) => {
    const res = await fetch(`${baseUrl}/chaser_6_3`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ state: "human_pause" }),
    });
    assert.equal(res.status, 400);
  });
});

test("server 404s on unknown routes", async () => {
  await withServer(async (baseUrl) => {
    const res = await fetch(`${baseUrl}/not_chaser`, { method: "POST" });
    assert.equal(res.status, 404);
  });
});
