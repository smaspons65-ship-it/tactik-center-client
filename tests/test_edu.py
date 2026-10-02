"""The Webscript lock and the readiness card refuse what they promise to refuse.

Each test attempts the convenient thing a deadline invites: lock with a question
nobody approved, drop the rule that refuses to write the candidate's work, store
a weight as a float, ask for a single readiness number. The gates must say no.
"""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tactik_eval import UNDETERMINED, CalibrationAttestation, PrematureCollapse, SealedObjective
from tactik_eval.canonical import CanonicalizationError
from tactik_eval.edu import (
    MANDATORY_EVENTS,
    MANDATORY_STOPS,
    NotLockable,
    ReadinessCard,
    ReadinessObservation,
    TeachingProfile,
    load_webscript,
    main,
)


def complete_payload() -> dict:
    """The smallest Webscript that passes every lock gate."""
    return {
        "format": "tactik-edu/webscript@1",
        "webscript_id": "unit",
        "version": 1,
        "supersedes": None,
        "course": {"code": "T 100", "title": "Test", "institution": "Fictional"},
        "objective": {
            "target": "defend the finding with evidence",
            "floor": "every criterion observed or undetermined with a reason",
            "must_not_happen": ["TACTIK writes the candidate's answer"],
        },
        "dossier": {"title": "t", "design": "cross-sectional", "facts": ["n = 10"]},
        "lenses": [
            {"key": "chair", "name": "Chair", "job": "j", "primary_lens": "p", "boundary": "b"}
        ],
        "states": [
            {"key": "orientation", "name": "O", "owner": "system", "goal": "g", "exit": "e"},
            {"key": "round", "name": "R", "owner": "chair", "goal": "g", "exit": "e"},
            {"key": "debrief", "name": "D", "owner": "system", "goal": "g", "exit": "e"},
        ],
        "pressure_levels": [
            {"level": 1, "definition": "gentle"},
            {"level": 2, "definition": "direct"},
            {"level": 3, "definition": "strongest rival put directly"},
        ],
        "questions": [
            {
                "qid": "Q01",
                "state": "round",
                "lens": "chair",
                "pressure": 1,
                "text": "Why this design?",
                "status": "APPROVED",
                "approved_by": "Faculty owner",
                "outcomes": ["CLO1"],
            }
        ],
        "event_rules": [
            {"event": e, "response": "respond", "prompt": "say this", "lens": None}
            for e in MANDATORY_EVENTS
        ],
        "stop_conditions": [{"key": k, "text": "stop"} for k in MANDATORY_STOPS],
        "visibility": {"student": ["claims"], "faculty": ["criteria"]},
        "rubric": {
            "weight_use": "prioritization",
            "status": "APPROVED",
            "approved_by": "Faculty owner",
            "criteria": [
                {"key": "method", "name": "Method", "evidence": "e", "weight_bp": 6000, "anchors": ["a", "b", "c", "d"]},
                {"key": "limits", "name": "Limits", "evidence": "e", "weight_bp": 4000, "anchors": ["a", "b", "c", "d"]},
            ],
        },
        "profile": {
            "challenge_intensity": 62,
            "evidence_strictness": 78,
            "evasions_before_reframe": 2,
            "format": "cold_call",
        },
    }


def codes(payload: dict) -> list[str]:
    return [code for code, _ in load_webscript(payload).lock_blockers()]


class TestWebscriptLock(unittest.TestCase):
    def test_a_complete_script_locks_and_yields_a_sealed_objective(self) -> None:
        webscript = load_webscript(complete_payload())
        self.assertEqual(webscript.lock_blockers(), ())
        self.assertIsInstance(webscript.require_lockable(), SealedObjective)

    def test_an_unapproved_question_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["questions"][0].update(status="DRAFT", approved_by=None)
        with self.assertRaises(NotLockable) as refused:
            load_webscript(payload).require_lockable()
        found = [code for code, _ in refused.exception.blockers]
        self.assertIn("QUESTION_PENDING", found)
        # A state left with no approved question cannot run at all.
        self.assertIn("STATE_WITHOUT_QUESTION", found)

    def test_approval_must_name_a_person(self) -> None:
        payload = complete_payload()
        payload["questions"][0]["approved_by"] = "  "
        self.assertEqual(codes(payload), ["QUESTION_UNATTRIBUTED"])

    def test_undefined_pressure_levels_block_the_lock(self) -> None:
        payload = complete_payload()
        payload["pressure_levels"][1]["definition"] = ""
        del payload["pressure_levels"][2]
        self.assertEqual(codes(payload), ["PRESSURE_UNDEFINED", "PRESSURE_UNDEFINED"])

    def test_the_refusal_to_write_student_work_cannot_be_removed(self) -> None:
        payload = complete_payload()
        payload["event_rules"] = [r for r in payload["event_rules"] if r["event"] != "answer_request"]
        self.assertEqual(codes(payload), ["EVENT_RULE_MISSING"])

    def test_a_mandatory_stop_condition_cannot_be_removed(self) -> None:
        payload = complete_payload()
        payload["stop_conditions"] = [
            s for s in payload["stop_conditions"] if s["key"] != "generates_student_work"
        ]
        self.assertEqual(codes(payload), ["STOP_CONDITION_MISSING"])

    def test_a_rule_without_candidate_wording_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["event_rules"][0]["prompt"] = "  "
        self.assertEqual(codes(payload), ["EVENT_RULE_MISSING"])

    def test_a_rule_spoken_by_an_unknown_lens_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["event_rules"].append(
            {"event": "causal_language", "response": "r", "prompt": "p", "lens": "methodologist"}
        )
        self.assertEqual(codes(payload), ["EVENT_LENS_UNKNOWN"])

    def test_an_empty_dossier_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["dossier"]["facts"] = ["", "  "]
        self.assertEqual(codes(payload), ["DOSSIER_EMPTY"])

    def test_faculty_may_add_a_stop_condition(self) -> None:
        payload = complete_payload()
        payload["stop_conditions"].append({"key": "faculty_6", "text": "candidate is distressed"})
        self.assertEqual(codes(payload), [])

    def test_a_session_must_be_bounded_by_system_states(self) -> None:
        payload = complete_payload()
        payload["states"] = payload["states"][:2]
        self.assertIn("STATES_UNBOUNDED", codes(payload))

    def test_a_question_asked_by_the_wrong_lens_is_misplaced(self) -> None:
        payload = complete_payload()
        payload["lenses"].append(
            {"key": "skeptic", "name": "S", "job": "j", "primary_lens": "p", "boundary": "b"}
        )
        payload["questions"][0]["lens"] = "skeptic"
        self.assertIn("QUESTION_MISPLACED", codes(payload))

    def test_weights_must_total_ten_thousand_basis_points(self) -> None:
        payload = complete_payload()
        payload["rubric"]["criteria"][0]["weight_bp"] = 5000
        self.assertEqual(codes(payload), ["RUBRIC_WEIGHTS"])

    def test_a_float_weight_is_refused_at_construction(self) -> None:
        payload = complete_payload()
        payload["rubric"]["criteria"][0]["weight_bp"] = 0.6
        with self.assertRaises(ValueError):
            load_webscript(payload)

    def test_a_float_anywhere_cannot_be_sealed(self) -> None:
        payload = complete_payload()
        payload["dossier"]["effect_size"] = 0.41
        with self.assertRaises(CanonicalizationError):
            load_webscript(payload).seal

    def test_an_unapproved_rubric_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["rubric"].update(status="DRAFT", approved_by=None)
        self.assertEqual(codes(payload), ["RUBRIC_PENDING"])

    def test_a_blank_objective_floor_blocks_the_lock(self) -> None:
        payload = complete_payload()
        payload["objective"]["floor"] = ""
        self.assertEqual(codes(payload), ["OBJECTIVE_INCOMPLETE"])

    def test_editing_a_question_changes_the_seal(self) -> None:
        payload = complete_payload()
        before = load_webscript(payload).seal
        payload["questions"][0]["text"] = "Why this design, really?"
        self.assertNotEqual(before, load_webscript(payload).seal)

    def test_seal_survives_a_round_trip_through_its_payload(self) -> None:
        webscript = load_webscript(complete_payload())
        reloaded = load_webscript(json.loads(json.dumps(webscript.to_payload())))
        self.assertEqual(webscript.seal, reloaded.seal)

    def test_a_field_outside_the_format_is_refused_not_dropped(self) -> None:
        """A dropped field would leave the seal not covering what was exported."""
        for path in (("operator_note",), ("objective", "override"), ("rubric", "composite_formula")):
            with self.subTest(path=path):
                payload = complete_payload()
                target = payload
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = "hidden"
                with self.assertRaises(ValueError):
                    load_webscript(payload)

    def test_unknown_question_status_is_malformed_not_a_blocker(self) -> None:
        payload = complete_payload()
        payload["questions"][0]["status"] = "APPROVED_BY_TACTIK"
        with self.assertRaises(ValueError):
            load_webscript(payload)


class TestTeachingProfile(unittest.TestCase):
    def test_challenge_intensity_sets_the_starting_pressure(self) -> None:
        for intensity, level in ((0, 1), (33, 1), (34, 2), (66, 2), (67, 3), (100, 3)):
            with self.subTest(intensity=intensity):
                profile = TeachingProfile(intensity, 50, 2, "cold_call")
                self.assertEqual(profile.starting_pressure, level)

    def test_strictness_decides_whether_confidence_escalates(self) -> None:
        self.assertTrue(TeachingProfile(50, 50, 2, "seminar").escalates_on_confidence)
        self.assertFalse(TeachingProfile(50, 49, 2, "seminar").escalates_on_confidence)

    def test_out_of_range_parameters_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            TeachingProfile(101, 50, 2, "cold_call")
        with self.assertRaises(ValueError):
            TeachingProfile(50, 50, 0, "cold_call")
        with self.assertRaises(ValueError):
            TeachingProfile(50, 50, 2, "avatar")


class TestReadinessCard(unittest.TestCase):
    def setUp(self) -> None:
        self.rubric = load_webscript(complete_payload()).rubric
        self.calibration = CalibrationAttestation(
            method="two raters scored 20 reference defenses against the anchors",
            attested_by="External methodologist",
            reference_runs=("ref-01",),
        )

    def card(self, rubric=None, **levels) -> ReadinessCard:
        observations = {
            key: ReadinessObservation(level, "" if level == UNDETERMINED else "ref", "unresolved" if level == UNDETERMINED else "")
            for key, level in levels.items()
        }
        return ReadinessCard(rubric or self.rubric, observations)

    def test_a_silent_criterion_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            self.card(method=2)

    def test_undetermined_requires_saying_what_is_unresolved(self) -> None:
        with self.assertRaises(ValueError):
            ReadinessObservation(UNDETERMINED, "", "  ")

    def test_a_level_must_cite_its_evidence(self) -> None:
        with self.assertRaises(ValueError):
            ReadinessObservation(2, "", "")

    def test_a_composite_is_refused_when_weights_are_for_prioritization(self) -> None:
        card = self.card(method=2, limits=1)
        with self.assertRaises(PrematureCollapse):
            card.composite(self.calibration)

    def test_a_composite_is_refused_without_calibration_even_when_permitted(self) -> None:
        payload = complete_payload()
        payload["rubric"]["weight_use"] = "composite"
        card = self.card(load_webscript(payload).rubric, method=2, limits=1)
        with self.assertRaises(PrematureCollapse):
            card.composite()

    def test_composite_with_both_keys_excludes_undetermined_rather_than_zeroing(self) -> None:
        payload = complete_payload()
        payload["rubric"]["weight_use"] = "composite"
        rubric = load_webscript(payload).rubric
        both = self.card(rubric, method=2, limits=1)
        # (2*100*6000 + 1*100*4000) // 10000
        self.assertEqual(both.composite(self.calibration), 160)
        partial = self.card(rubric, method=2, limits=UNDETERMINED)
        self.assertEqual(partial.composite(self.calibration), 200)
        self.assertEqual(partial.undetermined, ("limits",))

    def test_prioritized_order_follows_weight(self) -> None:
        self.assertEqual([c.key for c in self.rubric.prioritized()], ["method", "limits"])


class TestCommandLine(unittest.TestCase):
    def run_main(self, document: dict) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "webscript.json"
            path.write_text(json.dumps(document), "utf-8")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = main(["edu", str(path)])
            return code, out.getvalue() + err.getvalue()

    def test_a_lockable_export_with_its_seal_passes(self) -> None:
        payload = complete_payload()
        seal = load_webscript(payload).seal
        code, output = self.run_main({"webscript": payload, "seal": seal})
        self.assertEqual(code, 0, output)
        self.assertIn("matches", output)

    def test_a_recorded_seal_that_does_not_match_fails(self) -> None:
        payload = complete_payload()
        seal = load_webscript(payload).seal
        edited = copy.deepcopy(payload)
        edited["questions"][0]["text"] = "edited after the seal was recorded"
        code, output = self.run_main({"webscript": edited, "seal": seal})
        self.assertEqual(code, 1)
        self.assertIn("MISMATCH", output)

    def test_an_unfinished_script_fails_and_lists_its_blockers(self) -> None:
        payload = complete_payload()
        payload["questions"][0].update(status="DRAFT", approved_by=None)
        code, output = self.run_main(payload)
        self.assertEqual(code, 1)
        self.assertIn("QUESTION_PENDING", output)


if __name__ == "__main__":
    unittest.main()
