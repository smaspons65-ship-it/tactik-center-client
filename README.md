# tactik-center-client

Thin client for TACTIK 6 (Episteme-first intelligence center).

Contains `tactik_eval`: the frozen-evaluation substrate for the Santiago
Doctrine. Stdlib only, no dependencies, Python ≥ 3.10.

## Why this exists before a model does

The doctrine argues against putting itself in the weights:

> A principle applied when convenient is not a principle; it is a preference.
> The engine is the only place where a rule cannot be waived under pressure.

Fine-tuning produces exactly a preference — a strong prior that a sufficiently
persuasive context can override. Deterministic code cannot be talked out of a
gate. So the doctrine lives here, in gates, and a model trained on doctrine
prose would be the failure the doctrine opens by naming: fluency a skeptic
mistakes for judgment.

This package is also the prerequisite for any model work that follows. Frozen
cases are the eval set; graded doctrine-conformant outputs are the training set.
Same artifact, both jobs — and without it there is no way to show a fine-tune
helped, which the evaluation doctrine forbids assuming.

## The gates

Each of these is a rule the doctrine states, enforced in code rather than
documented as an intention. All of them raise; none of them warn.

| Rule | Enforcement |
|---|---|
| P07 — a session cannot start without a sealed objective | `SealedObjective` requires a target, a floor, and at least one must-not-happen clause. No floor means every outcome clears the bar retroactively. |
| P08 — a contaminated run gets no score, not a low one | `Run.result()` returns `NO_SCORE`, which is deliberately not `0`. Zero is a measurement; this is the absence of one. |
| P09 — undetermined is stated, blank is an error | `Scorecard` raises on an omitted dimension. `UNDETERMINED` is a valid band but demands a rationale saying what is unresolved. |
| P10 — correct by addition, never by mutation | `Ledger` exposes no update and no delete. Withdrawn content cannot be re-appended. |
| P11 — a hostile reviewer can check us without us | Two independent implementations of the hash recipe, in Python and JavaScript, both answerable to `docs/HASHING.md`. |
| P02 — the answer is often neither yes nor walk out | `CorrectBehavior.BOUNDED`, and `require_full_decision_range()` rejects a pack that never exercises all three. |
| No premature collapse | `Scorecard.aggregate()` refuses without a `CalibrationAttestation`. |
| No self-grading as validation | `Run.require_independent_grading()` raises when subject and grader match. |

Two design decisions worth knowing:

**Floats are rejected, not serialized.** Two languages do not always agree on
the shortest representation of an IEEE-754 double, and a hash recipe with that
ambiguity fails *open* — hashes agree on almost every input and diverge on rare
ones, which looks like correctness until it matters. Bands are integers, money
is minor units, and anything else is a decimal string parsed after verification.

**An undetermined dimension is excluded from an aggregate, never zeroed.**
Scoring honesty as zero would punish it, and the rule would be abandoned within
a quarter.

## Using it in Claude

Two skills ship with this repository.

**`/doctrine-review`** — hand it an analysis, memo, forecast or debrief and it
audits the reasoning against the twelve principles, then scores eight
dimensions. It cannot hand back a single grade, and it cannot leave a dimension
blank, because it routes its scorecard through `tactik_eval` and the code
refuses both.

**`/sealed-run`** — seals an objective before work starts, records who could
see what, scores the run, and appends the result to a tamper-evident ledger a
reviewer can check without you.

### The zero-install way (this repo only)

Nothing to do. Open Claude Code in this repository and type `/doctrine-review`.
Project skills in `.claude/skills/` load automatically for anyone who clones
it — which is the point: a reviewer gets the same rules you have.

### Everywhere else

To use the skills outside this repo, install the plugin:

```
/plugin marketplace add smaspons65-ship-it/tactik-center-client
/plugin install santiago-doctrine@tactik
```

Then the skills are namespaced: `/santiago-doctrine:doctrine-review`.

To try changes before publishing them, load the plugin from disk instead —
`claude --plugin-dir .` from the repo root, then `/reload-plugins` after edits.

### Watch the gates fire

```bash
python3 examples/demo_gates.py
```

Eight attempts at the convenient thing, and what the engine says back. This is
the demo to run in front of a skeptic.

## Use

```bash
pip install -e .
python3 -m unittest discover -s tests -v

python3 examples/worked_run.py ledger.json
node verify/verify.mjs ledger.json      # independent implementation
python3 -m tactik_eval.verify ledger.json
```

The worked example is deliberately unflattering: three cases, two runs, one of
which is contaminated and scores nothing, and one published aggregate that is
withdrawn rather than quietly recomputed.

## Layout

```
tactik_eval/
  canonical.py   canonical JSON + SHA-256; the freeze primitive
  casepack.py    sealed objectives, frozen cases, decision-range coverage
  rubric.py      the eight dimensions, never-blank and no-collapse gates
  protocol.py    run conditions, blinding attestation, void-on-contamination
  record.py      append-only hash-chained ledger with public withdrawal
  verify.py      python-side verifier CLI
verify/verify.mjs   second implementation, Node, no dependencies
docs/HASHING.md     the recipe both implementations answer to
doctrine/           the source documents the gates cite

.claude/skills/     doctrine-review, sealed-run — auto-load in this repo
skills/             the same two skills, as served by the plugin
.claude-plugin/     plugin manifest and marketplace entry
```

The skills are duplicated on purpose: `.claude/skills/` needs no installation
inside this repo, and `skills/` is what the plugin serves elsewhere. A test
asserts the two copies stay byte-identical, so they cannot drift into two
different sets of rules.

## What this does not establish

Predictive validity — which the doctrine names as its own load-bearing
assumption. Sealing, hashing and blinding are credibility infrastructure for a
claim they do not prove. Nothing here should be cited as evidence for it.
