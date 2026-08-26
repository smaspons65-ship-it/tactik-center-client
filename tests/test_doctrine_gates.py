"""Each test pins one doctrine rule that would otherwise be waivable.

Run: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from tactik_eval import (
    DIMENSIONS,
    NO_SCORE,
    UNDETERMINED,
    BlankScore,
    BlindingAttestation,
    Breach,
    CalibrationAttestation,
    CanonicalizationError,
    Case,
    CasePack,
    ContaminatedRun,
    CorrectBehavior,
    CoverageError,
    DimensionScore,
    Ledger,
    LedgerTampered,
    PrematureCollapse,
    Reissued,
    Run,
    RunConditions,
    Scorecard,
    SealBroken,
    SealedObjective,
    SelfGraded,
    canonical_bytes,
    digest,
    load_pack,
)


def an_objective(**overrides) -> SealedObjective:
    kwargs = {
        "target": "unit price at or above 4.20",
        "floor": "3.90, below which we walk",
        "must_not_happen": ("exclusivity clause", "volume commitment past Q3"),
    }
    kwargs.update(overrides)
    return SealedObjective(**kwargs)


def a_case(case_id: str = "c1", behavior: str = CorrectBehavior.BOUNDED) -> Case:
    return Case(
        case_id=case_id,
        objective=an_objective(),
        evidence=("buyer opened at 3.10", "buyer's Q4 supply gap is public"),
        correct_behavior=behavior,
    )


def a_scorecard(**overrides) -> Scorecard:
    scores = {
        name: DimensionScore(band=70, rationale="baseline") for name in DIMENSIONS
    }
    scores.update(overrides)
    return Scorecard(scores=scores)


def a_blinding(**overrides) -> BlindingAttestation:
    kwargs = {
        "objective_holder": "S. Maspons",
        "negotiator": "operator-a",
        "grader": "grader-b",
        "negotiator_saw_objective": False,
        "holder_watched_live": False,
    }
    kwargs.update(overrides)
    return BlindingAttestation(**kwargs)


def a_run(**overrides) -> Run:
    kwargs = {
        "run_id": "r1",
        "case_seal": a_case().seal,
        "conditions": RunConditions(
            model="m", tools=("search",), retrieval="none", fresh_session=True
        ),
        "blinding": a_blinding(),
        "scorecard": a_scorecard(),
        "subject": "doctrine-v1",
    }
    kwargs.update(overrides)
    return Run(**kwargs)


class TestCanonicalForm(unittest.TestCase):
    """P11: the recipe must be reimplementable, so it must be unambiguous."""

    def test_key_order_does_not_change_the_hash(self) -> None:
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))

    def test_array_order_does_change_the_hash(self) -> None:
        self.assertNotEqual(digest([1, 2]), digest([2, 1]))

    def test_floats_are_refused_rather_than_coerced(self) -> None:
        with self.assertRaises(CanonicalizationError) as caught:
            digest({"price": 4.2})
        self.assertIn("decimal string", str(caught.exception))

    def test_floats_are_refused_when_nested(self) -> None:
        with self.assertRaises(CanonicalizationError) as caught:
            digest({"runs": [{"bands": [1, 2.5]}]})
        self.assertIn("$.runs[0].bands[1]", str(caught.exception))

    def test_non_ascii_is_emitted_literally(self) -> None:
        self.assertIn("señor".encode(), canonical_bytes({"who": "señor"}))

    def test_no_insignificant_whitespace(self) -> None:
        self.assertEqual(canonical_bytes({"a": [1, 2]}), b'{"a":[1,2]}')


class TestSealedObjective(unittest.TestCase):
    """P07: the goal is sealed before the outcome can write it."""

    def test_objective_without_a_floor_is_refused(self) -> None:
        with self.assertRaises(ValueError) as caught:
            an_objective(floor="   ")
        self.assertIn("retroactively", str(caught.exception))

    def test_objective_without_must_not_happen_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            an_objective(must_not_happen=())

    def test_editing_the_objective_breaks_the_seal(self) -> None:
        sealed = an_objective().seal
        moved = an_objective(target="unit price at or above 3.95")
        self.assertNotEqual(sealed, moved.seal)


class TestCasePackCoverage(unittest.TestCase):
    """A suite built in the image of one disposition measures that disposition."""

    def test_pack_missing_a_decision_mode_is_refused(self) -> None:
        pack = CasePack(
            pack_id="p1",
            cases=(
                a_case("c1", CorrectBehavior.NO),
                a_case("c2", CorrectBehavior.NO),
            ),
        )
        with self.assertRaises(CoverageError) as caught:
            pack.require_full_decision_range()
        message = str(caught.exception)
        self.assertIn("BOUNDED", message)
        self.assertIn("YES", message)

    def test_pack_covering_all_three_passes(self) -> None:
        pack = CasePack(
            pack_id="p1",
            cases=(
                a_case("c1", CorrectBehavior.YES),
                a_case("c2", CorrectBehavior.NO),
                a_case("c3", CorrectBehavior.BOUNDED),
            ),
        )
        pack.require_full_decision_range()

    def test_duplicate_case_ids_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            CasePack(pack_id="p1", cases=(a_case("c1"), a_case("c1")))

    def test_changed_evidence_breaks_the_pack_seal(self) -> None:
        pack = CasePack(pack_id="p1", cases=(a_case("c1"),))
        frozen = pack.seal
        tampered = CasePack(
            pack_id="p1",
            cases=(
                Case(
                    case_id="c1",
                    objective=an_objective(),
                    evidence=("buyer opened at 3.10",),  # one line removed
                    correct_behavior=CorrectBehavior.BOUNDED,
                ),
            ),
        )
        with self.assertRaises(SealBroken):
            tampered.verify_seal(frozen)

    def test_pack_round_trips_through_its_payload(self) -> None:
        pack = CasePack(
            pack_id="p1",
            cases=(a_case("c1", CorrectBehavior.YES), a_case("c2", CorrectBehavior.NO)),
        )
        self.assertEqual(load_pack(pack.to_payload()).seal, pack.seal)


class TestRubric(unittest.TestCase):
    """P09 and the no-collapse rule."""

    def test_omitted_dimension_is_an_error_not_a_pass(self) -> None:
        partial = {
            name: DimensionScore(band=70, rationale="ok")
            for name in DIMENSIONS
            if name != "drift_control"
        }
        with self.assertRaises(BlankScore) as caught:
            Scorecard(scores=partial)
        self.assertIn("drift_control", str(caught.exception))

    def test_undetermined_requires_saying_what_is_unresolved(self) -> None:
        with self.assertRaises(BlankScore):
            DimensionScore(band=UNDETERMINED, rationale="")

    def test_undetermined_is_accepted_when_explained(self) -> None:
        score = DimensionScore(
            band=UNDETERMINED, rationale="no post-hoc outcome data yet"
        )
        self.assertTrue(score.is_undetermined)

    def test_aggregate_refuses_without_calibration(self) -> None:
        with self.assertRaises(PrematureCollapse) as caught:
            a_scorecard().aggregate()
        self.assertIn("calibration", str(caught.exception))

    def test_aggregate_allowed_once_calibration_is_attested(self) -> None:
        calibration = CalibrationAttestation(
            method="anchored against 12 hand-graded reference runs",
            attested_by="grader-b",
            reference_runs=("r-ref-01", "r-ref-02"),
        )
        self.assertEqual(a_scorecard().aggregate(calibration), 70)

    def test_calibration_cannot_be_asserted_without_reference_runs(self) -> None:
        with self.assertRaises(ValueError):
            CalibrationAttestation(
                method="vibes", attested_by="someone", reference_runs=()
            )

    def test_undetermined_dimensions_are_excluded_not_zeroed(self) -> None:
        calibration = CalibrationAttestation(
            method="anchored", attested_by="grader-b", reference_runs=("r-ref-01",)
        )
        card = a_scorecard(
            calibration=DimensionScore(band=UNDETERMINED, rationale="no outcome data")
        )
        # Scoring an unresolved dimension as zero would silently punish honesty.
        self.assertEqual(card.aggregate(calibration), 70)
        self.assertEqual(card.undetermined, ("calibration",))

    def test_band_outside_range_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            DimensionScore(band=140, rationale="excellent")


class TestBlinding(unittest.TestCase):
    """P08: a contaminated measurement is not a weak measurement."""

    def test_clean_run_yields_its_scorecard(self) -> None:
        run = a_run()
        self.assertIs(run.result(), run.scorecard)
        self.assertIs(run.require_measurement(), run.scorecard)

    def test_negotiator_knowing_the_objective_voids_the_run(self) -> None:
        run = a_run(blinding=a_blinding(negotiator_saw_objective=True))
        self.assertEqual(run.result(), NO_SCORE)
        with self.assertRaises(ContaminatedRun) as caught:
            run.require_measurement()
        self.assertIn("steering", str(caught.exception))

    def test_holder_watching_live_voids_the_run(self) -> None:
        run = a_run(blinding=a_blinding(holder_watched_live=True))
        self.assertEqual(run.result(), NO_SCORE)

    def test_recorded_breach_voids_the_run(self) -> None:
        run = a_run(
            blinding=a_blinding(
                breaches=(
                    Breach(
                        what="observer joined the live channel",
                        when="2026-07-31T14:02:00Z",
                        recorded_by="grader-b",
                    ),
                )
            )
        )
        self.assertEqual(run.result(), NO_SCORE)
        self.assertIn("observer joined", run.blinding.contamination()[0])

    def test_void_is_not_a_score_of_zero(self) -> None:
        run = a_run(blinding=a_blinding(negotiator_saw_objective=True))
        self.assertNotEqual(run.result(), 0)
        self.assertEqual(run.result(), NO_SCORE)

    def test_roles_must_be_named(self) -> None:
        with self.assertRaises(ValueError):
            a_blinding(grader="")


class TestSelfGrading(unittest.TestCase):
    """A protocol must not grade itself as proof of effectiveness."""

    def test_subject_grading_itself_is_refused_as_validation(self) -> None:
        run = a_run(subject="doctrine-v1", blinding=a_blinding(grader="doctrine-v1"))
        with self.assertRaises(SelfGraded) as caught:
            run.require_independent_grading()
        self.assertIn("debugging", str(caught.exception))

    def test_independent_grader_passes(self) -> None:
        a_run().require_independent_grading()


class TestRunConditions(unittest.TestCase):
    """An A/B whose arms differ elsewhere attributes the difference wrongly."""

    def test_differing_conditions_are_named(self) -> None:
        baseline = RunConditions(
            model="m1", tools=("search",), retrieval="none", fresh_session=True
        )
        governed = RunConditions(
            model="m2", tools=("search",), retrieval="web", fresh_session=True
        )
        self.assertEqual(baseline.differences_from(governed), ("model", "retrieval"))

    def test_identical_conditions_differ_in_nothing(self) -> None:
        conditions = RunConditions(
            model="m1", tools=("search", "calc"), retrieval="none", fresh_session=True
        )
        self.assertEqual(conditions.differences_from(conditions), ())

    def test_tool_order_is_not_a_difference(self) -> None:
        a = RunConditions(
            model="m", tools=("search", "calc"), retrieval="none", fresh_session=True
        )
        b = RunConditions(
            model="m", tools=("calc", "search"), retrieval="none", fresh_session=True
        )
        self.assertEqual(a.differences_from(b), ())


class TestLedger(unittest.TestCase):
    """P10: correct by addition, never by mutation."""

    def test_ledger_exposes_no_mutation_path(self) -> None:
        for forbidden in ("update", "edit", "delete", "remove", "replace"):
            self.assertFalse(
                hasattr(Ledger, forbidden),
                f"Ledger must not expose {forbidden}()",
            )

    def test_withdrawal_preserves_the_original(self) -> None:
        ledger = Ledger()
        original = ledger.append("score", {"run_id": "r1", "band": 100})
        ledger.withdraw(0, reason="grader was not blind", withdrawn_by="S. Maspons")

        self.assertEqual(len(ledger), 2)
        self.assertEqual(ledger.entries[0].body["band"], 100)
        self.assertTrue(ledger.is_withdrawn(original))
        self.assertEqual(ledger.standing(), ())

    def test_withdrawn_content_cannot_be_reissued(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 100})
        ledger.withdraw(0, reason="grader was not blind", withdrawn_by="S. Maspons")
        with self.assertRaises(Reissued) as caught:
            ledger.append("score", {"run_id": "r1", "band": 100})
        self.assertIn("Correct by addition", str(caught.exception))

    def test_a_corrected_figure_may_be_published_as_new_content(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 100})
        ledger.withdraw(0, reason="grader was not blind", withdrawn_by="S. Maspons")
        corrected = ledger.append(
            "score", {"run_id": "r1", "band": 61, "supersedes": 0}
        )
        self.assertEqual(ledger.standing(), (corrected,))

    def test_withdrawal_requires_a_public_reason_and_an_author(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 100})
        with self.assertRaises(ValueError):
            ledger.withdraw(0, reason="", withdrawn_by="S. Maspons")
        with self.assertRaises(ValueError):
            ledger.withdraw(0, reason="wrong", withdrawn_by="")

    def test_head_changes_on_every_append(self) -> None:
        ledger = Ledger()
        heads = {ledger.head}
        for index in range(4):
            ledger.append("note", {"n": index})
            heads.add(ledger.head)
        self.assertEqual(len(heads), 5)

    def test_chain_verifies_when_intact(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 70})
        ledger.append("score", {"run_id": "r2", "band": 55})
        ledger.verify_chain()

    def test_rewriting_history_is_detected(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 55})
        ledger.append("score", {"run_id": "r2", "band": 60})
        payload = ledger.to_payload()

        # Improve the first score after the fact, as one would.
        payload["entries"][0]["body"]["band"] = 95

        with self.assertRaises(LedgerTampered):
            Ledger.from_payload(payload)

    def test_round_trip_of_an_untampered_ledger(self) -> None:
        ledger = Ledger()
        ledger.append("score", {"run_id": "r1", "band": 55})
        ledger.withdraw(0, reason="arithmetic error", withdrawn_by="S. Maspons")
        ledger.append("score", {"run_id": "r1", "band": 51, "supersedes": 0})

        restored = Ledger.from_payload(ledger.to_payload())
        self.assertEqual(restored.head, ledger.head)
        self.assertEqual(len(restored.standing()), 1)


if __name__ == "__main__":
    unittest.main()
