#!/usr/bin/env bash
#
# Run the skill activation matrix in fresh harness sessions.
#
# Usage:
#   scripts/run-activation-matrix.sh --harness=claude [--out=DIR] [--rows=SECTION:ROW,...]
#   scripts/run-activation-matrix.sh --harness=codex  [--out=DIR] [--rows=SECTION:ROW,...]
#
# Each row is fired in its own fresh non-interactive session so context cannot
# bleed between rows. The script writes a normalized JSON artifact at
# $OUT/<ts>-<harness>-<commit>.json that scripts/collate-matrix-runs.sh can
# fold into a run-log entry — bring artifacts from multiple machines (e.g.
# claude local + codex elsewhere) and collate into one entry.
#
# Notes:
#   - Claude path uses --setting-sources user so the project's SessionStart
#     hooks (bd prime) don't pollute fresh-session activation.
#   - --plugin-dir loads this repo's plugin directly; no install step needed.
#   - The codex path is stubbed; the user fills it in on a machine that has
#     codex installed. The artifact format is identical so collation works.

set -euo pipefail

# If the script exits unexpectedly, surface the failing line so debugging
# doesn't require re-running with bash -x. Triggered by set -e via ERR trap.
trap 'rc=$?; echo "" >&2; echo "run-activation-matrix.sh: aborted at line $LINENO with exit $rc" >&2' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MATRIX="$REPO_ROOT/docs/skill-activation-matrix.md"
PLUGIN_DIR="$REPO_ROOT/plugins/superpowers-beads"

harness=""
out_dir="$REPO_ROOT/.matrix-runs"
filter_rows=""

usage() {
  sed -n '3,21p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
  case "$arg" in
    --harness=*) harness="${arg#--harness=}" ;;
    --out=*)     out_dir="${arg#--out=}" ;;
    --rows=*)    filter_rows="${arg#--rows=}" ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

case "$harness" in
  claude|codex) ;;
  *) echo "must pass --harness=claude or --harness=codex" >&2; exit 1 ;;
esac

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

mkdir -p "$out_dir"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
commit="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
run_id="$ts-$harness-$commit"
artifact="$out_dir/$run_id.json"
raw_dir="$out_dir/$run_id"
mkdir -p "$raw_dir"

# ---- 1. Parse matrix into a TSV of (section, row, prompt, expected, notes) ----
#
# Only tables under H3 sections with the canonical header columns
# `# | Prompt | Expected | Notes` are considered. Italic-only rows
# (like "_(any first message in a new session)_") are skipped because
# they aren't runnable as single prompts.

rows_tsv="$(mktemp)"
trap 'rm -f "$rows_tsv"' EXIT

awk '
  function trim(s) { sub(/^[[:space:]]+/, "", s); sub(/[[:space:]]+$/, "", s); return s }

  /^### / {
    section = $0
    sub(/^### +/, "", section)
    in_table = 0
    next
  }

  /^\| # \| Prompt \| Expected \| Notes \|/ { in_table = 1; next }

  in_table && /^\|[-: ]+\|[-: ]+\|[-: ]+\|[-: ]+\|$/ { next }

  in_table && /^\| / {
    line = $0
    # Strip leading and trailing pipe + whitespace, then split on " | "
    sub(/^\| */, "", line)
    sub(/ *\|$/, "", line)
    n = split(line, f, / *\| */)
    if (n < 4) next
    num = trim(f[1])
    prompt = trim(f[2])
    expected = trim(f[3])
    notes = trim(f[4])
    # Skip non-runnable italic-only prompts.
    if (prompt ~ /^_/ || prompt == "") next
    # Strip surrounding double quotes from prompt (matrix style).
    sub(/^"/, "", prompt); sub(/"$/, "", prompt)
    # Use literal tab as field separator.
    printf "%s\t%s\t%s\t%s\t%s\n", section, num, prompt, expected, notes
    next
  }

  /^## / || /^# / { in_table = 0 }
' "$MATRIX" > "$rows_tsv"

total_rows="$(wc -l < "$rows_tsv" | tr -d ' ')"
echo "Parsed $total_rows runnable rows from $(basename "$MATRIX")"

# ---- 2. Harness-specific row runners ----

# Run a single prompt in a fresh claude session and emit NDJSON to $1 (raw path).
# Returns 0 on success regardless of activation outcome (we capture, not judge).
run_claude_row() {
  local raw_path="$1"; shift
  local prompt="$1"; shift
  # --setting-sources user: skip project hooks (bd prime) for clean activation.
  # --plugin-dir: load this repo's plugin directly.
  # --output-format stream-json + --verbose: emit one JSON object per event so
  #   we can detect Skill tool_use invocations.
  # --max-budget-usd: per-row safety net; tighten if matrix grows.
  # --permission-mode bypassPermissions: avoid hanging on permission prompts
  #   in non-interactive runs. The user is opting in by running this script.
  claude -p \
    --setting-sources user \
    --plugin-dir "$PLUGIN_DIR" \
    --output-format stream-json \
    --verbose \
    --max-budget-usd 0.50 \
    --permission-mode bypassPermissions \
    "$prompt" \
    > "$raw_path" 2>"$raw_path.stderr" || true
}

# Stub: fill in on a machine that has the Codex CLI installed.
# Should write NDJSON (or any line-oriented format) to $1 such that
# extract_activations_codex below can pull skill names out of it.
run_codex_row() {
  local raw_path="$1"; shift
  local prompt="$1"; shift
  echo "ERROR: codex runner not yet implemented." >&2
  echo "Edit run_codex_row() in scripts/run-activation-matrix.sh to wire up:" >&2
  echo "  codex exec --plugin-dir $PLUGIN_DIR <flags> \"\$prompt\" > \"\$raw_path\"" >&2
  echo "and update extract_activations_codex() to match codex's tool-event shape." >&2
  return 2
}

# ---- 3. Activation extractors ----
#
# Each extractor reads a raw output file and prints one skill name per line
# (in invocation order) for every Skill tool_use the harness emitted. Skill
# names are normalized: any `<plugin>:` namespace prefix is stripped so the
# matrix's bare names (e.g. `brainstorming`) compare cleanly.

extract_activations_claude() {
  local raw_path="$1"
  # stream-json emits one JSON object per line. Look at assistant messages
  # whose content includes a tool_use named "Skill", and pull input.skill.
  jq -r '
    select(.type == "assistant")
    | .message.content[]?
    | select(.type == "tool_use" and .name == "Skill")
    | .input.skill
    | sub("^[^:]+:"; "")
  ' "$raw_path" 2>/dev/null || true
}

extract_activations_codex() {
  local raw_path="$1"
  # TODO: fill in once codex's tool-event JSON shape is known. Until then,
  # emit nothing so rows record empty activation and the collator flags them.
  : > /dev/null
  echo -n ""
  # Hint: if codex emits NDJSON with a "tool_use" type and a "skill" arg,
  # mirror the claude extractor:
  # jq -r 'select(.type=="tool_use" and .name=="skill") | .input.skill | sub("^[^:]+:"; "")' "$raw_path"
}

# ---- 4. Iterate rows, run, capture, build artifact ----

# Build the artifact with jq from a stream of per-row JSON objects.
results_ndjson="$(mktemp)"
trap 'rm -f "$rows_tsv" "$results_ndjson"' EXIT

row_index=0
matched=0
mismatched=0
ambiguous=0

# Allow filtering with --rows=section:row,section:row,...
should_run_row() {
  local section="$1" row="$2"
  [ -z "$filter_rows" ] && return 0
  IFS=',' read -ra wanted <<<"$filter_rows"
  for w in "${wanted[@]}"; do
    if [ "$w" = "$section:$row" ] || [ "$w" = "$section" ]; then
      return 0
    fi
  done
  return 1
}

while IFS=$'\t' read -r section row prompt expected notes; do
  row_index=$((row_index + 1))
  if ! should_run_row "$section" "$row"; then
    continue
  fi
  # Sanitize section for filename use.
  safe_section="$(printf '%s' "$section" | tr -c '[:alnum:]-_' '_')"
  raw_path="$raw_dir/${safe_section}-${row}.ndjson"

  printf '[%d/%d] %s row %s ... ' "$row_index" "$total_rows" "$section" "$row"

  case "$harness" in
    claude) run_claude_row "$raw_path" "$prompt" ;;
    codex)  run_codex_row  "$raw_path" "$prompt" ;;
  esac

  case "$harness" in
    claude) activated="$(extract_activations_claude "$raw_path" | awk 'NF' | paste -sd, -)" ;;
    codex)  activated="$(extract_activations_codex  "$raw_path" | awk 'NF' | paste -sd, -)" ;;
  esac

  # Comparator: drop using-superpowers from activated for matching purposes
  # (it's the always-on orchestrator and not relevant unless explicitly expected).
  # Use awk rather than grep -v: grep exits 1 when no lines match, which under
  # set -e + pipefail kills the script on rows where the only activation was
  # using-superpowers (or there was no activation at all — the "no skill" case).
  filtered="$(printf '%s' "$activated" | tr ',' '\n' | awk 'NF && $0 != "using-superpowers"' | paste -sd, -)"

  expected_lc="$(printf '%s' "$expected" | tr '[:upper:]' '[:lower:]')"
  outcome=""
  if [[ "$expected_lc" == *"no skill"* ]]; then
    if [ -z "$filtered" ]; then outcome="match"; else outcome="mismatch"; fi
  else
    # Pull recognizable skill names out of the expected cell.
    expected_skills="$(printf '%s' "$expected" | tr -c 'a-zA-Z-' '\n' | awk 'length($0)>2' | sort -u)"
    if [ -z "$filtered" ]; then
      outcome="mismatch"
    else
      # If any expected skill appears in activated, count as match.
      hit=0
      for es in $expected_skills; do
        if printf '%s\n' "$filtered" | tr ',' '\n' | grep -Fxq "$es"; then
          hit=1; break
        fi
      done
      [ $hit -eq 1 ] && outcome="match" || outcome="mismatch"
    fi
  fi

  # Anything with chains/alternatives in expected is worth a human glance.
  if [[ "$expected" == *"→"* ]] || [[ "$expected" == *" or "* ]] || [[ "$expected_lc" == *"with pushback"* ]] || [[ "$expected_lc" == *"validation step"* ]]; then
    outcome="${outcome}-review"
  fi

  case "$outcome" in
    match*) matched=$((matched + 1)); printf '\033[32mmatch\033[0m' ;;
    mismatch*) mismatched=$((mismatched + 1)); printf '\033[31mmismatch\033[0m' ;;
    *) ambiguous=$((ambiguous + 1)); printf '\033[33m%s\033[0m' "$outcome" ;;
  esac
  [[ "$outcome" == *-review ]] && printf ' (review)'
  printf '  expected="%s"  activated="%s"\n' "$expected" "${filtered:-<none>}"

  jq -nc \
    --arg section "$section" \
    --arg row "$row" \
    --arg prompt "$prompt" \
    --arg expected "$expected" \
    --arg notes "$notes" \
    --arg activated_raw "$activated" \
    --arg activated_filtered "$filtered" \
    --arg outcome "$outcome" \
    --arg raw_path "${raw_path#$REPO_ROOT/}" \
    '{
      section: $section, row: $row, prompt: $prompt, expected: $expected, notes: $notes,
      activated_raw: ($activated_raw | split(",") | map(select(length > 0))),
      activated_filtered: ($activated_filtered | split(",") | map(select(length > 0))),
      outcome: $outcome,
      raw_path: $raw_path
    }' >> "$results_ndjson"
done < "$rows_tsv"

# ---- 5. Build summary artifact ----

jq -s --arg ts "$ts" \
      --arg commit "$commit" \
      --arg harness "$harness" \
      --arg matrix_path "$(basename "$MATRIX")" \
      --argjson summary "{\"matched\":$matched,\"mismatched\":$mismatched,\"ambiguous\":$ambiguous,\"total\":$row_index}" \
   '{
      run_id: ($ts + "-" + $harness + "-" + $commit),
      timestamp: $ts,
      commit: $commit,
      harness: $harness,
      matrix: $matrix_path,
      summary: $summary,
      rows: .
    }' "$results_ndjson" > "$artifact"

echo
echo "Artifact: $artifact"
echo "Raw outputs: $raw_dir"
echo "Summary: $matched match, $mismatched mismatch, $ambiguous ambiguous (of $row_index run)"
