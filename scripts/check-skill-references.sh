#!/usr/bin/env sh
# Verify intra-skill references inside SKILL.md files actually resolve:
#   - `superpowers:<name>` references must match an existing skill directory.
#   - `./<file>.{md,sh,cjs,js,html,ts}` references must resolve relative to
#     the skill directory.
#   - `references/<file>.md` (or other extensions) must resolve relative to
#     the skill directory.
#   - `skills/<plugin>/<file>` absolute references must resolve from the
#     plugin root.
# Catches silent rot when files are renamed or removed.
set -eu

SKILLS_ROOT="plugins/superpowers-beads/skills"

if [ ! -d "$SKILLS_ROOT" ]; then
  echo "check-skill-references: $SKILLS_ROOT not found" >&2
  exit 1
fi

# Build the set of valid skill names from the directory tree.
valid_skills="$(find "$SKILLS_ROOT" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort -u)"

failed=0
checked=0

# We only validate references that look like file paths. URLs (http(s)://...)
# and code identifiers are ignored.
for skill_md in "$SKILLS_ROOT"/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  checked=$((checked + 1))
  skill_dir="$(dirname "$skill_md")"

  # 1. superpowers:<name> references
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    name="${ref#superpowers:}"
    if ! printf '%s\n' "$valid_skills" | grep -Fxq "$name"; then
      echo "$skill_md: references unknown skill: superpowers:$name" >&2
      failed=$((failed + 1))
    fi
  done <<EOF
$(grep -ohE 'superpowers:[a-z][a-z-]+' "$skill_md" | sort -u)
EOF

  # 2. ./<file>.<ext> relative references — resolve from skill_dir
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    target="$skill_dir/${ref#./}"
    if [ ! -e "$target" ]; then
      echo "$skill_md: references missing relative file: $ref (expected at $target)" >&2
      failed=$((failed + 1))
    fi
  done <<EOF
$(grep -ohE '\./[a-zA-Z0-9._/-]+\.(md|sh|cjs|js|html|ts)' "$skill_md" | sort -u)
EOF

  # 3. references/<file>.<ext> — resolve from skill_dir
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    target="$skill_dir/$ref"
    if [ ! -e "$target" ]; then
      echo "$skill_md: references missing supplementary file: $ref (expected at $target)" >&2
      failed=$((failed + 1))
    fi
  done <<EOF
$(grep -ohE 'references/[a-zA-Z0-9._/-]+\.(md|sh|cjs|js|html|ts)' "$skill_md" | sort -u)
EOF

  # 4. skills/<plugin-or-name>/<file> absolute-from-plugin-root references —
  # resolve from the plugin directory (plugins/superpowers-beads/).
  plugin_root="$(dirname "$SKILLS_ROOT")"
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    target="$plugin_root/$ref"
    if [ ! -e "$target" ]; then
      echo "$skill_md: references missing skills-rooted file: $ref (expected at $target)" >&2
      failed=$((failed + 1))
    fi
  done <<EOF
$(grep -ohE 'skills/[a-zA-Z0-9._/-]+\.(md|sh|cjs|js|html|ts)' "$skill_md" | sort -u)
EOF
done

if [ "$failed" -ne 0 ]; then
  echo "check-skill-references: $failed broken reference(s) across $checked SKILL.md files" >&2
  exit 1
fi

echo "Skill cross-references OK ($checked SKILL.md files)"
