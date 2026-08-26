---
name: doctrine-review
description: Audit an analysis, decision memo, forecast, negotiation debrief, or recommendation against the Santiago Doctrine — checking for unsealed objectives, silent uncertainty, one-observation-as-rule, theater read as belief, and collapsed scores. Use when the user asks to review, audit, stress-test, sanity-check or pressure-test a piece of reasoning, or asks whether an analysis is trustworthy or ready to act on. Also use before delivering high-stakes analysis of your own.
---

# Doctrine review

Audit a piece of reasoning against the Santiago Doctrine. The output is a
scorecard across eight dimensions plus named findings — never a single
verdict, and never a blank.

The doctrine's own reason for existing: *a principle applied when convenient
is not a principle; it is a preference.* So this skill does not ask you to
remember the rules. It routes your scorecard through `tactik_eval`, which
refuses malformed ones. If you skip a dimension or reach for one headline
number, the code raises and you fix it before answering.

## Source of truth

`doctrine/santiago-principles.md` and `doctrine/epistemic-governance.md` in
this repository. Read them if the audit turns on a principle's exact wording.

## Procedure

### 1. Find the objective, and when it was fixed

The first question is not whether the analysis is right. It is whether the
goal was stated before the outcome was known (P07).

Look for: a target, a floor or walk-away, and things that must not happen. If
the document states its goal only in the conclusion, or the goal has visibly
been shaped to fit what was found, that is the finding — write it plainly.
A goal stated after the outcome will always have been met, and this is the
most common defect in confident work.

Watch specifically for the **consolation prize**: real movement that is not
movement toward what was actually wanted. It reports like progress.

### 2. Separate what is supported from what is inferred, unknown, or missing

Four buckets, not two. The fourth — *missing* — is the one people skip: what
should be in the evidence and is not there at all. Negative space is evidence.

For each load-bearing claim, ask whether it is quotable and falsifiable. A
claim that cannot be checked cannot carry weight, regardless of how reasonable
it sounds.

### 3. Test the deductions

Inference is allowed; disguised invention is not. For each inference, ask
whether it actually follows from the cited evidence, or whether it merely sits
near it. As stakes, irreversibility and source weakness rise, the acceptable
inference window narrows.

### 4. Run the twelve principles as checks

Work them in order and record what you find. Most documents fail three or four.

1. **Read intent first** — does it establish whether a future exists in the
   relationship before it reasons about terms? Margin given to someone with no
   future is a donation, not a concession.
2. **Probe, don't binary** — does it present accept-or-walk-away as the only
   options? Name the third posture if it was available and unused: hold, buy
   time on a legitimate pretext, manufacture a second meeting. This is the
   most commonly missing move, and naming it is the coaching that makes a
   review worth more than a scoreboard.
3. **Person + institution** — is a read anchored to an individual without the
   institution modulating them? Trust does not transfer at face value.
4. **Theater ≠ belief** — did a performance (warmth, worry, studied
   indifference, delay dressed as process) update the model of the other
   side's true position? A warm meeting that produced nothing is not progress.
5. **Recurrence = rule** — is a single observation carrying the weight of a
   law? A pattern needs recurrence across different subjects and situations.
6. **Asymmetric doubt** — did one soft remark collapse a conclusion built from
   many independent signals? Weakening a well-supported read should cost more
   evidence than building it did.
7. **Seal the goal first** — from step 1.
8. **Blind the roles** — if this reports a measurement, could the measurer
   have steered the outcome? A contaminated measurement is not a weak
   measurement; it is not a measurement.
9. **Undetermined, not blank** — is anything unresolved passed over in
   silence? Silence flatters the author. Every gap gets words.
10. **Add, never overwrite** — was a previous figure quietly revised rather
    than withdrawn and superseded?
11. **Be dispensable** — could a hostile reader check the central claim
    without trusting the author?
12. **Constrain the actors** — does anyone in the analysis do something their
    real-world constraints would not permit? Miracles make comfortable,
    useless rehearsals.

### 5. Score, through the code

Write and run a short script. Do not hand-write the scorecard in prose — the
point is that the gates fire on you too.

```python
from tactik_eval import DIMENSIONS, UNDETERMINED, DimensionScore, Scorecard

card = Scorecard(scores={
    "factual_correctness":  DimensionScore(band=70, rationale="..."),
    "protocol_adherence":   DimensionScore(band=55, rationale="..."),
    "deduction_quality":    DimensionScore(band=40, rationale="..."),
    "decision_usefulness":  DimensionScore(band=65, rationale="..."),
    "calibration":          DimensionScore(band=UNDETERMINED,
                                           rationale="no outcome data to check against"),
    "drift_control":        DimensionScore(band=60, rationale="..."),
    "completion":           DimensionScore(band=80, rationale="..."),
    "evidence_richness":    DimensionScore(band=35, rationale="..."),
})
print(card.to_payload())
print("unresolved:", card.undetermined)
```

Bands are integers 0–100. Every one needs a rationale. `UNDETERMINED` is
correct and expected when you have no basis — it is a finding, not a failure,
and it must say what is unresolved.

If `Scorecard(...)` raises, you left something blank. Fix it rather than
working around it.

**Do not call `aggregate()`.** It will refuse without a calibration
attestation, and rightly. Report the eight bands.

### 6. Report

Lead with the single most consequential finding, in one sentence.

Then:

- **What the document is trying to decide**, and whether that was fixed before
  or after the analysis.
- **Findings**, most severe first. Each one names the principle, quotes the
  passage, and says what it would take to fix. A finding without a quote is an
  impression.
- **The scorecard**, eight bands with rationales.
- **Unresolved**, in words. Everything you could not determine and why.
- **What this review does not establish** — be specific. If you did not check
  the underlying data, say so here rather than letting the reader assume you did.

Two standing prohibitions:

**Do not produce an overall grade.** Not a letter, not a percentage, not
"broadly sound." The dimensions are separate because a document can be
decisive and wrong, or correct and useless, and one number cannot say which.

**Do not audit your own work and call it validation.** If you wrote the
analysis, this review is debugging. Say that in the output.

## When uncertainty is not a NO

Do not let this skill turn into reflexive caution — that failure is as real as
overconfidence and easier to hide behind.

Epistemic uncertainty is not an automatic NO. A strong YES must remain
possible when the evidence is strong, and a reversible pilot can be justified
while the final outcome is unknown. If the evidence supports acting, say so
and say how far it supports acting. A review that never approves anything is
measuring its own timidity.
