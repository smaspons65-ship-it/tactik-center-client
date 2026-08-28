"""The skills ship in two places, and must not drift apart.

`.claude/skills/` loads automatically for anyone working in this repository.
`skills/` is what the installable plugin serves. They are the same skills, so
a change to one without the other would mean two people running "the same"
audit against different rules — which is the failure the doctrine is about.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_SKILLS = REPO_ROOT / ".claude" / "skills"
PLUGIN_SKILLS = REPO_ROOT / "skills"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"

EXPECTED_SKILLS = {"doctrine-review", "sealed-run", "santiago"}


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML frontmatter reader: `key: value` pairs between --- fences."""
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must open with a --- frontmatter fence")
    _, block, _ = text.split("---\n", 2)
    fields: dict[str, str] = {}
    key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and key:
            fields[key] += " " + line.strip()
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        fields[key] = value.strip()
    return fields


class TestSkillsDoNotDrift(unittest.TestCase):
    def test_both_locations_hold_the_same_skills(self) -> None:
        project = {p.name for p in PROJECT_SKILLS.iterdir() if p.is_dir()}
        plugin = {p.name for p in PLUGIN_SKILLS.iterdir() if p.is_dir()}
        self.assertEqual(project, EXPECTED_SKILLS)
        self.assertEqual(plugin, EXPECTED_SKILLS)

    def test_each_skill_is_byte_identical_in_both_locations(self) -> None:
        for name in EXPECTED_SKILLS:
            with self.subTest(skill=name):
                a = (PROJECT_SKILLS / name / "SKILL.md").read_bytes()
                b = (PLUGIN_SKILLS / name / "SKILL.md").read_bytes()
                self.assertEqual(
                    a,
                    b,
                    f"{name} differs between .claude/skills/ and skills/; "
                    "copy one over the other",
                )


class TestSkillFrontmatter(unittest.TestCase):
    def test_every_skill_declares_a_description(self) -> None:
        for name in EXPECTED_SKILLS:
            with self.subTest(skill=name):
                fields = parse_frontmatter(
                    (PROJECT_SKILLS / name / "SKILL.md").read_text("utf-8")
                )
                self.assertIn(
                    "description",
                    fields,
                    "description is required; it is what decides when the "
                    "skill triggers",
                )
                self.assertGreater(
                    len(fields["description"]),
                    80,
                    "a thin description triggers unreliably; say when to use it",
                )

    def test_declared_name_matches_its_directory(self) -> None:
        for name in EXPECTED_SKILLS:
            with self.subTest(skill=name):
                fields = parse_frontmatter(
                    (PROJECT_SKILLS / name / "SKILL.md").read_text("utf-8")
                )
                if "name" in fields:
                    self.assertEqual(fields["name"], name)


class TestPluginManifest(unittest.TestCase):
    def test_manifest_is_valid_json_with_required_keys(self) -> None:
        manifest = json.loads(PLUGIN_MANIFEST.read_text("utf-8"))
        self.assertIn("name", manifest)
        self.assertIn("description", manifest)
        self.assertEqual(manifest["name"], "santiago-doctrine")

    def test_marketplace_lists_this_plugin(self) -> None:
        marketplace = json.loads(MARKETPLACE.read_text("utf-8"))
        manifest = json.loads(PLUGIN_MANIFEST.read_text("utf-8"))
        names = {entry["name"] for entry in marketplace["plugins"]}
        self.assertIn(manifest["name"], names)

    def test_marketplace_version_tracks_the_manifest(self) -> None:
        marketplace = json.loads(MARKETPLACE.read_text("utf-8"))
        manifest = json.loads(PLUGIN_MANIFEST.read_text("utf-8"))
        entry = next(
            e for e in marketplace["plugins"] if e["name"] == manifest["name"]
        )
        self.assertEqual(entry["version"], manifest["version"])

    def test_plugin_subdirectories_are_not_inside_the_manifest_directory(self) -> None:
        """skills/ belongs at the plugin root, never under .claude-plugin/."""
        stray = PLUGIN_MANIFEST.parent / "skills"
        self.assertFalse(stray.exists(), "skills/ must not live in .claude-plugin/")


if __name__ == "__main__":
    unittest.main()
