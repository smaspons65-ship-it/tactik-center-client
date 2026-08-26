---
name: sealed-run
description: Set up and record a doctrine-governed evaluation — seal an objective before work begins, score a run across eight dimensions, and append the result to a tamper-evident ledger. Use when the user wants to run a negotiation simulation, pre-register a prediction or decision, evaluate a model or protocol against frozen cases, set up an A/B test between two conditions, or produce a record an outside reviewer can verify.
---

# Sealed run

Run something in a way a skeptic can check afterwards. Three phases, and the
order is the point: **seal, run, record.** Doing them out of order is the
failure this skill exists to prevent.

Uses `tactik_eval` from this repository. Import it; do not reimplement it. Its
refusals are the enforcement.

## Phase 1 — Seal, before anything happens

Nothing runs until the objective is fixed. If the user wants to start and
"write down the goal after," stop and explain why: a goal stated once the
outcome is known will always have been met, and the run measures nothing.

Collect three things. All are required; the code rejects an objective missing
any of them.

- **Target** — what success actually is, in specific terms.
- **Floor** — the walk-away. Without it, every outcome clears the bar in
  hindsight.
- **Must-not-happen** — at least one. The things that make a nominal win a
  real loss.

```python
from tactik_eval import SealedObjective, Case, CasePack, CorrectBehavior

objective = SealedObjective(
    target="renewal at or above 4.20/unit for 24 months",
    floor="3.90/unit, below which we do not sign",
    must_not_happen=("exclusivity", "volume commitment beyond Q3"),
)
print("seal:", objective.seal)
```

Show the user the seal — the 64-character fingerprint — and tell them to keep
it. It is what proves later that the objective did not move.

**For a case pack** (evaluating a model or protocol rather than a single
negotiation), build several cases and check coverage:

```python
pack = CasePack(pack_id="pack-2026-08", cases=(...))
pack.require_full_decision_range()   # raises unless YES, NO and BOUNDED all appear
print("pack seal:", pack.seal)
```

If that raises, the suite only rewards one disposition. A pack whose every
case should end in NO measures timidity and reports it as rigor. Add the
missing cases rather than removing the check.

Mark each case with the behavior that would be correct:
`CorrectBehavior.YES`, `.NO`, or `.BOUNDED`. **BOUNDED is the important one** —
acting, but inside a stated boundary. Most real correct answers live there,
and a suite without it cannot tell judgment from indecision.

## Phase 2 — Run, with the roles split

Record who could see what. Blindness is attested, never assumed.

```python
from tactik_eval import BlindingAttestation, Breach, RunConditions

blinding = BlindingAttestation(
    objective_holder="...",   # owns the sealed objective, does not watch live
    negotiator="...",         # does the work, does not know the objective
    grader="...",             # scores it, and must not be the subject
    negotiator_saw_objective=False,
    holder_watched_live=False,
)

conditions = RunConditions(
    model="...", tools=(...), retrieval="none", fresh_session=True
)
```

If a wall was crossed, record it as a `Breach` rather than smoothing it over.
The run then reports `NO_SCORE` — not a low score. A contaminated measurement
is not a weak measurement; it is not a measurement. Say that to the user
plainly when it happens; it is a real result, not a failure of the tooling.

**For an A/B comparison**, hold conditions constant and prove it:

```python
diffs = baseline_conditions.differences_from(governed_conditions)
if diffs:
    print("arms differ in:", diffs)   # the comparison is not sound yet
```

Any difference here means an outcome gap cannot be attributed to the thing
under test. Fix the arms or state the limitation.

## Phase 3 — Score and record

Score all eight dimensions. `UNDETERMINED` is correct whenever you lack a
basis — and it requires saying what is unresolved.

```python
from tactik_eval import DimensionScore, Scorecard, UNDETERMINED, Run

card = Scorecard(scores={...})          # raises if any dimension is missing
run = Run(run_id="run-001", case_seal=..., conditions=conditions,
          blinding=blinding, scorecard=card, subject="...")

run.require_independent_grading()        # raises if the subject graded itself
scorecard = run.require_measurement()    # raises if the run was contaminated
```

Then append to the ledger and publish the head:

```python
from tactik_eval import Ledger
import json

ledger = Ledger()
ledger.append("run_scored", {"run_id": run.run_id, "scorecard": scorecard.to_payload()})
json.dump(ledger.to_payload(), open("ledger.json", "w"), indent=2)
print("head:", ledger.head)
```

Give the user the head hash and tell them what it is for: anyone holding it
can later prove the history beneath it never changed.

## Correcting a published figure

Never edit. The ledger has no update and no delete, deliberately.

```python
ledger.withdraw(index, reason="stated in public", withdrawn_by="name")
ledger.append("score", {..., "supersedes": index})   # the corrected figure, as new content
```

The original stays exactly where it was, saying exactly what it said, marked
withdrawn. If the user asks you to quietly recompute instead, explain that a
record whose author can improve it after the fact proves nothing — and that
publishing the retraction is usually worth more than the figure was.

## Handing it to a reviewer

The whole point is that they need nothing from you:

```bash
node verify/verify.mjs ledger.json          # independent implementation
python3 -m tactik_eval.verify ledger.json   # ours
```

Two implementations, written against the prose spec in `docs/HASHING.md`. Tell
the reviewer to run both. If they disagree, that is a finding about us and
should be reported as one.

## What a sealed run does not establish

Predictive validity. Sealing, blinding and hashing show that a result was not
edited and not steered. They say nothing about whether a simulated counterparty
behaves like the real one. Only pre-registered predictions scored against real
events can speak to that, with the failures published beside the hits.

State this when presenting results. It is the doctrine's own stated open
question, and letting a verified record imply more than it shows is exactly
the flattery the doctrine is built against.
