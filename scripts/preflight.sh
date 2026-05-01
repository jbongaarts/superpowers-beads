#!/usr/bin/env sh
set -eu

allowed_in_progress="${ALLOW_IN_PROGRESS:-}"

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
run scripts/test-run-activation-matrix-codex.sh
run git diff --check
run bd orphans
run bd stale

printf '\n==> bd list --status=in_progress\n'
in_progress_json="$(bd list --status=in_progress --json)"
in_progress_count="$(printf '%s' "$in_progress_json" | jq 'length')"

if [ "$in_progress_count" -eq 0 ]; then
  echo "No in-progress issues found."
elif [ -n "$allowed_in_progress" ]; then
  # ALLOW_IN_PROGRESS is comma-separated; every in-progress bead must be on
  # the allowlist or this gate fails.
  unexpected="$(printf '%s' "$in_progress_json" \
    | jq -r --arg allow "$allowed_in_progress" '
        ($allow | split(",") | map(. | gsub("^[[:space:]]+|[[:space:]]+$"; ""))) as $allowlist
        | .[] | select(.id as $id | $allowlist | index($id) | not) | .id
      ')"
  if [ -z "$unexpected" ]; then
    echo "All in-progress beads are on the allowlist: $allowed_in_progress"
  else
    echo "Unexpected in-progress issues (not on ALLOW_IN_PROGRESS allowlist):" >&2
    printf '%s\n' "$unexpected" | while read -r id; do
      bd show "$id" 2>/dev/null | head -1 >&2
    done
    exit 1
  fi
else
  echo "Unexpected in-progress issues:" >&2
  bd list --status=in_progress >&2
  exit 1
fi

echo
echo "Plugin preflight passed."
