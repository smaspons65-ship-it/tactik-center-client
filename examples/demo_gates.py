"""Watch the gates refuse.

    python3 examples/demo_gates.py

Every block below attempts something a person under deadline pressure would
plausibly do, and shows what the engine says back. The point is not that these
are bad ideas — it is that none of them require anyone to be watching.
"""

from __future__ import annotations

from tactik_eval import (
    DIMENSIONS,
    NO_SCORE,
    UNDETERMINED,
    BlindingAttestation,
    CalibrationAttestation,
    Case,
    CasePack,
    CorrectBehavior,
    DimensionScore,
    Ledger,
    Run,
    RunConditions,
    Scorecard,
    SealedObjective,
    digest,
)

WIDTH = 74


def header(number: int, title: str, principle: str) -> None:
    print()
    print("─" * WIDTH)
    print(f"  {number}. {title}")
    print(f"     {principle}")
    print("─" * WIDTH)


def attempt(description: str) -> None:
    print(f"\n  attempt   {description}")


def refused(error: Exception) -> None:
    label = "refused"
    for line in str(error).splitlines():
        print(f"  {label:9} {line}")
        label = ""
    print()


def allowed(message: str) -> None:
    print(f"  allowed   {message}\n")


def good_objective() -> SealedObjective:
    return SealedObjective(
        target="renewal at or above 4.20/unit",
        floor="3.90/unit, below which we do not sign",
        must_not_happen=("exclusivity", "volume commitment beyond Q3"),
    )


def full_scorecard(band: int = 70) -> Scorecard:
    return Scorecard(
        scores={n: DimensionScore(band=band, rationale="graded") for n in DIMENSIONS}
    )


def clean_blinding(**overrides) -> BlindingAttestation:
    kwargs = dict(
        objective_holder="S. Maspons",
        negotiator="operator-a",
        grader="grader-b",
        negotiator_saw_objective=False,
        holder_watched_live=False,
    )
    kwargs.update(overrides)
    return BlindingAttestation(**kwargs)


def main() -> None:
    print()
    print("=" * WIDTH)
    print("  THE SANTIAGO DOCTRINE — GATES".center(WIDTH))
    print("  eight attempts to do the convenient thing".center(WIDTH))
    print("=" * WIDTH)

    # 1 ---------------------------------------------------------------------
    header(1, "Start a session without a walk-away floor", "P07 — seal the goal first")
    attempt('objective with a target but floor=""')
    try:
        SealedObjective(
            target="get the best deal we can",
            floor="",
            must_not_happen=("exclusivity",),
        )
    except ValueError as error:
        refused(error)

    # 2 ---------------------------------------------------------------------
    header(2, "Build a test suite that can only say NO", "P02 — probe, don't binary")
    attempt("a pack whose every case should end in NO")
    pack = CasePack(
        pack_id="cautious-pack",
        cases=tuple(
            Case(
                case_id=f"c{i}",
                objective=good_objective(),
                evidence=("counterparty opened low",),
                correct_behavior=CorrectBehavior.NO,
            )
            for i in range(1, 4)
        ),
    )
    try:
        pack.require_full_decision_range()
    except Exception as error:
        refused(error)

    # 3 ---------------------------------------------------------------------
    header(3, "Leave the awkward dimension blank", "P09 — undetermined, not blank")
    attempt("a scorecard omitting calibration, which we have no data for")
    partial = {
        n: DimensionScore(band=80, rationale="graded")
        for n in DIMENSIONS
        if n != "calibration"
    }
    try:
        Scorecard(scores=partial)
    except Exception as error:
        refused(error)

    attempt('the same scorecard with calibration marked UNDETERMINED')
    card = Scorecard(
        scores={
            **partial,
            "calibration": DimensionScore(
                band=UNDETERMINED, rationale="no post-hoc outcome data yet"
            ),
        }
    )
    allowed(f"scored, with {card.undetermined[0]!r} recorded as unresolved")

    # 4 ---------------------------------------------------------------------
    header(4, "Ask for one headline number", "evaluation doctrine — no premature collapse")
    attempt("aggregate() across the eight bands")
    try:
        card.aggregate()
    except Exception as error:
        refused(error)

    attempt("aggregate() with calibration attested against reference runs")
    calibration = CalibrationAttestation(
        method="anchored against 12 hand-graded reference runs",
        attested_by="grader-b",
        reference_runs=("r-ref-01", "r-ref-02"),
    )
    print(f"  allowed   aggregate = {card.aggregate(calibration)}")
    print("            (the UNDETERMINED dimension is excluded, never zeroed)\n")

    # 5 ---------------------------------------------------------------------
    header(5, "Score a run where the wall was crossed", "P08 — blind the roles")
    contaminated = Run(
        run_id="run-001",
        case_seal=digest({"case": "ambiguous-pilot"}),
        conditions=RunConditions(
            model="m", tools=(), retrieval="none", fresh_session=True
        ),
        blinding=clean_blinding(holder_watched_live=True),
        scorecard=full_scorecard(88),
        subject="doctrine-v1",
    )
    attempt("read the result of a run the objective-holder watched live")
    print(f"  returned  {contaminated.result()}")
    print(f"            (not 0 — zero is a measurement, this is the absence of one)")
    attempt("force the scorecard out of it anyway")
    try:
        contaminated.require_measurement()
    except Exception as error:
        refused(error)

    # 6 ---------------------------------------------------------------------
    header(6, "Grade our own protocol", "a protocol must not grade itself")
    attempt("subject 'doctrine-v1' graded by 'doctrine-v1'")
    self_graded = Run(
        run_id="run-002",
        case_seal=digest({"case": "distress-exit"}),
        conditions=RunConditions(
            model="m", tools=(), retrieval="none", fresh_session=True
        ),
        blinding=clean_blinding(grader="doctrine-v1"),
        scorecard=full_scorecard(91),
        subject="doctrine-v1",
    )
    try:
        self_graded.require_independent_grading()
    except Exception as error:
        refused(error)

    # 7 ---------------------------------------------------------------------
    header(7, "Quietly fix a published number", "P10 — add, never overwrite")
    ledger = Ledger()
    ledger.append("score", {"run_id": "run-002", "band": 100})
    print(f"\n  published  band=100 at index 0")
    print(f"  head       {ledger.head[:32]}…")

    attempt("edit index 0 in place")
    print("  refused   Ledger has no update() and no delete() to call")
    for forbidden in ("update", "edit", "delete", "remove", "replace"):
        assert not hasattr(Ledger, forbidden)
    print("            (asserted above — the methods do not exist)\n")

    attempt("withdraw it publicly, then republish the identical figure")
    ledger.withdraw(0, reason="grader was not blind", withdrawn_by="S. Maspons")
    try:
        ledger.append("score", {"run_id": "run-002", "band": 100})
    except Exception as error:
        refused(error)

    attempt("publish a corrected figure as new content")
    ledger.append("score", {"run_id": "run-002", "band": 61, "supersedes": 0})
    allowed(
        f"{len(ledger)} entries, {len(ledger.standing())} standing, "
        "the original still readable at index 0"
    )
    print(f"  original  {ledger.entries[0].body}   <- unchanged, marked withdrawn")
    print(f"  head      {ledger.head[:32]}…\n")

    # 8 ---------------------------------------------------------------------
    header(8, "Improve the record after publishing", "P11 — be dispensable")
    payload = ledger.to_payload()
    print(f"\n  published head    {payload['head'][:32]}…")
    attempt("change the withdrawn 100 to a 61 so the history looks cleaner")
    payload["entries"][0]["body"]["band"] = 61
    from tactik_eval.record import Ledger as L

    try:
        L.from_payload(payload)
    except Exception as error:
        refused(error)
    print("  note      a second implementation in another language (verify/verify.mjs)")
    print("            catches this independently, from the prose spec alone.\n")

    print("=" * WIDTH)
    print("  Every refusal above happened with nobody watching.".center(WIDTH))
    print("=" * WIDTH)
    print()


if __name__ == "__main__":
    main()
