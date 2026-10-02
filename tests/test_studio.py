"""The Faculty Studio's JavaScript and tactik_eval's Python must agree, and the
studio must keep the promises the proposal makes about it.

Two implementations answer to docs/WEBSCRIPT.md and docs/HASHING.md: the core
script inside studio/faculty.html, and tactik_eval. This suite runs the studio's
own core under Node and checks its seals, blockers, engine and ledgers with
Python and with verify/verify.mjs. Skipped, loudly, when Node is unavailable.

The engine's central promise is tested hardest: every line a candidate sees is
an approved question, an approved rule prompt, or a fixed system line, whatever
the classifier returns. A classifier that tries to write for the candidate, or
labels every turn as a challenge, cannot change that or keep a session going
forever.

The static checks need no Node. They hold the page to claims about a file: no
network call other than the font stylesheet, no AI path other than the opt-in
`sample` capability, no institution's name, no simulated person.
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

from tactik_eval import Ledger, digest
from tactik_eval.edu import load_webscript

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDIO = REPO_ROOT / "studio" / "faculty.html"
VERIFIER = REPO_ROOT / "verify" / "verify.mjs"
NODE = shutil.which("node")

VECTORS = ["", "abc", "señor · café — ✓", "a" * 1000, "日本語 🜛", "quote \" backslash \\ tab\t"]

HARNESS = r"""
const S = globalThis.StudioCore;
const out = { sha: VECTORS.map(S.sha256Hex), packs: {} };

function allowedTexts(ws) {
  return new Set([
    ...ws.questions.filter((q) => q.status === "APPROVED").map((q) => q.text),
    ...ws.event_rules.map((r) => r.prompt),
    ...S.systemLines(ws),
  ]);
}
function spoken(s) { return s.transcript.filter((t) => t.role === "lens" || t.role === "system").map((t) => t.text); }
function asLedger(effects) { const l = { entries: [] }; effects.forEach((e) => S.appendEntry(l, e.kind, e.body)); return S.ledgerPayload(l); }

const seeded = S.seedState("Faculty owner (fictional)");
for (const pack of S.PACKS) {
  const draft = S.buildScript(pack.spec);
  const locked = seeded.scripts[pack.spec.id];
  const ws = locked.webscript;
  const sim = S.engineSimulate(ws, pack.dryRun);
  const allowed = allowedTexts(ws);
  const said = spoken(sim.session);

  // A hostile classifier: invented labels, its own prose, every event at once.
  const hostile = S.engineStart(ws, { session: "H", candidate: "R-99", seal: locked.locked.seal, classifier: "claude", at: null });
  const store = {};
  const raw = { events: ["grade_student", "write_answer", "unsupported_claim", "causal_language", "projection_without_basis", "conclusory_answer"], text: "HERE IS THE ANSWER YOU SHOULD GIVE", answer: "A model answer." };
  const sanitized = S.sanitizeClassification(ws, raw);
  let turns = 0;
  const hostileEffects = hostile.effects.slice();
  while (hostile.session.status === "running" && turns < 200) {
    hostileEffects.push(...S.engineAnswer(ws, hostile.session, `turn ${turns}`, sanitized, store, null));
    turns += 1;
  }

  out.packs[pack.id] = {
    draft: { payload: draft, seal: S.digest(draft), blockers: S.lockBlockers(draft) },
    locked: { payload: ws, seal: S.digest(ws), recorded: locked.locked.seal, blockers: S.lockBlockers(ws) },
    sim: {
      status: sim.session.status, turns: sim.session.turns, preserved: sim.session.preserved.length, open: sim.session.openObjections.length,
      declined: sim.session.transcript.filter((t) => t.event === "answer_request").length,
      asked: sim.session.transcript.filter((t) => t.qid).map((t) => t.qid),
      outside: said.filter((t) => !allowed.has(t)),
      ledger: asLedger(sim.effects),
      start: S.startingPressure(ws.profile), end: sim.session.pressure,
      debrief: S.debriefOf(ws, sim.session, sim.store),
    },
    hostile: { sanitized, turns, status: hostile.session.status, outside: spoken(hostile.session).filter((t) => !allowed.has(t)), ledger: asLedger(hostileEffects) },
    allowedEvents: S.allowedEvents(ws),
  };
}

const dba = seeded.scripts["dba-defense-readiness"].webscript;
const allDraft = S.clone(dba);
allDraft.questions.forEach((q) => { q.status = "DRAFT"; q.approved_by = null; });
out.allDraftAsked = S.engineSimulate(allDraft, S.PACKS[0].dryRun).session.transcript.filter((t) => t.qid).length;

const calm = S.clone(dba);
calm.profile.challenge_intensity = 10;
calm.profile.evidence_strictness = 10;
const calmRun = S.engineSimulate(calm, S.PACKS[0].dryRun).session;
out.calm = { start: S.startingPressure(calm.profile), end: calmRun.pressure };

const stopped = S.engineStart(dba, { session: "L-01", candidate: "R-01", seal: "x", classifier: "rules", at: null });
const stopEffects = S.engineStop(dba, stopped.session, "R-01", "participant_requests_stop", null);
out.stop = stopEffects[0];
let answerAfterStop = null;
try { S.engineAnswer(dba, stopped.session, "late answer", { events: [], source: "rules" }, {}, null); } catch (err) { answerAfterStop = err.message; }
out.answerAfterStop = answerAfterStop;

out.seed = S.ledgerPayload(seeded.ledger);
out.contentRefs = Object.entries(seeded.content).map(([ref, v]) => ({ ref, salt: v.salt, text: v.text }));
const firstRef = Object.keys(seeded.content)[0];
delete seeded.content[firstRef];
S.appendEntry(seeded.ledger, "content_erased", { content_ref: firstRef, reason: "test", by: "Faculty owner (fictional)" });
out.erased = { ledger: S.ledgerPayload(seeded.ledger), ref: firstRef };

const parsed = S.parseSyllabus(S.SAMPLE_SYLLABUS);
const syllabus = S.syllabusFrom(parsed, "test");
const imported = S.draftFromSyllabus(syllabus, "socratic", ["x"]);
const drafted = S.applyDraftedQuestions(S.clone(imported), syllabus, { questions: [
  { state: "issue_rule", pressure: 1, outcomes: ["CLO1", "CLO9"], text: "Which rule governs your evaluation design, and why?" },
  { state: "nowhere", pressure: 1, text: "dropped: unknown state" },
  { state: "application", pressure: 7, text: "dropped: pressure out of range" },
  { state: "application", pressure: 1.5, text: "dropped: float pressure" },
  { state: "inversion", pressure: 2, text: "x".repeat(500) },
] });
out.syllabus = { parsed, imported: { payload: imported, seal: S.digest(imported), blockers: S.lockBlockers(imported) },
  drafted: { payload: drafted, seal: S.digest(drafted), blockers: S.lockBlockers(drafted) } };

let floatRefused = false;
try { S.digest({ weight: 0.15 }); } catch (err) { floatRefused = true; }
let withdrawalRefused = false;
try { S.appendEntry({ entries: [] }, "withdrawal", {}); } catch (err) { withdrawalRefused = true; }
out.refusals = { floatRefused, withdrawalRefused };
out.garbage = [null, {}, [], { entries: { 0: {} } }, { entries: [] }].map((g) => S.verifyLedgerPayload(g).ok);
out.fairness = S.fairness().map((p) => ({ id: p.id, breach: p.breach, a: p.triggersA, b: p.triggersB }));
console.log(JSON.stringify(out));
"""


def studio_source() -> str:
    return STUDIO.read_text("utf-8")


def core_script() -> str:
    match = re.search(r'<script id="studio-core">([\s\S]*?)</script>', studio_source())
    if not match:
        raise AssertionError('studio/faculty.html has no <script id="studio-core"> block')
    return match.group(1)


@unittest.skipIf(NODE is None, "node is not installed; studio cross-language check skipped")
class TestStudioAgreesWithTactikEval(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        script = core_script() + f"\nconst VECTORS = {json.dumps(VECTORS)};\n" + HARNESS
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.js"
            path.write_text(script, "utf-8")
            result = subprocess.run([NODE, str(path)], capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise AssertionError(f"studio core failed under node:\n{result.stderr}")
        cls.out = json.loads(result.stdout)

    def node_verify(self, payload: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), "utf-8")
            return subprocess.run([NODE, str(VERIFIER), str(path)], capture_output=True, text=True, timeout=30)

    def assert_parity(self, item: dict) -> None:
        webscript = load_webscript(item["payload"])
        self.assertEqual(webscript.seal, item["seal"])
        self.assertEqual(
            [list(b) for b in webscript.lock_blockers()],
            [[b["code"], b["detail"]] for b in item["blockers"]],
        )

    def test_sha256_matches_hashlib(self) -> None:
        self.assertEqual(self.out["sha"], [hashlib.sha256(v.encode("utf-8")).hexdigest() for v in VECTORS])

    def test_every_pack_agrees_with_python_as_drafted_and_as_locked(self) -> None:
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name, stage="draft"):
                self.assert_parity(pack["draft"])
                found = {b["code"] for b in pack["draft"]["blockers"]}
                self.assertTrue({"QUESTION_PENDING", "PRESSURE_UNDEFINED", "RUBRIC_PENDING"} <= found)
            with self.subTest(pack=name, stage="locked"):
                self.assert_parity(pack["locked"])
                self.assertEqual(pack["locked"]["blockers"], [])
                self.assertEqual(pack["locked"]["recorded"], pack["locked"]["seal"])
                load_webscript(pack["locked"]["payload"]).require_lockable()

    def test_the_engine_runs_every_pack_to_a_debrief(self) -> None:
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name):
                sim = pack["sim"]
                self.assertEqual(sim["status"], "completed")
                self.assertEqual(sim["declined"], 1, "the request to write an answer was not declined")
                self.assertEqual(sim["preserved"], 2, "both versions of revised claims were not kept")
                self.assertEqual(sim["open"], 1)
                self.assertGreater(sim["end"], sim["start"], "a confident unsupported claim did not raise pressure")
                self.assertTrue(sim["debrief"]["actions"])
                self.assertNotIn("grade", json.dumps(sim["debrief"]).lower().replace("no grade", ""))

    def test_a_candidate_sees_only_approved_wording(self) -> None:
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name, run="scripted"):
                self.assertEqual(pack["sim"]["outside"], [])
            with self.subTest(pack=name, run="hostile classifier"):
                self.assertEqual(pack["hostile"]["outside"], [])

    def test_a_hostile_classifier_is_reduced_to_this_scripts_events(self) -> None:
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name):
                sanitized = pack["hostile"]["sanitized"]
                self.assertTrue(set(sanitized["events"]) <= set(pack["allowedEvents"]))
                self.assertNotIn("grade_student", sanitized["events"])
                self.assertNotIn("write_answer", sanitized["events"])
                self.assertIn("Discarded", sanitized["note"])
                self.assertEqual(set(sanitized), {"events", "source", "note"}, "classifier prose leaked through")

    def test_a_session_cannot_wander(self) -> None:
        """Three challenged turns per round, then the engine moves on."""
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name):
                self.assertEqual(pack["hostile"]["status"], "completed")
                self.assertLess(pack["hostile"]["turns"], 30)

    def test_engine_ledgers_verify_in_python_and_in_verify_mjs(self) -> None:
        for name, pack in self.out["packs"].items():
            for run in ("sim", "hostile"):
                with self.subTest(pack=name, run=run):
                    payload = pack[run]["ledger"]
                    self.assertEqual(Ledger.from_payload(payload).head, payload["head"])
                    self.assertEqual(self.node_verify(payload).returncode, 0)

    def test_only_approved_questions_are_asked(self) -> None:
        for name, pack in self.out["packs"].items():
            with self.subTest(pack=name):
                approved = {q["qid"] for q in pack["locked"]["payload"]["questions"] if q["status"] == "APPROVED"}
                self.assertTrue(set(pack["sim"]["asked"]) <= approved)
        self.assertEqual(self.out["allDraftAsked"], 0, "a draft question reached the candidate")

    def test_the_teaching_profile_changes_behavior(self) -> None:
        self.assertEqual((self.out["calm"]["start"], self.out["calm"]["end"]), (1, 1))
        dba = self.out["packs"]["dba"]["sim"]
        self.assertEqual((dba["start"], dba["end"]), (2, 3))

    def test_a_stopped_session_is_no_score_and_takes_no_more_answers(self) -> None:
        self.assertEqual(self.out["stop"]["kind"], "session_stopped")
        self.assertEqual(self.out["stop"]["body"]["result"], "NO_SCORE")
        self.assertIn("stopped", self.out["answerAfterStop"])

    def test_seed_ledger_verifies_in_python_and_in_verify_mjs(self) -> None:
        seed = self.out["seed"]
        self.assertEqual(Ledger.from_payload(seed).head, seed["head"])
        result = self.node_verify(seed)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(seed["head"], result.stdout)

    def test_candidate_text_never_enters_an_entry_body(self) -> None:
        bodies = json.dumps([e["body"] for e in self.out["seed"]["entries"]], ensure_ascii=False)
        for item in self.out["contentRefs"]:
            self.assertNotIn(item["text"], bodies)
            self.assertEqual(digest({"salt": item["salt"], "text": item["text"]}), item["ref"])
        for name, pack in self.out["packs"].items():
            turns = [e for e in pack["sim"]["ledger"]["entries"] if e["kind"] == "turn_recorded"]
            with self.subTest(pack=name):
                self.assertTrue(turns)
                for entry in turns:
                    self.assertEqual(set(entry["body"]) & {"text", "turn_text"}, set())

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

    def test_syllabus_import_reads_outcomes_weeks_and_weights_without_floats(self) -> None:
        parsed = self.out["syllabus"]["parsed"]
        self.assertEqual(parsed["code"], "EDD 740")
        self.assertEqual([o["id"] for o in parsed["outcomes"]], ["CLO1", "CLO2", "CLO3", "CLO4"])
        self.assertEqual(len(parsed["modules"]), 6)
        self.assertEqual([a["weight_bp"] for a in parsed["assessments"]], [2500, 2000, 1750, 3750])
        self.assertEqual(parsed["warnings"], [])

    def test_an_imported_draft_agrees_with_python_and_cannot_lock(self) -> None:
        for stage in ("imported", "drafted"):
            with self.subTest(stage=stage):
                item = self.out["syllabus"][stage]
                self.assert_parity(item)
                found = {b["code"] for b in item["blockers"]}
                self.assertTrue({"OBJECTIVE_INCOMPLETE", "DOSSIER_EMPTY", "QUESTION_PENDING"} <= found)

    def test_drafted_questions_are_filtered_and_stay_drafts(self) -> None:
        questions = self.out["syllabus"]["drafted"]["payload"]["questions"]
        claude = [q for q in questions if q["state"] == "issue_rule"]
        self.assertEqual([q["text"] for q in claude], ["Which rule governs your evaluation design, and why?"])
        self.assertEqual(claude[0]["outcomes"], ["CLO1"], "an outcome the syllabus does not have survived")
        self.assertTrue(all(q["status"] == "DRAFT" and q["approved_by"] is None for q in questions))
        self.assertTrue(all(len(q["text"]) <= 400 for q in questions))
        imported = self.out["syllabus"]["imported"]["payload"]["questions"]
        rounds = {q["state"] for q in imported}
        self.assertEqual({q["state"] for q in questions}, rounds, "a round lost all its questions")

    def test_studio_refuses_floats_withdrawals_and_garbage_ledgers(self) -> None:
        self.assertTrue(self.out["refusals"]["floatRefused"])
        self.assertTrue(self.out["refusals"]["withdrawalRefused"])
        self.assertEqual(self.out["garbage"], [False, False, False, False, False])

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

    def test_the_only_ai_path_is_the_opt_in_sample_capability(self) -> None:
        uses = re.findall(r"claude\.use\(\s*\"([a-z]+)\"\s*\)", studio_source())
        self.assertEqual(uses, ["sample"])

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
