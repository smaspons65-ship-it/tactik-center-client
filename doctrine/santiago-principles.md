# The Santiago Doctrine — the twelve principles

Santiago Maspons · TACTIK · Doctrine 1.0.0

Reference extract, kept in the repository so the code has something to cite.
The reasoning edition (the full prose, with what each rule defends against) and
the enforced specification are separate documents; this file is neither, and
where they disagree with this summary, they win.

Principles marked **enforced** are gated in `tactik_eval/`. The rest are
judgment rules for the engine and the debrief, not properties this package can
check — listed here so the gap between "stated" and "enforced" stays visible,
which is itself P09.

| # | Principle | In one line | Status |
|---|---|---|---|
| 01 | Read intent first | Numbers are meaningless until you know if a future exists. | engine |
| 02 | Probe, don't binary | Between yes and walking out is where deals are actually won. | enforced — `CorrectBehavior.BOUNDED` |
| 03 | Person + institution | Trust does not travel at face value. | engine |
| 04 | Theater ≠ belief | Never let a performance update your model. | engine |
| 05 | Recurrence = rule | One observation is a story, not a law. | engine |
| 06 | Asymmetric doubt | Destroying a judgment costs more than building one. | engine |
| 07 | Seal the goal first | Otherwise the goal is written by the outcome. | enforced — `SealedObjective` |
| 08 | Blind the roles | A contaminated measurement is not a measurement. | enforced — `BlindingAttestation` |
| 09 | Undetermined, not blank | Silence always flatters the author. | enforced — `Scorecard` |
| 10 | Add, never overwrite | A record you can improve proves nothing. | enforced — `Ledger` |
| 11 | Be dispensable | A hostile reviewer must be able to check us without us. | enforced — `canonical` + `verify/` |
| 12 | Constrain the actors | Miracles make comfortable, useless rehearsals. | engine — `Case.actor_constraints` carries them |

## Two rules from the epistemic governance doctrine

Both are enforced here, and both are the kind that erode quietly:

- **Dimensions do not collapse into one number** before semantics and
  calibration are established. `Scorecard.aggregate()` refuses without a
  `CalibrationAttestation`.
- **A behavioral protocol must not grade itself** as proof of effectiveness.
  Self-evaluation is for debugging. `Run.require_independent_grading()` raises
  when the subject is also the grader.

## What this package does not establish

Predictive validity, which the doctrine names as its own load-bearing
assumption. Sealing, hashing and blinding are credibility infrastructure for a
claim they do not prove: that a reconstructed counterparty behaves closely
enough to the real one to change the real outcome. Only pre-registered
predictions, scored after real events, with the failures published beside the
hits, can settle that.

Nothing in this repository should be cited as evidence for it.
