import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from build_plugin import build_variant_plugin


class BuildVariantPluginTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ab-test-bvp-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_writes_plugin_manifest_with_expected_name(self):
        dest = self.tmp / "variant-current"
        path = build_variant_plugin(
            description="Use when starting any conversation",
            dest=dest,
            plugin_name="superpowers-beads",
        )
        self.assertEqual(Path(path), dest)
        manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "superpowers-beads")

    def test_writes_skill_md_with_description_in_frontmatter(self):
        dest = self.tmp / "variant-a"
        description = "First prompt in a top-level agent session"
        build_variant_plugin(description=description, dest=dest)
        skill_md = (dest / "skills" / "using-superpowers" / "SKILL.md").read_text()

        self.assertTrue(skill_md.startswith("---\n"))
        body_start = skill_md.index("\n---\n", 4)
        frontmatter = yaml.safe_load(skill_md[4:body_start])
        self.assertEqual(frontmatter["name"], "using-superpowers")
        self.assertEqual(frontmatter["description"], description)

    def test_descriptions_with_special_characters_are_safely_quoted(self):
        dest = self.tmp / "variant-b"
        description = (
            'Tricky: with "double quotes", colon: yes, and a newline\\nstaying inline'
        )
        build_variant_plugin(description=description, dest=dest)
        skill_md = (dest / "skills" / "using-superpowers" / "SKILL.md").read_text()
        body_start = skill_md.index("\n---\n", 4)
        frontmatter = yaml.safe_load(skill_md[4:body_start])
        self.assertEqual(frontmatter["description"], description)

    def test_creates_dest_if_missing(self):
        dest = self.tmp / "nested" / "deeper" / "variant-c"
        build_variant_plugin(description="x", dest=dest)
        self.assertTrue((dest / ".claude-plugin" / "plugin.json").exists())
        self.assertTrue((dest / "skills" / "using-superpowers" / "SKILL.md").exists())

    def test_custom_plugin_name_propagates(self):
        dest = self.tmp / "variant-named"
        build_variant_plugin(
            description="hi", dest=dest, plugin_name="custom-thing"
        )
        manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "custom-thing")

    def test_writes_codex_repo_skill_tree(self):
        dest = self.tmp / "variant-codex"
        description = "Codex candidate description"
        build_variant_plugin(description=description, dest=dest)

        skill_md = (
            dest / ".agents" / "skills" / "using-superpowers" / "SKILL.md"
        ).read_text()
        self.assertTrue(skill_md.startswith("---\n"))
        body_start = skill_md.index("\n---\n", 4)
        frontmatter = yaml.safe_load(skill_md[4:body_start])
        self.assertEqual(frontmatter["name"], "using-superpowers")
        self.assertEqual(frontmatter["description"], description)


if __name__ == "__main__":
    unittest.main()
