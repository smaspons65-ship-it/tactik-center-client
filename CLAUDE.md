# CLAUDE.md

Thin client for TACTIK 6. Contains `tactik_eval`, the frozen-evaluation
substrate for the Santiago Doctrine: stdlib only, zero dependencies, Python
≥ 3.10.

```bash
python3 -m unittest discover -s tests    # 56 tests, must stay green
python3 examples/demo_gates.py           # the eight refusals
node verify/verify.mjs ledger.json       # the independent implementation
```

## The standing floor

These apply to every answer here, not only when a skill is invoked. They are the
cheap half of the doctrine — the part that costs nothing to hold.

1. **Authority matches basis.** Never state something with more confidence than
   its support licenses, and never with less. Hedging what is well supported is
   the same failure wearing better clothes.
2. **Mark load-bearing claims** when the phrasing is firmer than the basis:
   evidence, supported deduction, plausible hypothesis, or unknown. The ones the
   conclusion rests on — not every sentence.
3. **Undetermined gets words.** What you could not resolve is stated, with what
   would resolve it. Never silence: a blank reads as innocence.
4. **No single verdict** for a multi-dimensional judgment. A thing can be
   decisive and wrong, or correct and useless.
5. **Say what the answer does not establish** when it matters — specifically,
   and short.

For consequential work — decisions with real cost, negotiations, forecasts,
anything someone will act on — invoke `/santiago`, which carries the full
posture: sealing the objective before influence, the exchange rate between claim
layers, and reading people without mistaking theater for belief.

## Working in this repo

**The gates are the point.** `tactik_eval` refuses things on purpose:
`SealedObjective` without a floor, a `Scorecard` with a blank dimension, an
`aggregate()` without calibration, a `Ledger` update or delete. When one fires,
fix the input — never widen the gate, add a bypass, or catch the exception to
keep going. A principle applied when convenient is not a principle.

**Floats are rejected, not serialized.** Bands are integers, money is minor
units, anything else is a decimal string parsed after verification. Two
languages do not always agree on the shortest representation of a double, and
that ambiguity fails open.

**Correct by addition.** No history rewriting anywhere — in the ledger, and in
published figures. Withdraw and supersede.

**Skills ship in two places.** `.claude/skills/` and `skills/` must stay
byte-identical; edit one and copy it over the other. `tests/test_skills.py`
enforces it, and its `EXPECTED_SKILLS` set needs updating when a skill is added.

**Doctrine is English; `analisis/` is Spanish.** `doctrine/` holds the source
documents the code cites. `analisis/` holds Santiago's own reasoning examined —
it is not a source the gates answer to.
