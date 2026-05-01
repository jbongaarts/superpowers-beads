#!/usr/bin/env bash
#
# Collate one or more matrix-run artifacts into a markdown run-log entry
# suitable for pasting under `## Run log` in docs/skill-activation-matrix.md.
#
# Usage:
#   scripts/collate-matrix-runs.sh ARTIFACT [ARTIFACT...]
#
# Example:
#   scripts/collate-matrix-runs.sh \
#     .matrix-runs/20260430T120000Z-claude-bc34335.json \
#     /tmp/from-other-machine/20260430T140000Z-codex-bc34335.json

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: $0 ARTIFACT [ARTIFACT...]" >&2
  exit 1
fi

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

# ---- 1. Per-run summary table rows ----

date_today="$(date -u +%Y-%m-%d)"

echo "<!-- Paste under \`## Run log\` in docs/skill-activation-matrix.md -->"
echo

for artifact in "$@"; do
  jq -r --arg today "$date_today" '
    def verdict:
      if .summary.mismatched == 0 and .summary.ambiguous == 0 then "Pass"
      elif .summary.mismatched == 0 then "Pass with review"
      else "Fail (\(.summary.mismatched) mismatch)"
      end;
    "| \($today) | `\(.commit)` | \(.harness | ascii_upcase) (automated) | \(verdict) | \(.summary.matched)/\(.summary.total) match, \(.summary.mismatched) mismatch, \(.summary.ambiguous) ambiguous. See details for [`\(.run_id)`](#\(.run_id | ascii_downcase | gsub("[^a-z0-9-]"; "-"))). |"
  ' "$artifact"
done

echo
echo "---"
echo

# ---- 2. Per-run details ----

for artifact in "$@"; do
  run_id="$(jq -r '.run_id' "$artifact")"
  harness="$(jq -r '.harness' "$artifact")"
  commit="$(jq -r '.commit' "$artifact")"
  total="$(jq -r '.summary.total' "$artifact")"
  matched="$(jq -r '.summary.matched' "$artifact")"
  mismatched="$(jq -r '.summary.mismatched' "$artifact")"
  ambiguous="$(jq -r '.summary.ambiguous' "$artifact")"

  echo "### $run_id"
  echo
  echo "Automated run via \`scripts/run-activation-matrix.sh --harness=$harness\` against commit \`$commit\`."
  echo "Result: $matched/$total match, $mismatched mismatch, $ambiguous flagged for review."
  echo

  # Mismatches first, ambiguous next, matches collapsed.
  mismatch_count="$(jq '[.rows[] | select(.outcome | startswith("mismatch"))] | length' "$artifact")"
  if [ "$mismatch_count" -gt 0 ]; then
    echo "**Mismatches:**"
    echo
    echo "| Section | Row | Expected | Activated | Prompt |"
    echo "|---|---|---|---|---|"
    jq -r '
      .rows[]
      | select(.outcome | startswith("mismatch"))
      | "| \(.section) | \(.row) | \(.expected) | \(.activated_filtered | join(", ") // "<none>") | \(.prompt | .[0:80]) |"
    ' "$artifact"
    echo
  fi

  ambiguous_count="$(jq '[.rows[] | select(.outcome | endswith("-review"))] | length' "$artifact")"
  if [ "$ambiguous_count" -gt 0 ]; then
    echo "**Flagged for review** (chains, alternatives, or qualifiers in the Expected column — verify by hand):"
    echo
    echo "| Section | Row | Expected | Activated |"
    echo "|---|---|---|---|"
    jq -r '
      .rows[]
      | select(.outcome | endswith("-review"))
      | "| \(.section) | \(.row) | \(.expected) | \(.activated_filtered | join(", ") // "<none>") |"
    ' "$artifact"
    echo
  fi

  if [ "$mismatch_count" -eq 0 ] && [ "$ambiguous_count" -eq 0 ]; then
    echo "All rows matched the Expected column without ambiguity."
    echo
  fi

  echo "<details><summary>All rows</summary>"
  echo
  echo "| Section | Row | Outcome | Expected | Activated |"
  echo "|---|---|---|---|---|"
  jq -r '
    .rows[]
    | "| \(.section) | \(.row) | \(.outcome) | \(.expected) | \(.activated_filtered | join(", ") // "<none>") |"
  ' "$artifact"
  echo
  echo "</details>"
  echo
done
