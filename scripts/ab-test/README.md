# A/B test harness for skill description activation rates

Empirically measure how often a candidate frontmatter description for a
Superpowers Beads skill causes a fresh agent session to invoke that skill as
its first tool action on turn 1. Initial target: `using-superpowers`.

Tracking issue: `superpowers-beads-uij` (epic). This implementation is
`superpowers-beads-hag`; Codex support is tracked as `superpowers-beads-uij.1`.

## What it measures

For each `(variant, prompt, model, rep)` cell:

1. Build a temporary plugin tree that mirrors `plugins/superpowers-beads/`,
   substituting the candidate `description` into
   `skills/using-superpowers/SKILL.md`'s frontmatter.
2. Spawn a fresh Claude or Codex session.

   Claude uses `claude --print --output-format stream-json` with:
   - `--setting-sources ""` (no `~/.claude/`, no project, no local — hermetic)
   - `--plugin-dir <variant>` (loads exactly one plugin: the variant)
   - `--no-session-persistence` (no resumable session left behind)
   - `--dangerously-skip-permissions` (required for non-interactive runs)

   Codex uses `codex exec --json` with:
   - `--ephemeral` (no persistent session history)
   - `--ignore-user-config` (user config/plugins do not affect rows)
   - `--sandbox read-only` (activation checks should not mutate the workspace)
   - `-C <variant>` (runs from the temp variant workspace)
3. Send the prompt, parse the newline-delimited JSON event stream.
4. Validate from the `system/init` event that
   `superpowers-beads:using-superpowers` is in the loaded `skills` array
   (Claude) or that the temp workspace contains
   `.agents/skills/using-superpowers/SKILL.md` (Codex).
5. Find the first tool action. Activation is defined as:
   - Claude: first `tool_use.name == "Skill"` and
     `tool_use.input.skill == "superpowers-beads:using-superpowers"`.
   - Codex: first completed `command_execution` reads
     `.agents/skills/using-superpowers/SKILL.md`.

The signal is binary per cell. Aggregate activation rates per
`(variant, model)` over `n` reps and any number of prompts.

Only the *first* `tool_use` block decides the outcome, so for the Claude
harness the cell's `claude` subprocess is killed the moment that block arrives
in the stream — tool-heavy openers ("the build is broken") otherwise run a
dozen-plus investigation turns that the metric never reads and that dominate
the per-cell token burn. Turn-1 behavior is unaffected, so `activated` is the
same as if the session ran to completion; the row just records
`early_stopped: true` and its token/cost fields come from the last assistant
message rather than a `result` event (so `total_cost_usd`/`duration_ms` may be
`null`). Set `AB_TEST_NO_EARLY_STOP=1` to let every session run to natural
completion.

Cells run in rep/prompt/model order with variants adjacent inside each group.
That keeps partial JSONLs less biased if a run is interrupted before every
cell completes.

If a cell fails to a model rate limit (hard 429, "usage limit" / "quota", or a
rejected unified rate-limit status — distinct from a soft `allowed_warning`
event, which still returns a real answer), the run **stops**: cells already in
flight finish, every later cell is skipped, the partial JSONL is kept, and the
harness prints the exact `--resume` command to finish the rest once your bucket
resets. The process exits `2` (vs `0` for a clean finish, `1` for a refused
preflight). See "Resuming after a rate limit" below.

## Variant injection mechanism

Hermetic per-cell sessions, **not** mutate-and-restore on `~/.claude/`.

For each variant, the harness writes a self-contained plugin tree under a temp
directory, then invokes Claude with `--setting-sources "" --plugin-dir <temp>`
or Codex from that temp directory with a repo-local `.agents/skills` tree.
That combination — confirmed by the spike (`superpowers-beads-2an`) — disables
filesystem settings inheritance for Claude while loading exactly the variant
plugin. For Codex, `--ignore-user-config` keeps user plugins out of the run
while the temp `.agents/skills` tree supplies the variant skill definition.

Why hermetic plugin trees beat mutate-and-restore:

- No `~/.claude/` mutation; safe to interrupt or crash mid-run.
- Parallel-safe across cells (different temp dirs per variant).
- No SHA verification or backup/restore plumbing.
- No risk of leaving the user's working tree in a half-modified state.

## Auth and bucket caveat

Claude auth is the **subscription** auth in your installed `claude` CLI — runs
deduct from your interactive Pro 5h bucket, not from an API key. This is
intentional: the goal is to mirror the real environment users see.

Codex auth is your installed `codex` CLI session. Codex rows can consume the
same kind of session bucket that an interactive Codex session uses, and Codex
JSONL does not currently expose Claude-style token usage fields.

Implications:

- Token usage is logged per cell; extrapolate from a small calibration pilot
  before committing to a large Claude `--n`.
- For Codex, start with `--n 1 --concurrency 1` and a small variant/prompt
  filter before scaling up.
- The harness refuses to run without `--yes`. The preflight prints planned
  cell count, model breakdown, and concurrency so you can see what you are
  about to spend.
- If the bucket runs out mid-run, the harness stops itself on the first
  rate-limited cell rather than burning the remainder. Resume with `--resume`
  once it resets (see "Resuming after a rate limit").

To use API-key auth instead, prepend `ANTHROPIC_API_KEY=...` and pass an
explicit `--claude` to a CLI built without your subscription session — we have
not validated that path.

## Usage

```bash
# Smoke test (1 variant x 1 prompt x 1 model x 1 rep = 1 cell)
python3 scripts/ab-test/run.py \
  --variants current \
  --prompts feature-request \
  --models claude-haiku-4-5 \
  --n 1 \
  --concurrency 1 \
  --yes

# Calibration pilot recommended in the epic (4 variants x 5 prompts x 2 models x 2 reps = 80 cells)
python3 scripts/ab-test/run.py \
  --models claude-sonnet-4-6 claude-opus-4-7 \
  --n 2 \
  --yes

# Codex smoke run (1 variant x 1 prompt x CLI default model x 1 rep = 1 cell)
python3 scripts/ab-test/run.py \
  --harness codex \
  --variants current \
  --prompts feature-request \
  --n 1 \
  --concurrency 1 \
  --yes
```

`--variants` and `--prompts` use comma-separated ids because they filter fixed
YAML banks. `--models` accepts one or more space-separated model ids. When
omitted, Claude defaults to `claude-sonnet-4-6`; Codex omits `--model` and uses
the installed Codex CLI default model.

The harness defaults to `--concurrency 4`, which runs up to four cells at once
with independent temp plugin trees and fresh agent sessions. Use
`--concurrency 1` for strict sequential execution when debugging order-sensitive
output. Raise it only after a small pilot confirms your subscription bucket can
handle the parallel load; if stderr excerpts show rate-limit or bucket pressure,
lower concurrency before increasing `--n`.

Output:

- Per-run JSONL: `scripts/ab-test/results/run-<utc-ts>.jsonl` (one row per cell)
- Activation-rate summary table printed at the end, including excluded and
  rate-limited row counts

To re-summarize an existing JSONL without re-running — pass one file, or
several (an original run plus its `--resume` runs) to combine them:

```bash
python3 scripts/ab-test/report.py scripts/ab-test/results/run-<utc-ts>.jsonl
python3 scripts/ab-test/report.py results/run-A.jsonl results/run-B.jsonl
```

## Resuming after a rate limit

A large Claude run (hundreds of cells) is likely to exhaust your Pro 5h bucket
mid-run. When that happens the harness stops on the first rate-limited cell,
keeps the partial JSONL, and prints a `--resume` command. After your bucket
resets, run that command: `--resume <prev.jsonl>` (repeatable) skips every cell
already completed in the prior file(s) and runs only the remainder, into a new
JSONL. Then point `report.py` at all the files to get the combined table.

```bash
# Run 1 — say it stops after 51 of 400 cells on a rate limit
python3 scripts/ab-test/run.py --models claude-sonnet-4-6 --n 80 --yes
#   ⚠ Run stopped early on a model rate limit: rate_limit_event status=rejected
#   ...When your usage limit resets, finish the test with:
#     python3 scripts/ab-test/run.py --n 80 --resume results/run-<ts1>.jsonl --yes

# Run 2 — after the reset; does the remaining ~349 cells
python3 scripts/ab-test/run.py --n 80 --resume results/run-<ts1>.jsonl --yes

# Combined 400-cell summary
python3 scripts/ab-test/report.py results/run-<ts1>.jsonl results/run-<ts2>.jsonl
```

Notes:

- The resume run must use the same variant/prompt/model/`--n` selection as the
  original (it skips by `(variant, prompt, model, rep)`); pass back any other
  non-default flags you used. The printed resume command already includes them.
- Rate-limit casualty rows are written to the JSONL with `rate_limited_failure`
  set; `--resume` re-runs those cells and `report.py` ignores them.
- If a resume run still doesn't get through everything, it stops and prints the
  next `--resume` command (now chaining both prior files). Repeat as needed.
- A resume run whose cells are all already complete prints "nothing to run" and
  exits `0`.

When a run is used as evidence for a description change, promote the JSONL into
`scripts/ab-test/results/promoted/<bead-id>.jsonl` and commit it with the code
or skill change it supports. Leave ordinary exploratory runs under
`scripts/ab-test/results/run-<utc-ts>.jsonl`; those remain ignored.

## JSONL row schema

```json
{
  "ts": "2026-05-07T18:00:00+00:00",
  "variant_id": "current",
  "prompt_id": "feature-request",
  "model": "claude-sonnet-4-6",
  "rep": 0,
  "harness_validated": true,
  "first_tool_call": "Bash",
  "first_tool_skill_name": null,
  "first_tool_call_block_index": 1,
  "activated": false,
  "input_tokens": 10,
  "output_tokens": 142,
  "cache_read_input_tokens": 24420,
  "cache_creation_input_tokens": 5163,
  "duration_ms": 1271,
  "total_cost_usd": 0.0092,
  "rate_limit_status": null,
  "rate_limited_failure": null,
  "returncode": 0,
  "early_stopped": false,
  "stderr_excerpt": ""
}
```

`harness_validated == false` rows are excluded from `report.py` rate
calculations and counted separately as `excluded` so you can spot variant
loading regressions. Rows with a Claude `rate_limit_event` carry
`rate_limit_status` (e.g. `allowed_warning`) and are counted in the
`rate_limited` summary column. `rate_limited_failure` is `null` unless the cell
failed *because* of throttling — those rows are the casualty marker the run
stopped on; `report.py` skips them and `--resume` re-runs the cell. Codex rows
leave token/cost/rate-limit fields as `null` unless the Codex CLI exposes
compatible usage data in the future.

## Adding a new variant

Edit `variants.yaml`:

```yaml
variants:
  - id: my-new-variant
    description: "New candidate description text goes here"
```

Then run with `--variants current,my-new-variant` to compare against the baseline.

## Adding a new prompt

Edit `prompts.yaml`:

```yaml
prompts:
  - id: my-new-prompt
    text: "User-facing first-turn prompt here"
```

The prompt should be representative of a real first-turn user message; keep
the bank small and reproducible rather than sampled live.

## Adding a new model

`--models` accepts one or more identifiers per the selected harness. For Claude,
pass values accepted by `claude --model` (e.g. `claude-sonnet-4-6`,
`claude-opus-4-7`, `claude-haiku-4-5`). For Codex, pass values accepted by
`codex exec --model`; omit the flag to use the Codex CLI default. The model
field is recorded verbatim in each JSONL row. The harness checks
`claude --version` at startup for Claude runs and requires Claude Code 2.1.132
or newer, the first version validated against the current stream-json fields.

## Tests

```bash
cd scripts/ab-test
python3 -m unittest discover tests -v
```

Pure-logic modules (`detect`, `build_plugin`, `executor`, `report`, `runner`,
`codex_runner`, `ratelimit`, and `run` — including the stop-on-rate-limit loop)
have unit tests. Full end-to-end confidence still comes from a small `--n 1` run
because it exercises the real agent CLI. Use the Codex smoke shape above
sparingly because it consumes the real Codex session.

## Files

| File | Purpose |
|------|---------|
| `run.py` | CLI entry point: argparse, preflight, cell loop, JSONL writer |
| `executor.py` | Sequential or parallel cell execution wrapper |
| `runner.py` | Subprocess wrapper around `claude` CLI; usage extraction |
| `codex_runner.py` | Subprocess wrapper around `codex exec`; Codex activation detection |
| `build_plugin.py` | Build temp plugin tree from a variant frontmatter |
| `detect.py` | Stream-json walker: harness validation + activation detection |
| `ratelimit.py` | Classify a cell's output as a model rate-limit failure (vs ordinary failure / soft warning) |
| `report.py` | Summarize one or more JSONL files into a `(variant, model)` rate table |
| `variants.yaml` | The 4 candidates from `superpowers-beads-3c0` |
| `prompts.yaml` | The 5 fixed first-turn prompts |
| `tests/` | Unit tests for the pure-logic modules |
| `results/` | Generated JSONL artifacts (gitignored) |
