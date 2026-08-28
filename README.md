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

Three skills ship with this repository, plus a standing floor that needs no
invocation at all.

**`/santiago`** — the reasoning posture, applied while the work happens rather
than audited afterwards. Marks what is evidence versus deduction versus
hypothesis versus unknown, keeps confidence matched to the basis in both
directions, seals the objective before the conversation can rewrite it, and
closes with what the answer does not establish. It scales with stakes on
purpose: a doctrine applied everywhere at full weight gets switched off within a
week, and then it governs nothing.

**`/doctrine-review`** — hand it an analysis, memo, forecast or debrief and it
audits the reasoning against the twelve principles, then scores eight
dimensions. It cannot hand back a single grade, and it cannot leave a dimension
blank, because it routes its scorecard through `tactik_eval` and the code
refuses both.

**`/sealed-run`** — seals an objective before work starts, records who could
see what, scores the run, and appends the result to a tamper-evident ledger a
reviewer can check without you.

**`CLAUDE.md`** carries the cheap half — authority matched to basis, undetermined
stated rather than left blank, no collapsed verdicts — and is always in context
inside this repository without anyone asking for it. Skills load when their
description matches what you are doing; a floor that must hold on every answer
belongs there instead.

To carry the same floor outside this repo:

```bash
bash instalar/instalar.sh              # installs it at user level
bash instalar/instalar.sh --mostrar    # prints it, to paste where there is no filesystem
```

It extracts the floor from `CLAUDE.md` rather than carrying a copy, so the two
cannot drift into two different sets of rules. It never overwrites: an existing
`~/.claude/CLAUDE.md` is backed up and appended to, running it twice replaces its
own marked block, and uninstalling means deleting that block. Plain-Spanish
walkthrough for all three surfaces in `instalar/INSTRUCCIONES.md`.

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

.claude/skills/     santiago, doctrine-review, sealed-run — auto-load here
skills/             the same three skills, as served by the plugin
.claude-plugin/     plugin manifest and marketplace entry
CLAUDE.md           the standing floor, always in context in this repo
instalar/           one-command install of that floor elsewhere (Spanish)
analisis/           the doctrine's own reasoning examined (Spanish)
```

The skills are duplicated on purpose: `.claude/skills/` needs no installation
inside this repo, and `skills/` is what the plugin serves elsewhere. A test
asserts the copies stay byte-identical, so they cannot drift into two
different sets of rules.

## What this does not establish

Predictive validity — which the doctrine names as its own load-bearing
assumption. Sealing, hashing and blinding are credibility infrastructure for a
claim they do not prove. Nothing here should be cited as evidence for it.
