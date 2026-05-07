# A/B test harness for skill description activation rates

Empirically measure how often a candidate frontmatter description for a
Superpowers Beads skill causes a fresh Claude session to invoke that skill as
its first tool action on turn 1. Initial target: `using-superpowers`.

Tracking issue: `superpowers-beads-uij` (epic). This implementation is
`superpowers-beads-hag`.

## What it measures

For each `(variant, prompt, model, rep)` cell:

1. Build a temporary plugin tree that mirrors `plugins/superpowers-beads/`,
   substituting the candidate `description` into
   `skills/using-superpowers/SKILL.md`'s frontmatter.
2. Spawn a fresh `claude --print --output-format stream-json` session with:
   - `--setting-sources ""` (no `~/.claude/`, no project, no local — hermetic)
   - `--plugin-dir <variant>` (loads exactly one plugin: the variant)
   - `--no-session-persistence` (no resumable session left behind)
   - `--dangerously-skip-permissions` (required for non-interactive runs)
3. Send the prompt, parse the newline-delimited JSON event stream.
4. Validate from the `system/init` event that
   `superpowers-beads:using-superpowers` is in the loaded `skills` array.
5. Find the first `assistant` event with a `tool_use` block. Activation is
   defined as: `tool_use.name == "Skill"` AND
   `tool_use.input.skill == "superpowers-beads:using-superpowers"`.

The signal is binary per cell. Aggregate activation rates per
`(variant, model)` over `n` reps and any number of prompts.

## Variant injection mechanism

Hermetic per-cell sessions, **not** mutate-and-restore on `~/.claude/`.

For each variant, the harness writes a self-contained plugin tree under a temp
directory, then invokes claude with `--setting-sources "" --plugin-dir <temp>`.
That combination — confirmed by the spike (`superpowers-beads-2an`) — disables
filesystem settings inheritance entirely while loading exactly the variant
plugin. The user's installed `superpowers-beads:using-superpowers` is not
visible to the session under test.

Why hermetic plugin trees beat mutate-and-restore:

- No `~/.claude/` mutation; safe to interrupt or crash mid-run.
- Parallel-safe across cells (different temp dirs per variant).
- No SHA verification or backup/restore plumbing.
- No risk of leaving the user's working tree in a half-modified state.

## Auth and bucket caveat

Auth is the **subscription** auth in your installed `claude` CLI — runs deduct
from your interactive Pro 5h bucket, not from an API key. This is intentional:
the goal is to mirror the real environment users see.

Implications:

- Token usage is logged per cell; extrapolate from a small calibration pilot
  before committing to a large `--n`.
- The harness refuses to run without `--yes`. The preflight prints planned
  cell count + model breakdown so you can see what you are about to spend.

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
  --yes

# Calibration pilot recommended in the epic (4 variants x 5 prompts x 2 models x 2 reps = 80 cells)
python3 scripts/ab-test/run.py \
  --models claude-sonnet-4-6 claude-opus-4-7 \
  --n 2 \
  --yes
```

Output:

- Per-run JSONL: `scripts/ab-test/results/run-<utc-ts>.jsonl` (one row per cell)
- Activation-rate summary table printed at the end

To re-summarize an existing JSONL without re-running:

```bash
python3 scripts/ab-test/report.py scripts/ab-test/results/run-<utc-ts>.jsonl
```

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
  "returncode": 0,
  "stderr_excerpt": ""
}
```

`harness_validated == false` rows are excluded from `report.py` rate
calculations and counted separately as `excluded` so you can spot variant
loading regressions.

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

`--models` accepts one or more identifiers per the `claude --model` flag (e.g.
`claude-sonnet-4-6`, `claude-opus-4-7`, `claude-haiku-4-5`). The model field is
recorded verbatim in each JSONL row.

## Tests

```bash
cd scripts/ab-test
python3 -m unittest discover tests -v
```

Pure-logic modules (`detect`, `build_plugin`, `report`) have unit tests.
`runner` and `run` are validated by an `--n 1` end-to-end run because they
exercise the real `claude` CLI.

## Files

| File | Purpose |
|------|---------|
| `run.py` | CLI entry point: argparse, preflight, cell loop, JSONL writer |
| `runner.py` | Subprocess wrapper around `claude` CLI; usage extraction |
| `build_plugin.py` | Build temp plugin tree from a variant frontmatter |
| `detect.py` | Stream-json walker: harness validation + activation detection |
| `report.py` | Summarize a JSONL into a `(variant, model)` rate table |
| `variants.yaml` | The 4 candidates from `superpowers-beads-3c0` |
| `prompts.yaml` | The 5 fixed first-turn prompts |
| `tests/` | Unit tests for the pure-logic modules |
| `results/` | Generated JSONL artifacts (gitignored) |
