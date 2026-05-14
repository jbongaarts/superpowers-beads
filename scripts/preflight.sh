#!/usr/bin/env sh
set -eu

if ! command -v jq >/dev/null 2>&1; then
  echo "preflight: jq is required but was not found on PATH" >&2
  exit 1
fi

run() {
  printf '\n==> %s\n' "$*"
  "$@"
}

run claude plugin validate .
run test -f .agents/skills/using-superpowers/SKILL.md
run jq empty plugins/superpowers-beads/.codex-plugin/plugin.json
run jq empty .agents/plugins/marketplace.json
run scripts/check-version-sync.sh
run scripts/check-codex-manifests.sh
run scripts/check-skill-frontmatter.sh
run scripts/check-skill-references.sh
run scripts/check-bd-api.sh
run scripts/test-check-in-progress-beads.sh
run sh -c "cd scripts/ab-test && python3 -m unittest discover tests -q"
run scripts/test-run-activation-matrix-codex.sh
run git diff --check
run bd orphans
run bd stale
run scripts/check-in-progress-beads.sh

echo
echo "Plugin preflight passed."
