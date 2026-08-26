import test from "node:test";
import assert from "node:assert/strict";
import { microDriftDetector } from "../src/chaser/microDriftDetector.ts";

test("passes through when drift is within the ceiling", () => {
  const original = { text: "The weather today is sunny and warm." };
  const regulated = { text: "The weather today is sunny and warm!" };
  const { turn, changed, drift } = microDriftDetector(regulated, original);
  assert.equal(turn.text, regulated.text);
  assert.equal(changed, false);
  assert.ok(drift < 0.35);
});

test("rolls back to the original when drift exceeds the ceiling", () => {
  const original = { text: "The weather today is sunny and warm." };
  const regulated = { text: "Completely different content about spaceships and dragons." };
  const { turn, changed, drift } = microDriftDetector(regulated, original);
  assert.equal(turn.text, original.text);
  assert.equal(changed, true);
  assert.ok(drift > 0.35);
});
