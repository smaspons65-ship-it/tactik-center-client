import test from "node:test";
import assert from "node:assert/strict";
import { contextCleanerLite } from "../src/chaser/contextCleanerLite.ts";

test("strips leaked pause markers", () => {
  const { turn, changed } = contextCleanerLite({ text: "Thinking… the answer is 42." });
  assert.equal(turn.text, "the answer is 42.");
  assert.equal(changed, true);
});

test("collapses excess whitespace", () => {
  const { turn } = contextCleanerLite({ text: "hello   world\n\n\n\nfoo" });
  assert.equal(turn.text, "hello world\n\nfoo");
});

test("dedupes immediately repeated sentences", () => {
  const { turn, changed } = contextCleanerLite({ text: "It works. It works. Great." });
  assert.equal(turn.text, "It works. Great.");
  assert.equal(changed, true);
});

test("is a no-op on already-clean text", () => {
  const { turn, changed } = contextCleanerLite({ text: "All good here." });
  assert.equal(turn.text, "All good here.");
  assert.equal(changed, false);
});
