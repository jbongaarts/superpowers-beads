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
run git diff --check
run bd orphans
run bd stale

printf '\n==> bd list --status=in_progress\n'
in_progress_json="$(bd list --status=in_progress --json)"
in_progress_count="$(printf '%s' "$in_progress_json" | jq 'length')"

if [ "$in_progress_count" -eq 0 ]; then
  echo "No in-progress issues found."
elif [ -n "$allowed_in_progress" ] &&
  [ "$in_progress_count" -eq 1 ] &&
  printf '%s' "$in_progress_json" | jq -e --arg id "$allowed_in_progress" 'any(.[]; .id == $id)' >/dev/null; then
  echo "Only allowed in-progress issue found: $allowed_in_progress"
else
  echo "Unexpected in-progress issues:" >&2
  bd list --status=in_progress >&2
  exit 1
fi

echo
echo "Plugin preflight passed."
