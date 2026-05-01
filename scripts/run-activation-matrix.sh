#!/usr/bin/env bash
#
# Run the skill activation matrix in fresh harness sessions.
#
# Usage:
#   scripts/run-activation-matrix.sh --harness=claude [--out=DIR] [--rows=SECTION:ROW,...] [--jobs=N]
#   scripts/run-activation-matrix.sh --harness=codex  [--out=DIR] [--rows=SECTION:ROW,...] [--jobs=N]
#
# Each row is fired in its own fresh non-interactive session so context cannot
# bleed between rows. Rows are independent, so they run in parallel by default
# (--jobs controls concurrency; default 8). The script writes a normalized JSON
# artifact at $OUT/<ts>-<harness>-<commit>.json that scripts/collate-matrix-runs.sh
# can fold into a run-log entry — bring artifacts from multiple machines (e.g.
# claude local + codex elsewhere) and collate into one entry.
#
# Notes:
#   - Claude path uses --setting-sources user so the project's SessionStart
#     hooks (bd prime) don't pollute fresh-session activation.
#   - --plugin-dir loads this repo's plugin directly; no install step needed.
#   - --jobs=1 forces sequential execution (useful when debugging a single row
#     or when API/local-CPU contention is a concern).
#   - Codex loads repo-local skills from .agents/skills when run at REPO_ROOT.
#     The artifact format is identical to Claude's so collation works.

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
jobs=8

usage() {
  sed -n '3,23p' "$0" | sed 's/^# \{0,1\}//'
}

for arg in "$@"; do
  case "$arg" in
    --harness=*) harness="${arg#--harness=}" ;;
    --out=*)     out_dir="${arg#--out=}" ;;
    --rows=*)    filter_rows="${arg#--rows=}" ;;
    --jobs=*)    jobs="${arg#--jobs=}" ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "unknown arg: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

case "$jobs" in
  ''|*[!0-9]*) echo "--jobs must be a positive integer, got: $jobs" >&2; exit 1 ;;
esac
[ "$jobs" -lt 1 ] && { echo "--jobs must be >= 1" >&2; exit 1; }

case "$harness" in
  claude|codex) ;;
  *) echo "must pass --harness=claude or --harness=codex" >&2; exit 1 ;;
esac

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
case "$harness" in
  claude) command -v claude >/dev/null || { echo "claude is required for --harness=claude" >&2; exit 1; } ;;
  codex)  command -v codex  >/dev/null || { echo "codex is required for --harness=codex" >&2; exit 1; } ;;
esac

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
  # --max-budget-usd: per-row safety net only. Set high enough that legitimate
  #   activation work (e.g. executing-plans firing, then doing its initial
  #   investigation per the skill's "stop and ask" protocol) is not cut off.
  #   The earlier 0.15 cap masked real activation behavior on rows where the
  #   model legitimately invoked a skill that does extensive checking. Wall-
  #   clock parallelism (--jobs) is the actual lever for keeping runs fast,
  #   not budget pressure.
  # --permission-mode bypassPermissions: avoid hanging on permission prompts
  #   in non-interactive runs. The user is opting in by running this script.
  claude -p \
    --setting-sources user \
    --plugin-dir "$PLUGIN_DIR" \
    --output-format stream-json \
    --verbose \
    --max-budget-usd 1.00 \
    --permission-mode bypassPermissions \
    "$prompt" \
    > "$raw_path" 2>"$raw_path.stderr" || true
}

# Run a single prompt in a fresh codex session and emit JSONL to $1 (raw path).
# Codex does not currently expose a --plugin-dir flag; from REPO_ROOT it
# discovers this repo's .agents/skills symlink and loads skills from there.
run_codex_row() {
  local raw_path="$1"; shift
  local prompt="$1"; shift
  # --json: emit line-delimited events that include command executions.
  # --ephemeral: do not persist matrix sessions to the user's Codex history.
  # --ignore-user-config: keep user-level config/plugins from affecting rows;
  #   auth still comes from CODEX_HOME, and repo-local AGENTS/skills still load.
  # --sandbox read-only: activation checks should not mutate the checkout.
  # stdin is /dev/null so backgrounded workers cannot consume the matrix TSV.
  codex exec \
    --json \
    --ephemeral \
    --ignore-user-config \
    --sandbox read-only \
    --color never \
    -C "$REPO_ROOT" \
    "$prompt" \
    < /dev/null \
    > "$raw_path" 2>"$raw_path.stderr" || true
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
  # Codex CLI JSONL currently reports skill activation indirectly: the agent
  # reads the selected skill's SKILL.md via a command_execution event. Pull the
  # skill directory out of completed command strings and de-duplicate in order
  # because each skill can be read more than once during a turn.
  jq -r '
    def skill_from_path:
      try capture("(^|/)(\\.agents/)?skills/(?<skill>[A-Za-z0-9_-]+)/SKILL\\.md").skill catch empty;

    select(.type == "item.completed")
    | .item?
    | select(.type == "command_execution")
    | .command // ""
    | skill_from_path
    | sub("^[^:]+:"; "")
  ' "$raw_path" 2>/dev/null | awk 'NF && !seen[$0]++' || true
}

# ---- 4. Iterate rows, run, capture, build artifact ----

# Per-row results land in $raw_dir/<seq>.json so the parent can concat them in
# a stable order after all workers finish. We can't aggregate counts in shell
# vars across backgrounded jobs (each worker is its own subshell), so the
# summary is computed at the end by reading the per-row JSON files.

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

# Process a single row end-to-end: run the harness, extract activations,
# classify outcome, write per-row JSON to a dedicated file. Designed to be
# safe to run concurrently — every output path is row-scoped.
process_row() {
  local seq="$1" total="$2" section="$3" row="$4" prompt="$5" expected="$6" notes="$7"
  local safe_section raw_path result_path activated filtered expected_lc outcome
  safe_section="$(printf '%s' "$section" | tr -c '[:alnum:]-_' '_')"
  raw_path="$raw_dir/${safe_section}-${row}.ndjson"
  result_path="$raw_dir/${safe_section}-${row}.result.json"

  local started ended
  started="$(date +%s)"

  case "$harness" in
    claude) run_claude_row "$raw_path" "$prompt" ;;
    codex)  run_codex_row  "$raw_path" "$prompt" ;;
  esac

  case "$harness" in
    claude) activated="$(extract_activations_claude "$raw_path" | awk 'NF' | paste -sd, -)" ;;
    codex)  activated="$(extract_activations_codex  "$raw_path" | awk 'NF' | paste -sd, -)" ;;
  esac

  ended="$(date +%s)"
  local duration=$((ended - started))

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
    local expected_skills hit es
    expected_skills="$(printf '%s' "$expected" | tr -c 'a-zA-Z-' '\n' | awk 'length($0)>2' | sort -u)"
    if [ -z "$filtered" ]; then
      outcome="mismatch"
    else
      hit=0
      for es in $expected_skills; do
        if printf '%s\n' "$filtered" | tr ',' '\n' | grep -Fxq "$es"; then
          hit=1; break
        fi
      done
      [ $hit -eq 1 ] && outcome="match" || outcome="mismatch"
    fi
  fi

  if [[ "$expected" == *"→"* ]] || [[ "$expected" == *" or "* ]] || [[ "$expected_lc" == *"with pushback"* ]] || [[ "$expected_lc" == *"validation step"* ]]; then
    outcome="${outcome}-review"
  fi

  # Progress line. Workers are interleaved when --jobs > 1, so include both
  # row and outcome on a single printf so lines don't get mangled.
  local color reset='\033[0m'
  case "$outcome" in
    match*) color='\033[32m' ;;
    mismatch*) color='\033[31m' ;;
    *) color='\033[33m' ;;
  esac
  local review=""
  [[ "$outcome" == *-review ]] && review=" (review)"
  printf "[%d/%d] %s row %s (%ds) ${color}%s${reset}%s  expected=\"%s\"  activated=\"%s\"\n" \
    "$seq" "$total" "$section" "$row" "$duration" "$outcome" "$review" "$expected" "${filtered:-<none>}"

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
    --argjson duration "$duration" \
    '{
      section: $section, row: $row, prompt: $prompt, expected: $expected, notes: $notes,
      activated_raw: ($activated_raw | split(",") | map(select(length > 0))),
      activated_filtered: ($activated_filtered | split(",") | map(select(length > 0))),
      outcome: $outcome,
      duration_seconds: $duration,
      raw_path: $raw_path
    }' > "$result_path"
}

# Build the worklist and dispatch to backgrounded workers, throttled to $jobs.
# Each worker runs `process_row` in a subshell. We track filenames in the order
# they were enqueued so the final artifact's `rows[]` is stable and reproducible.

total_filtered=0
declare -a result_files=()

# Pre-count rows to give the [seq/total] progress label a meaningful denominator.
filtered_tsv="$(mktemp)"
trap 'rm -f "$rows_tsv" "$filtered_tsv"' EXIT
while IFS=$'\t' read -r section row prompt expected notes; do
  if should_run_row "$section" "$row"; then
    printf '%s\t%s\t%s\t%s\t%s\n' "$section" "$row" "$prompt" "$expected" "$notes" >> "$filtered_tsv"
  fi
done < "$rows_tsv"
total_filtered="$(wc -l < "$filtered_tsv" | tr -d ' ')"

if [ "$total_filtered" -eq 0 ]; then
  echo "No rows matched --rows filter; nothing to run." >&2
  exit 1
fi

echo "Running $total_filtered rows with --jobs=$jobs"

# Propagate Ctrl-C: kill any in-flight workers before exiting.
trap 'rm -f "$rows_tsv" "$filtered_tsv"; kill $(jobs -p) 2>/dev/null; exit 130' INT TERM

seq=0
running=0
while IFS=$'\t' read -r section row prompt expected notes; do
  seq=$((seq + 1))
  safe_section="$(printf '%s' "$section" | tr -c '[:alnum:]-_' '_')"
  result_files+=("$raw_dir/${safe_section}-${row}.result.json")

  process_row "$seq" "$total_filtered" "$section" "$row" "$prompt" "$expected" "$notes" &
  running=$((running + 1))

  if [ "$running" -ge "$jobs" ]; then
    # wait -n returns when any one backgrounded job exits.
    wait -n || true
    running=$((running - 1))
  fi
done < "$filtered_tsv"

# Drain remaining jobs.
wait

# ---- 5. Build summary artifact ----

results_ndjson="$(mktemp)"
trap 'rm -f "$rows_tsv" "$filtered_tsv" "$results_ndjson"' EXIT

# Concatenate per-row JSON files in enqueue order. A missing file means a
# worker crashed before writing its result — surface that loudly rather than
# silently shipping a short artifact.
missing=0
for f in "${result_files[@]}"; do
  if [ ! -f "$f" ]; then
    echo "missing per-row result: $f" >&2
    missing=$((missing + 1))
    continue
  fi
  cat "$f" >> "$results_ndjson"
done
if [ "$missing" -gt 0 ]; then
  echo "$missing row(s) produced no result file — artifact will be incomplete." >&2
fi

# Compute summary by reading the NDJSON we just assembled.
matched="$(jq -s   '[.[] | select(.outcome | startswith("match"))]    | length' "$results_ndjson")"
mismatched="$(jq -s '[.[] | select(.outcome | startswith("mismatch"))] | length' "$results_ndjson")"
ambiguous="$(jq -s '[.[] | select((.outcome | startswith("match")    | not) and (.outcome | startswith("mismatch") | not))] | length' "$results_ndjson")"
total_rows_run="$(jq -s 'length' "$results_ndjson")"

jq -s --arg ts "$ts" \
      --arg commit "$commit" \
      --arg harness "$harness" \
      --arg matrix_path "$(basename "$MATRIX")" \
      --argjson jobs "$jobs" \
      --argjson summary "{\"matched\":$matched,\"mismatched\":$mismatched,\"ambiguous\":$ambiguous,\"total\":$total_rows_run}" \
   '{
      run_id: ($ts + "-" + $harness + "-" + $commit),
      timestamp: $ts,
      commit: $commit,
      harness: $harness,
      matrix: $matrix_path,
      jobs: $jobs,
      summary: $summary,
      rows: .
    }' "$results_ndjson" > "$artifact"

echo
echo "Artifact: $artifact"
echo "Raw outputs: $raw_dir"
echo "Summary: $matched match, $mismatched mismatch, $ambiguous ambiguous (of $total_rows_run run, jobs=$jobs)"
