"""The Faculty Studio's JavaScript and tactik_eval's Python must agree, and the
studio must keep the promises the proposal makes about it.

Two implementations answer to docs/WEBSCRIPT.md and docs/HASHING.md: the core
script inside studio/faculty.html, and tactik_eval. This suite runs the studio's
own core under Node and checks its seals, blockers and ledgers with Python and
with verify/verify.mjs. Skipped, loudly, when Node is unavailable.

The static checks need no Node. The proposal says the browser prototype makes
no external AI call and carries no institution's name without permission
(pp.4, 22). Those are claims about a file, so they are checked against the file.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tactik_eval import Ledger
from tactik_eval.edu import load_webscript

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDIO = REPO_ROOT / "studio" / "faculty.html"
VERIFIER = REPO_ROOT / "verify" / "verify.mjs"
NODE = shutil.which("node")

VECTORS = ["", "abc", "señor · café — ✓", "a" * 1000, "日本語 🜛", "quote \" backslash \\ tab\t"]

HARNESS = r"""
const S = globalThis.StudioCore;
const out = {};
out.sha = VECTORS.map(S.sha256Hex);

const template = S.dbaTemplate();
out.template = { payload: template, seal: S.digest(template), blockers: S.lockBlockers(template) };

const done = JSON.parse(JSON.stringify(template));
done.pressure_levels.forEach((p) => { p.definition = S.PRESSURE_SUGGESTIONS[p.level]; });
done.questions.forEach((q) => { q.status = "APPROVED"; q.approved_by = "Faculty owner (fictional)"; });
done.rubric.status = "APPROVED";
done.rubric.approved_by = "Faculty owner (fictional)";
out.complete = { payload: done, seal: S.digest(done), blockers: S.lockBlockers(done) };

const seeded = S.seedState("Faculty owner (fictional)");
out.seed = S.ledgerPayload(seeded.ledger);
out.seedSelfCheck = S.verifyLedgerPayload(out.seed).ok;
out.contentRefs = Object.entries(seeded.content).map(([ref, v]) => ({ ref, salt: v.salt, text: v.text }));

const firstRef = Object.keys(seeded.content)[0];
delete seeded.content[firstRef];
S.appendEntry(seeded.ledger, "content_erased", { content_ref: firstRef, reason: "test", by: "Faculty owner (fictional)" });
out.erased = { ledger: S.ledgerPayload(seeded.ledger), ref: firstRef, remaining: Object.keys(seeded.content).length };

let floatRefused = false;
try { S.digest({ weight: 0.15 }); } catch (err) { floatRefused = true; }
out.floatRefused = floatRefused;

let withdrawalRefused = false;
try { S.appendEntry({ entries: [] }, "withdrawal", {}); } catch (err) { withdrawalRefused = true; }
out.withdrawalRefused = withdrawalRefused;

const run = S.runDryRun(template, S.DRY_RUN_SCRIPT);
out.run = {
  asked: run.steps.filter((s) => s.kind === "ask").map((s) => s.qid),
  candidateTurns: run.steps.filter((s) => s.kind === "candidate").length,
  preserved: run.preserved.length,
  declined: run.steps.filter((s) => s.kind === "rule" && s.event === "answer_request").length,
  start: run.startPressure,
  end: run.finalPressure,
};
const allDraft = JSON.parse(JSON.stringify(template));
allDraft.questions.forEach((q) => { q.status = "DRAFT"; q.approved_by = null; });
out.runAllDraft = S.runDryRun(allDraft, S.DRY_RUN_SCRIPT).steps.filter((s) => s.kind === "ask").length;

const calm = JSON.parse(JSON.stringify(template));
calm.profile.challenge_intensity = 10;
calm.profile.evidence_strictness = 10;
const calmRun = S.runDryRun(calm, S.DRY_RUN_SCRIPT);
out.calm = { start: calmRun.startPressure, end: calmRun.finalPressure };

out.fairness = S.fairness("cross-sectional").map((p) => ({ id: p.id, breach: p.breach, a: p.triggersA, b: p.triggersB }));
console.log(JSON.stringify(out));
"""


def studio_source() -> str:
    return STUDIO.read_text("utf-8")


def core_script() -> str:
    match = re.search(r'<script id="studio-core">([\s\S]*?)</script>', studio_source())
    if not match:
        raise AssertionError("studio/faculty.html has no <script id=\"studio-core\"> block")
    return match.group(1)


@unittest.skipIf(NODE is None, "node is not installed; studio cross-language check skipped")
class TestStudioAgreesWithTactikEval(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        script = core_script() + f"\nconst VECTORS = {json.dumps(VECTORS)};\n" + HARNESS
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.js"
            path.write_text(script, "utf-8")
            result = subprocess.run([NODE, str(path)], capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise AssertionError(f"studio core failed under node:\n{result.stderr}")
        cls.out = json.loads(result.stdout)

    def node_verify(self, payload: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
            return subprocess.run([NODE, str(VERIFIER), str(path)], capture_output=True, text=True, timeout=30)

    def test_sha256_matches_hashlib(self) -> None:
        expected = [hashlib.sha256(v.encode("utf-8")).hexdigest() for v in VECTORS]
        self.assertEqual(self.out["sha"], expected)

    def test_template_seal_and_blockers_agree(self) -> None:
        template = self.out["template"]
        webscript = load_webscript(template["payload"])
        self.assertEqual(webscript.seal, template["seal"])
        self.assertEqual(
            [list(b) for b in webscript.lock_blockers()],
            [[b["code"], b["detail"]] for b in template["blockers"]],
        )

    def test_template_cannot_be_locked_as_drafted(self) -> None:
        found = {b["code"] for b in self.out["template"]["blockers"]}
        # TACTIK drafted it; faculty have not finished approving it.
        self.assertTrue({"QUESTION_PENDING", "PRESSURE_UNDEFINED", "RUBRIC_PENDING"} <= found)

    def test_completed_script_locks_in_both_languages_with_one_seal(self) -> None:
        complete = self.out["complete"]
        webscript = load_webscript(complete["payload"])
        self.assertEqual(complete["blockers"], [])
        webscript.require_lockable()
        self.assertEqual(webscript.seal, complete["seal"])

    def test_seed_ledger_verifies_in_python_and_in_verify_mjs(self) -> None:
        seed = self.out["seed"]
        self.assertTrue(self.out["seedSelfCheck"])
        self.assertEqual(Ledger.from_payload(seed).head, seed["head"])
        result = self.node_verify(seed)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(seed["head"], result.stdout)

    def test_candidate_text_never_enters_an_entry_body(self) -> None:
        bodies = json.dumps([e["body"] for e in self.out["seed"]["entries"]], ensure_ascii=False)
        for item in self.out["contentRefs"]:
            self.assertNotIn(item["text"], bodies)
            # The reference is the salted digest the spec defines, nothing more.
            from tactik_eval import digest
            self.assertEqual(digest({"salt": item["salt"], "text": item["text"]}), item["ref"])

    def test_erasing_content_leaves_a_verifiable_chain(self) -> None:
        erased = self.out["erased"]
        ledger = Ledger.from_payload(erased["ledger"])
        self.assertEqual(ledger.entries[-1].kind, "content_erased")
        self.assertEqual(ledger.entries[-1].body["content_ref"], erased["ref"])
        self.assertEqual(self.node_verify(erased["ledger"]).returncode, 0)

    def test_an_edited_studio_entry_is_caught_by_both_verifiers(self) -> None:
        payload = json.loads(json.dumps(self.out["seed"]))
        target = next(e for e in payload["entries"] if e["kind"] == "observation_recorded")
        target["body"]["level"] = 3
        self.assertEqual(self.node_verify(payload).returncode, 1)
        with self.assertRaises(Exception):
            Ledger.from_payload(payload)

    def test_studio_refuses_floats_and_withdrawals(self) -> None:
        self.assertTrue(self.out["floatRefused"])
        self.assertTrue(self.out["withdrawalRefused"])

    def test_dry_run_asks_only_approved_questions(self) -> None:
        template = self.out["template"]["payload"]
        approved = {q["qid"] for q in template["questions"] if q["status"] == "APPROVED"}
        self.assertTrue(set(self.out["run"]["asked"]) <= approved)
        self.assertEqual(self.out["runAllDraft"], 0, "a draft question reached the candidate")

    def test_dry_run_declines_to_write_and_preserves_both_versions(self) -> None:
        run = self.out["run"]
        self.assertEqual(run["declined"], 1)
        self.assertEqual(run["preserved"], 2)

    def test_the_teaching_profile_changes_behavior(self) -> None:
        self.assertEqual((self.out["run"]["start"], self.out["run"]["end"]), (2, 3))
        self.assertEqual((self.out["calm"]["start"], self.out["calm"]["end"]), (1, 1))

    def test_fairness_pairs_report_differing_triggers_as_breaches(self) -> None:
        for pair in self.out["fairness"]:
            with self.subTest(pair=pair["id"]):
                self.assertEqual(pair["breach"], sorted(pair["a"]) != sorted(pair["b"]))


class TestStudioKeepsItsBoundaries(unittest.TestCase):
    def test_the_studio_exists(self) -> None:
        self.assertTrue(STUDIO.is_file(), "studio/faculty.html is missing")

    def test_no_network_call_and_no_external_script(self) -> None:
        source = studio_source()
        for forbidden in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "EventSource", "import(", "<script src"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_only_the_font_host_is_contacted(self) -> None:
        hosts = set(re.findall(r"https?://([a-zA-Z0-9.-]+)", studio_source()))
        self.assertLessEqual(hosts, {"fonts.googleapis.com", "fonts.gstatic.com"})

    def test_no_institution_is_named_without_permission(self) -> None:
        source = studio_source().lower()
        for name in ("westcliff", "western state", "harvard", "mit sloan"):
            with self.subTest(name=name):
                self.assertNotIn(name, source)

    def test_no_real_person_is_simulated(self) -> None:
        source = studio_source().lower()
        for marker in ("scalia", "never break character", "behavioral replica", "dna_auth", "tactic_score"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, source)

    def test_the_spec_both_implementations_answer_to_is_present(self) -> None:
        self.assertTrue((REPO_ROOT / "docs" / "WEBSCRIPT.md").is_file())


if __name__ == "__main__":
    unittest.main()
