#!/usr/bin/env sh
# Verify that every plugins/*/skills/*/SKILL.md has YAML frontmatter with a
# non-empty `name` and `description`. Exit non-zero with a list of offenders.
set -eu

failed=0
checked=0

for skill in plugins/*/skills/*/SKILL.md; do
  [ -f "$skill" ] || continue
  checked=$((checked + 1))

  awk -v file="$skill" '
    BEGIN { state = "before"; have_name = 0; have_desc = 0 }
    NR == 1 {
      if ($0 != "---") {
        printf "%s: missing YAML frontmatter (file does not start with ---)\n", file > "/dev/stderr"
        exit 2
      }
      state = "in"
      next
    }
    state == "in" && $0 == "---" { state = "after"; exit 0 }
    state == "in" {
      # Match `name:` / `description:` with at least one non-space char of value.
      if ($0 ~ /^name:[[:space:]]*[^[:space:]]/) have_name = 1
      if ($0 ~ /^description:[[:space:]]*[^[:space:]]/) have_desc = 1
    }
    END {
      if (state != "after") {
        printf "%s: unterminated YAML frontmatter\n", file > "/dev/stderr"
        exit 2
      }
      if (!have_name) {
        printf "%s: missing or empty `name:` in frontmatter\n", file > "/dev/stderr"
        exit 2
      }
      if (!have_desc) {
        printf "%s: missing or empty `description:` in frontmatter\n", file > "/dev/stderr"
        exit 2
      }
    }
  ' "$skill" || failed=$((failed + 1))
done

if [ "$checked" -eq 0 ]; then
  echo "skill-frontmatter: no SKILL.md files found under plugins/*/skills/*/" >&2
  exit 1
fi

if [ "$failed" -ne 0 ]; then
  echo "skill-frontmatter: $failed of $checked SKILL.md files failed" >&2
  exit 1
fi

echo "Frontmatter OK ($checked SKILL.md files)"
