"""The two implementations of the hash recipe must agree, and must both refuse.

Doctrine P11: two implementations that agree are evidence. One implementation
called twice is not. This suite is what keeps that claim true as the code moves,
and it is the reason a change to canonical.py cannot land quietly.

Skipped, loudly, when Node is unavailable — never passed by default. A green
run that silently checked nothing is the blank field of P09 in test form.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tactik_eval import Ledger

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIER = REPO_ROOT / "verify" / "verify.mjs"
NODE = shutil.which("node")


def build_ledger() -> Ledger:
    """A record exercising every shape the canonical form has to handle."""
    ledger = Ledger()
    ledger.append(
        "pack_sealed",
        {
            "pack_id": "pack-2026-07",
            "case_count": 3,
            "sealed_by": "S. Maspons",
            "nested": {"b": [1, 2, 3], "a": {"deep": True}},
            "unicode": "señor · café — ✓",
            "quoting": 'he said "no" \\ then left\nnewline',
            "empty_object": {},
            "empty_array": [],
            "null_value": None,
            "negative": -17,
            "decimal_as_string": "4.20",
        },
    )
    ledger.append("run_voided", {"run_id": "run-001", "result": "NO_SCORE"})
    ledger.append("aggregate_published", {"run_id": "run-002", "claimed": 74})
    ledger.withdraw(2, reason="uncalibrated bands", withdrawn_by="S. Maspons")
    ledger.append("note", {"statement": "no aggregate published for run-002"})
    return ledger


@unittest.skipIf(NODE is None, "node is not installed; cross-language check skipped")
class TestCrossLanguageAgreement(unittest.TestCase):
    def run_node_verifier(self, path: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [NODE, str(VERIFIER), str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def write(self, directory: str, name: str, payload: dict) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), "utf-8")
        return path

    def test_both_implementations_accept_an_intact_ledger(self) -> None:
        ledger = build_ledger()
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "ledger.json", ledger.to_payload())

            result = self.run_node_verifier(path)
            self.assertEqual(result.returncode, 0, result.stderr)

            # And the hash the other language computed is the one we published.
            self.assertIn(ledger.head, result.stdout)

    def test_both_implementations_reject_an_edited_body(self) -> None:
        ledger = build_ledger()
        payload = ledger.to_payload()
        payload["entries"][2]["body"]["claimed"] = 95

        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "tampered.json", payload)

            result = self.run_node_verifier(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("link mismatch", result.stderr)

            with self.assertRaises(Exception):
                Ledger.from_payload(payload)

    def test_both_implementations_reject_a_removed_entry(self) -> None:
        """Deleting an inconvenient line is the failure P10 exists to prevent."""
        ledger = build_ledger()
        payload = ledger.to_payload()
        del payload["entries"][2]
        for position, entry in enumerate(payload["entries"]):
            entry["index"] = position

        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "shortened.json", payload)

            result = self.run_node_verifier(path)
            self.assertEqual(result.returncode, 1)

            with self.assertRaises(Exception):
                Ledger.from_payload(payload)

    def test_unicode_and_escaping_hash_identically(self) -> None:
        """The escaping edge cases, isolated from the rest of the record."""
        ledger = Ledger()
        for text in (
            "señor",
            "café — ✓",
            'quote " backslash \\ ',
            "tab\there",
            "newline\nhere",
            "日本語",
            "emoji 🜛 and combining é",
        ):
            ledger.append("note", {"text": text})

        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "unicode.json", ledger.to_payload())
            result = self.run_node_verifier(path)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(ledger.head, result.stdout)


class TestVerifierIsPresent(unittest.TestCase):
    """P11 is a claim about artifacts, so the artifact has to exist."""

    def test_second_implementation_is_in_the_repository(self) -> None:
        self.assertTrue(
            VERIFIER.is_file(),
            "the second implementation of the hash recipe is missing; "
            "P11 is not satisfied by one implementation",
        )

    def test_hash_recipe_prose_is_in_the_repository(self) -> None:
        recipe = REPO_ROOT / "docs" / "HASHING.md"
        self.assertTrue(
            recipe.is_file(),
            "both implementations are answerable to docs/HASHING.md, "
            "which is missing",
        )


if __name__ == "__main__":
    unittest.main()
