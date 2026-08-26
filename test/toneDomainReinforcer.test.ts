import test from "node:test";
import assert from "node:assert/strict";
import { toneDomainReinforcer } from "../src/chaser/toneDomainReinforcer.ts";

test("nudges casual register toward formal", () => {
  const { turn, changed } = toneDomainReinforcer({ text: "Hey, we're gonna ship it." }, { tone: "formal" });
  assert.equal(turn.text, "Hello, we're going to ship it.");
  assert.equal(changed, true);
});

test("nudges formal register toward casual", () => {
  const { turn } = toneDomainReinforcer({ text: "We will utilize the tool; however, results vary." }, { tone: "casual" });
  assert.equal(turn.text, "We will use the tool; but, results vary.");
});

test("leaves text untouched when no tone is set", () => {
  const { turn, changed } = toneDomainReinforcer({ text: "Hey, gonna go." }, {});
  assert.equal(turn.text, "Hey, gonna go.");
  assert.equal(changed, false);
});

test("flags absent domain vocabulary without rewriting the turn", () => {
  const { turn, changed, notes } = toneDomainReinforcer(
    { text: "The contract looks fine." },
    { domain: "legal", vocabulary: ["agreement", "indemnify"] },
  );
  assert.equal(turn.text, "The contract looks fine.");
  assert.equal(changed, false);
  assert.match(notes ?? "", /legal/);
});

test("does not flag when domain vocabulary is present", () => {
  const { notes } = toneDomainReinforcer(
    { text: "Please review the agreement." },
    { domain: "legal", vocabulary: ["agreement", "indemnify"] },
  );
  assert.equal(notes, undefined);
});
