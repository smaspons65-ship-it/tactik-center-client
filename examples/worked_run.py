"""A worked run, end to end, producing a ledger a stranger can check.

    python3 examples/worked_run.py /tmp/ledger.json
    node verify/verify.mjs /tmp/ledger.json
    python3 -m tactik_eval.verify /tmp/ledger.json

The scenario is deliberately unflattering: three cases, two runs, one of which
is contaminated and therefore scores nothing, and one published figure that
turns out to be wrong and is withdrawn rather than quietly recomputed.
"""

from __future__ import annotations

import json
import sys

from tactik_eval import (
    DIMENSIONS,
    UNDETERMINED,
    BlindingAttestation,
    Breach,
    Case,
    CasePack,
    CorrectBehavior,
    DimensionScore,
    Ledger,
    Run,
    RunConditions,
    Scorecard,
    SealedObjective,
)


def build_pack() -> CasePack:
    """Three cases whose correct answers are YES, NO and BOUNDED."""
    supply = SealedObjective(
        target="renewal at or above 4.20/unit for 24 months",
        floor="3.90/unit, below which we do not sign",
        must_not_happen=("exclusivity", "volume commitment beyond Q3"),
    )
    distress = SealedObjective(
        target="exit the contract with no termination fee",
        floor="fee at or below 40000 minor units",
        must_not_happen=("public statement of fault", "12-month non-compete"),
    )
    unclear = SealedObjective(
        target="written commitment to a pilot in Q1",
        floor="a scheduled second meeting with the decision owner present",
        must_not_happen=("pricing disclosed before the pilot is agreed",),
    )

    return CasePack(
        pack_id="pack-2026-07",
        cases=(
            Case(
                case_id="supply-renewal",
                objective=supply,
                evidence=(
                    "counterparty opened at 4.35 unprompted",
                    "their Q4 supply gap is public and unresolved",
                    "they have renewed on our terms twice before",
                ),
                correct_behavior=CorrectBehavior.YES,
                actor_constraints=(
                    "buyer cannot commit past their fiscal year without board sign-off",
                ),
                notes="Strong evidence. A protocol that cannot say YES here is timid, "
                "not rigorous.",
            ),
            Case(
                case_id="distress-exit",
                objective=distress,
                evidence=(
                    "counterparty has no repeat business available to us",
                    "their counsel opened with a termination-fee demand of 180000",
                    "they refused to schedule any follow-up",
                ),
                correct_behavior=CorrectBehavior.NO,
                notes="Margin given to someone with no future is a donation (P01).",
            ),
            Case(
                case_id="ambiguous-pilot",
                objective=unclear,
                evidence=(
                    "warm meeting, no commitment of any kind",
                    "the person in the room does not own the budget",
                    "one cold sentence about timing, otherwise cordial",
                ),
                correct_behavior=CorrectBehavior.BOUNDED,
                notes="P02: neither yes nor walk out. Buy time, manufacture the "
                "second meeting. P04: the warmth is not evidence of receptiveness.",
            ),
        ),
    )


def main(argv: list[str]) -> int:
    out_path = argv[1] if len(argv) > 1 else "ledger.json"

    pack = build_pack()
    pack.require_full_decision_range()

    conditions = RunConditions(
        model="baseline-model", tools=(), retrieval="none", fresh_session=True
    )

    ledger = Ledger()
    ledger.append(
        "pack_sealed",
        {
            "pack_id": pack.pack_id,
            "pack_seal": pack.seal,
            "case_count": len(pack.cases),
            "sealed_by": "S. Maspons",
        },
    )

    # --- Run 1: the wall was crossed. It scores nothing. -------------------
    contaminated = Run(
        run_id="run-001",
        case_seal=pack.case("ambiguous-pilot").seal,
        conditions=conditions,
        blinding=BlindingAttestation(
            objective_holder="S. Maspons",
            negotiator="operator-a",
            grader="grader-b",
            negotiator_saw_objective=False,
            holder_watched_live=True,
            breaches=(
                Breach(
                    what="objective holder joined the live channel at turn 4",
                    when="2026-07-31T14:02:00Z",
                    recorded_by="grader-b",
                ),
            ),
        ),
        scorecard=Scorecard(
            scores={name: DimensionScore(band=88, rationale="graded") for name in DIMENSIONS}
        ),
        subject="doctrine-v1",
    )
    ledger.append(
        "run_voided",
        {
            "run_id": contaminated.run_id,
            "case_seal": contaminated.case_seal,
            "result": str(contaminated.result()),
            "reasons": list(contaminated.blinding.contamination()),
        },
    )

    # --- Run 2: clean, independently graded, honestly undetermined ---------
    clean = Run(
        run_id="run-002",
        case_seal=pack.case("distress-exit").seal,
        conditions=conditions,
        blinding=BlindingAttestation(
            objective_holder="S. Maspons",
            negotiator="operator-a",
            grader="grader-b",
            negotiator_saw_objective=False,
            holder_watched_live=False,
        ),
        scorecard=Scorecard(
            scores={
                "factual_correctness": DimensionScore(
                    band=80, rationale="every claim traced to the evidence pack"
                ),
                "protocol_adherence": DimensionScore(
                    band=90, rationale="objective sealed before turn 1"
                ),
                "deduction_quality": DimensionScore(
                    band=70, rationale="one inference leaned on tone rather than record"
                ),
                "decision_usefulness": DimensionScore(
                    band=75, rationale="named the walk-away and the trigger for it"
                ),
                "calibration": DimensionScore(
                    band=UNDETERMINED,
                    rationale="no post-hoc outcome data; calibration cannot be "
                    "asserted from a single run",
                ),
                "drift_control": DimensionScore(
                    band=65, rationale="restated the objective at turn 6 accurately"
                ),
                "completion": DimensionScore(
                    band=85, rationale="reached a decision within the turn budget"
                ),
                "evidence_richness": DimensionScore(
                    band=55, rationale="thin: three evidence lines, none independent"
                ),
            }
        ),
        subject="doctrine-v1",
    )
    clean.require_independent_grading()
    scorecard = clean.require_measurement()

    ledger.append(
        "run_scored",
        {
            "run_id": clean.run_id,
            "case_seal": clean.case_seal,
            "conditions_seal": clean.conditions.seal,
            "scorecard": scorecard.to_payload(),
            "undetermined": list(scorecard.undetermined),
        },
    )

    # --- A published figure turns out to be wrong (P10) --------------------
    ledger.append(
        "aggregate_published",
        {"run_id": "run-002", "claimed_aggregate": 74, "basis": "mean of eight bands"},
    )
    ledger.withdraw(
        3,
        reason=(
            "aggregate was computed across uncalibrated bands and counted an "
            "UNDETERMINED dimension as zero; the figure has no referent"
        ),
        withdrawn_by="S. Maspons",
    )
    ledger.append(
        "aggregate_retracted_no_replacement",
        {
            "run_id": "run-002",
            "supersedes_index": 3,
            "statement": "no aggregate is published for this run; the scorecard "
            "stands on its own until calibration is established",
        },
    )

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(ledger.to_payload(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"pack seal : {pack.seal}")
    print(f"entries   : {len(ledger)}")
    print(f"standing  : {len(ledger.standing())}")
    print(f"head      : {ledger.head}")
    print(f"written   : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
