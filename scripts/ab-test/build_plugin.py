"""Build a temporary plugin tree mirroring the superpowers-beads layout, with
the variant frontmatter description applied to using-superpowers/SKILL.md.

Plugin name defaults to "superpowers-beads" so the namespaced skill ref the
model sees (superpowers-beads:using-superpowers) matches what users see in
production. Each cell loads exactly one variant via --plugin-dir, so per-cell
plugin name reuse is safe."""

import json
from pathlib import Path
from typing import Union

import yaml


DEFAULT_PLUGIN_NAME = "superpowers-beads"
DEFAULT_SKILL_NAME = "using-superpowers"

_BODY_STUB = (
    "Activation-test stub.\n\n"
    "This plugin is built by scripts/ab-test/ to measure how often a fresh\n"
    "session invokes Skill(using-superpowers) on its first turn given only the\n"
    "frontmatter description above. The body is intentionally minimal — body\n"
    "content does not influence first-tool-call selection.\n"
)


def build_variant_plugin(
    description: str,
    dest: Union[str, Path],
    plugin_name: str = DEFAULT_PLUGIN_NAME,
    skill_name: str = DEFAULT_SKILL_NAME,
) -> Path:
    dest = Path(dest)
    (dest / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (dest / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": plugin_name,
                "description": "ab-test variant",
                "version": "0.0.0",
            },
            indent=2,
        )
        + "\n"
    )

    skill_dir = dest / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(
        {"name": skill_name, "description": description},
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=10**9,
    )
    skill_md = f"---\n{frontmatter}---\n\n{_BODY_STUB}"
    (skill_dir / "SKILL.md").write_text(skill_md)
    return dest
