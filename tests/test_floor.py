"""The standing floor ships in one place and is extracted, never copied.

`CLAUDE.md` loads automatically for anyone working in this repository.
`instalar/instalar.sh` installs the same floor at user level so it applies
outside the repo too — and it does that by *extracting* the section from
CLAUDE.md at install time rather than carrying its own copy. A second copy
would be a second set of rules the moment someone edited one of them, which
is the drift `test_skills.py` exists to prevent for skills.

That extraction keys on an exact heading. These tests fail loudly if the
heading moves, rather than letting the installer quietly write an empty block.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
INSTALLER = REPO_ROOT / "instalar" / "instalar.sh"

HEADING = "## The standing floor"


def extract_floor(text: str) -> str:
    """The awk in instalar.sh, in Python: the heading, then up to the next `## `."""
    match = re.search(
        rf"^{re.escape(HEADING)}$\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1).strip() if match else ""


class TestStandingFloor(unittest.TestCase):
    def test_claude_md_exists(self) -> None:
        self.assertTrue(
            CLAUDE_MD.is_file(),
            "CLAUDE.md is the always-on half of the doctrine; without it the "
            "floor only applies when a skill happens to trigger",
        )

    def test_the_heading_the_installer_keys_on_is_present(self) -> None:
        self.assertIn(
            HEADING,
            CLAUDE_MD.read_text("utf-8"),
            f"instalar/instalar.sh extracts on {HEADING!r}; renaming it makes "
            "the installer write an empty floor without complaining",
        )

    def test_extraction_yields_every_rule(self) -> None:
        floor = extract_floor(CLAUDE_MD.read_text("utf-8"))
        self.assertTrue(floor, "extraction returned nothing")
        for n in range(1, 6):
            with self.subTest(rule=n):
                self.assertIn(f"{n}. **", floor, f"rule {n} missing from the floor")


class TestInstaller(unittest.TestCase):
    def test_installer_is_present_and_executable(self) -> None:
        self.assertTrue(INSTALLER.is_file(), "instalar/instalar.sh is missing")
        self.assertTrue(
            os.access(INSTALLER, os.X_OK), "instalar/instalar.sh is not executable"
        )

    def _run(self, config_dir: Path) -> str:
        subprocess.run(
            ["bash", str(INSTALLER)],
            cwd=REPO_ROOT,
            env={**os.environ, "CLAUDE_CONFIG_DIR": str(config_dir)},
            check=True,
            capture_output=True,
        )
        return (config_dir / "CLAUDE.md").read_text("utf-8")

    def test_it_installs_the_floor_into_a_fresh_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            written = self._run(Path(tmp))
            self.assertIn(HEADING, written)
            self.assertIn("santiago-floor:inicio", written)

    def test_it_preserves_what_the_user_already_had(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "CLAUDE.md"
            target.write_text("# My notes\n\nAlways use pnpm.\n", encoding="utf-8")
            written = self._run(Path(tmp))
            self.assertIn("Always use pnpm.", written)
            self.assertIn(HEADING, written)

    def test_running_it_twice_does_not_duplicate_the_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._run(Path(tmp))
            once = (Path(tmp) / "CLAUDE.md").read_text("utf-8")
            twice = self._run(Path(tmp))
            self.assertEqual(once, twice, "a second run changed the file")
            self.assertEqual(twice.count("santiago-floor:inicio"), 1)


if __name__ == "__main__":
    unittest.main()
