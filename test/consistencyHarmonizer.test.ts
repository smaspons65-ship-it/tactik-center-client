import test from "node:test";
import assert from "node:assert/strict";
import { consistencyHarmonizer } from "../src/chaser/consistencyHarmonizer.ts";

test("removes space before punctuation and adds space after", () => {
  const { turn, changed } = consistencyHarmonizer({ text: "Hello ,world.Next sentence" });
  assert.equal(turn.text, "Hello, world. Next sentence.");
  assert.equal(changed, true);
});

test("appends terminal punctuation when missing", () => {
  const { turn } = consistencyHarmonizer({ text: "No ending here" });
  assert.equal(turn.text, "No ending here.");
});

test("is a no-op on already-well-formed text", () => {
  const { turn, changed } = consistencyHarmonizer({ text: "Already tidy." });
  assert.equal(turn.text, "Already tidy.");
  assert.equal(changed, false);
});
