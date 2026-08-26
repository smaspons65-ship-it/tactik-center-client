import test from "node:test";
import assert from "node:assert/strict";
import { chaser6_3 } from "../src/chaser/chaser.ts";

test("passes the turn through untouched outside Human Pause", () => {
  const lastTurn = { text: "Thinking… hello   world" };
  const result = chaser6_3("responding", {}, lastTurn);
  assert.deepEqual(result, lastTurn);
});

for (const state of ["human_pause", "thinking", "thinking_longer", "searching"]) {
  test(`runs the full pipeline during Human Pause state "${state}"`, () => {
    const result = chaser6_3(state, { tone: "formal" }, { text: "Hey, we're   gonna ship it" });
    assert.equal(result.text, "Hello, we're going to ship it.");
    const trace = (result.metadata?.chaser6_3 as { trace: unknown[] }).trace;
    assert.equal(trace.length, 5);
  });
}

test("rolls back drift while still recording the attempt in the trace", () => {
  const lastTurn = { text: "The weather today is sunny and warm." };
  const result = chaser6_3("human_pause", {}, lastTurn);
  assert.equal(result.text, lastTurn.text);
  const trace = (result.metadata?.chaser6_3 as { trace: Array<{ step: string; changed: boolean }> }).trace;
  const driftStep = trace.find((t) => t.step === "micro_drift_detector");
  assert.equal(driftStep?.changed, false);
});

test("never duplicates Episteme/Guardian/Backflow work — output stays a plain Turn shape", () => {
  const result = chaser6_3("human_pause", {}, { text: "Stable content." });
  assert.deepEqual(Object.keys(result).sort(), ["metadata", "text"]);
});
