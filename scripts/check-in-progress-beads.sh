#!/usr/bin/env sh
set -eu

allowed_in_progress="${ALLOW_IN_PROGRESS:-}"

current_json="$(bd show --current --json 2>/dev/null || true)"
current_in_progress="$(
  printf '%s' "$current_json" \
    | jq -r '[.[]? | select(.status == "in_progress") | .id] | join(",")'
)"

if [ -n "$current_in_progress" ]; then
  if [ -n "$allowed_in_progress" ]; then
    allowed_in_progress="$current_in_progress,$allowed_in_progress"
  else
    allowed_in_progress="$current_in_progress"
  fi
fi

printf '\n==> bd list --status=in_progress\n'
in_progress_json="$(bd list --status=in_progress --json)"
in_progress_count="$(printf '%s' "$in_progress_json" | jq 'length')"

if [ "$in_progress_count" -eq 0 ]; then
  echo "No in-progress issues found."
elif [ -n "$allowed_in_progress" ]; then
  # ALLOW_IN_PROGRESS is comma-separated; every in-progress bead must be on
  # the allowlist or be the current claimed bead, or this gate fails.
  unexpected="$(printf '%s' "$in_progress_json" \
    | jq -r --arg allow "$allowed_in_progress" '
        ($allow | split(",") | map(. | gsub("^[[:space:]]+|[[:space:]]+$"; ""))) as $allowlist
        | .[] | select(.id as $id | $allowlist | index($id) | not) | .id
      ')"
  if [ -z "$unexpected" ]; then
    echo "Allowed in-progress issues: $allowed_in_progress"
  else
    echo "Unexpected in-progress issues (not current and not on ALLOW_IN_PROGRESS allowlist):" >&2
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
