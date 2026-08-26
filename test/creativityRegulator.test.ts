import test from "node:test";
import assert from "node:assert/strict";
import { creativityRegulator } from "../src/chaser/creativityRegulator.ts";

test("dampens runaway punctuation when far above target", () => {
  const { turn, changed, reading } = creativityRegulator(
    { text: "This is amazing!!! Truly wild???" },
    { creativityTarget: 0.1 },
  );
  assert.equal(turn.text, "This is amazing! Truly wild?");
  assert.equal(changed, true);
  assert.ok(reading.score > reading.target);
});

test("leaves text untouched when within target range", () => {
  const { turn, changed } = creativityRegulator({ text: "A calm, measured sentence." }, { creativityTarget: 0.8 });
  assert.equal(turn.text, "A calm, measured sentence.");
  assert.equal(changed, false);
});

test("defaults target to 0.5 when avatar omits it", () => {
  const { reading } = creativityRegulator({ text: "Plain text." }, {});
  assert.equal(reading.target, 0.5);
});
