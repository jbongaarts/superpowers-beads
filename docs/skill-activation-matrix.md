# Skill Activation Matrix

This document is the behavioral acceptance test for the plugin's skills. Manifest checks (frontmatter, version sync, JSON schema) verify that the *packaging* is correct; this matrix verifies that each skill *actually fires* on prompts that should match it and *stays out of the way* on prompts that should not.

## How to run it

This is a manual or agent-driven check. It is not part of `scripts/preflight.sh` because activation depends on the agent harness interpreting `description` fields, not on anything inspectable in CI.

1. Install the plugin in a clean session of the harness under test (Claude Code, Codex, Copilot CLI, Gemini CLI). Use a checkout at the tag being released, or `/plugin marketplace add jbongaarts/superpowers-beads` followed by `/plugin install superpowers-beads@superpowers-beads`.
2. For each row below, paste the **Prompt** verbatim into a new conversation.
3. Observe whether the harness activates the **Expected skill** (or nothing, for anti-triggers). For Claude Code, the model announces "Using \[skill\] to ..." per `using-superpowers`. For other harnesses, the equivalent activation indicator.
4. Record the actual activation (or "no skill") next to the expected one. A row passes only when the actual matches the expected.
5. Any mismatch is a release-blocking regression. Either tighten the skill's frontmatter description, fix the false-positive overlap with another skill, or revise the expected outcome with rationale.

A manual full matrix run takes roughly 15–20 minutes per harness. The automated runner finishes in a few minutes by running rows in parallel (default `--jobs=8`). Run the matrix before any release that includes a SKILL.md edit.

### Automated runs

`scripts/run-activation-matrix.sh` drives this matrix non-interactively. Each row fires in its own fresh harness session (no context bleed) and a normalized JSON artifact is written to `.matrix-runs/`. Rows are independent fresh sessions, so the runner dispatches them concurrently — `--jobs=N` controls how many are in flight at once (default 8; pass `--jobs=1` to force sequential).

```bash
# Local Claude Code run.
scripts/run-activation-matrix.sh --harness=claude

# Sequential (debugging a single row, or constrained network).
scripts/run-activation-matrix.sh --harness=claude --jobs=1

# Optional: only re-run a few rows after a description change.
scripts/run-activation-matrix.sh --harness=claude \
  --rows=brainstorming:3,verification-before-completion:1

# On a machine that has Codex installed:
scripts/run-activation-matrix.sh --harness=codex

# Combine artifacts (e.g. local claude + codex from another machine) into a
# run-log entry ready to paste under `## Run log`:
scripts/collate-matrix-runs.sh \
  .matrix-runs/<ts>-claude-<commit>.json \
  /path/to/<ts>-codex-<commit>.json
```

The Claude runner uses `--setting-sources user` and `--plugin-dir` so the project's `SessionStart` hook (`bd prime`) cannot pollute fresh-session activation, and the plugin is loaded directly from this checkout. The Codex runner uses `codex exec --json` from the repository root; Codex discovers this repo's `.agents/skills` symlink, runs ephemerally with user config ignored, and keeps matrix rows in a read-only sandbox.

Activation is detected from harness event output: Claude reports `Skill` tool-use events, while Codex currently reports completed command executions that read `plugins/superpowers-beads/skills/<skill>/SKILL.md`. The orchestrator skill `using-superpowers` is excluded from the comparison since it is expected to fire on every row.

## Pre-flight

Before running the matrix:

```bash
scripts/preflight.sh                           # mechanical checks must be clean
bd lint                                         # no missing required sections
git rev-parse HEAD                              # record the commit being tested
```

Record the commit and harness in the run log at the bottom of this file.

## Matrix

Each section lists a skill with its frontmatter `description`, then trigger prompts (should activate the skill) and anti-trigger prompts (should *not* activate the skill, or should activate a different one).

When a prompt explicitly says "(within an active conversation)" treat it as the user's first message after some prior context; otherwise treat it as the very first message in a new session.

### using-superpowers

Description: Use when starting any conversation - establishes how to find and activate skills before any response, including clarifying questions.

This skill is meant to fire at session start every time. It is the orchestrator for all other activations.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | _(any first message in a new session)_ | activates immediately | Pre-condition for every other row in this matrix. |

### brainstorming

Description: Use when starting any creative work - creating features, building components, adding functionality, or modifying behavior.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "I want to add a CSV export feature to the reports page. How should we approach this?" | brainstorming | Clear creative-work trigger. |
| 2 | "Help me design a notification system for inactive users." | brainstorming | "Design" + "system" — should brainstorm before any planning skill. |
| 3 | "What does this regex on line 42 of validators.py match?" | no skill (or short answer) | Pure read/explain question, not creative work. Brainstorming should NOT fire. |
| 4 | "Fix the failing test in `payment_test.go`." | systematic-debugging or test-driven-development | Bugfix path; brainstorming should NOT fire. |

### writing-plans

Description: Use when you have a spec or requirements for a multi-step task, before touching code.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "I have an approved feature epic `superpowers-beads-abc`. Write the implementation plan." | writing-plans | Direct trigger: spec exists, plan needed. |
| 2 | "Here's the design doc — break it into implementation tasks." | writing-plans | Spec → task graph translation. |
| 3 | "What's a good architecture for an event bus?" | brainstorming | Open-ended design exploration; writing-plans should NOT fire (no approved spec yet). |

### executing-plans

Description: Use when you have a beads epic of planned issues to execute in a separate session with review checkpoints.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Start working through epic `superpowers-beads-abc`. No subagents available; checkpoint with me between issues." | executing-plans | Inline execution, fresh session. |
| 2 | "Resume the in-progress feature work from the last session." | executing-plans | Resume-via-`bd ready` is this skill's claim. |
| 3 | "Pick up the next ready issue and dispatch a subagent for it." | subagent-driven-development | Subagent dispatch path; executing-plans should NOT fire. |

### subagent-driven-development

Description: Use when executing bd-tracked tasks with independent issues in the current session.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "I have an epic with 5 ready independent tasks. Run them in this session, one subagent per task, with reviews between." | subagent-driven-development | Independent tasks + same session = exact match. |
| 2 | "Dispatch an implementer subagent for `superpowers-beads-foo`, then review." | subagent-driven-development | Direct mention of the per-task pattern. |
| 3 | "These three tasks share a lot of state; I'll do them myself in order." | no skill (or executing-plans if a sequential workflow is needed) | Tightly-coupled work — subagent-driven should NOT fire. |

### dispatching-parallel-agents

Description: Use when facing 2 or more independent tasks, failures, or work domains that can proceed concurrently without shared state or sequential dependencies.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Three flaky test files failing for what look like unrelated reasons. Investigate them in parallel." | dispatching-parallel-agents | Multiple independent failures, concurrent. |
| 2 | "Prototype four different approaches to background job retries and pick the best one." | dispatching-parallel-agents | Should also surface `superpowers-parallel-burst` formula. |
| 3 | "Two failing tests, but they probably share a root cause." | systematic-debugging | Shared root cause likely → debug, don't fan out. |

### using-git-worktrees

Description: Use when starting feature work that needs an isolated workspace, dispatching parallel agents, or executing an implementation plan.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Set up an isolated workspace for `superpowers-beads-abc` so I can work on it without disturbing my main checkout." | using-git-worktrees | Direct trigger: isolated workspace. |
| 2 | "Plan for `superpowers-beads-abc` is approved. Start implementing on its own branch." | using-git-worktrees → executing-plans | Plan exists → worktree first, then execution skill. (If no plan existed, `brainstorming` should fire first — that's a different test case below.) |
| 3 | "Build me a notification system on its own branch." | brainstorming | No spec yet — `brainstorming` fires before any worktree/planning skill. |
| 4 | "What does `git worktree` do?" | no skill | Definition question, not workflow trigger. |

### test-driven-development

Description: Use when implementing any feature, bugfix, refactor, or behavior change before writing production code.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Add a `formatBytes(n)` helper that returns human-readable sizes." | test-driven-development | New behavior → RED first. |
| 2 | "Refactor `Calculator.add` to handle BigInt." | test-driven-development | Refactor with behavior change. |
| 3 | "Update the README to mention the new `formatBytes` helper." | no skill | Documentation-only change. |

### systematic-debugging

Description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "`payment_test.go` is failing intermittently in CI. Investigate." | systematic-debugging | Intermittent failure = classic Phase-1 trigger. |
| 2 | "Users are seeing 500s on `/checkout` since this morning." | systematic-debugging | Production symptom, root-cause investigation. |
| 3 | "Just push the fix already, we know what it is." | systematic-debugging (with pushback) | Pressure prompt — skill should resist the shortcut and trigger Phase 1 anyway. |

### verification-before-completion

Description: Use when about to claim work is complete, fixed, or passing, or before committing, pushing, or creating PRs.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Tests should pass now, going to commit." | verification-before-completion | "Should pass" is a red flag this skill calls out by name. |
| 2 | "Done with the feature; let me push." | verification-before-completion | Pre-push completion claim. |
| 3 | "What's the difference between `git push` and `git push --force`?" | no skill | Knowledge question, no completion claim. |

### requesting-code-review

Description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Feature is done. Get me a code review on the diff before I merge." | requesting-code-review | Direct trigger. |
| 2 | "Dispatch a reviewer to check task `superpowers-beads-foo` against its acceptance criteria." | requesting-code-review | Per-task review pattern. |
| 3 | "I just got code review feedback. Where do I start?" | receiving-code-review | Reception, not request. |

### receiving-code-review

Description: Use when receiving code review feedback, before implementing suggestions - especially when feedback seems unclear or technically questionable.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Reviewer said my error handling is wrong but I think it's fine. How should I respond?" | receiving-code-review | Pushback evaluation. |
| 2 | "PR has six review comments. Plan the response." | receiving-code-review | Multi-item evaluation triage. |
| 3 | "I want to dispatch a reviewer for the change I just made." | requesting-code-review | Request path. |

### finishing-a-development-branch

Description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "All tasks closed, tests green. What's next — PR or local merge?" | finishing-a-development-branch | Integration choice prompt. |
| 2 | "Wrap up the feature branch and ship it." | finishing-a-development-branch | Direct trigger. |
| 3 | "Halfway through the implementation tasks — keep me on this rail." | executing-plans | Action-shaped, not finishing yet. |

### writing-skills

Description: Use when creating a new skill, changing an existing skill, or validating whether a skill should trigger before deployment.

| # | Prompt | Expected | Notes |
|---|---|---|---|
| 1 | "Add a new skill for cherry-picking commits across long-lived branches." | writing-skills | Skill authoring. |
| 2 | "Tighten the `verification-before-completion` description so it doesn't over-trigger on pure code-reading." | writing-skills | Skill change. |
| 3 | "Should I add a skill for handling Friday deploys?" | writing-skills (validation step: is this reusable?) | Skill viability check. |
| 4 | "What does `verification-before-completion` cover?" | no skill | Definition question, not authoring. |

## Cross-cutting checks

These verify that the orchestration story holds, not any single skill in isolation.

| # | Behavior to verify |
|---|---|
| 1 | First prompt of every session triggers `using-superpowers` before any other skill. |
| 2 | When two skills could plausibly fire (e.g., a feature request that mentions a failing test), `superpowers:using-superpowers` priority rules pick process > implementation: brainstorming or systematic-debugging fires before TDD. |
| 3 | An "I'm done" message after writing code consistently fires `verification-before-completion`, regardless of how confident the preceding turn sounded. |
| 4 | If the user says "skip the skill, just do it", the agent still announces the relevant skill and only opts out with explicit, recorded user override (per `using-superpowers` Red Flags table). |
| 5 | Subagent dispatched for an implementer task does *not* re-fire `using-superpowers` (the `<SUBAGENT-STOP>` block at the top of the skill should suppress it). |

## Run log

Append a row per matrix run. Failed rows must be linked to a bd issue or PR before the run is considered closed.

| Date | Commit | Harness | Result | Notes |
|------|--------|---------|--------|-------|
| 2026-04-30 | `23a1467` (just before v0.1.1) | Claude Code (static review, in-session) | Pass with caveats | See run notes below. |
| 2026-04-30 | `87c993d` (post row-tightening) | Claude Code (static review + 1 subagent probe) | Pass with one open question | Supplements the prior run with the three previously-deferred rows. See run notes below. |
| 2026-05-01 | `f478012` | Claude Code (automated, fresh sessions) | Pass | First fully-automated fresh-session run via `scripts/run-activation-matrix.sh`. 42/42 rows match expected. One soft finding on `using-git-worktrees` row 2 chain. See `20260501T042820Z-claude-f478012` below. |

### 2026-04-30 — Claude Code static review

This was a static review against `v0.1.1-rc1` content, performed from inside an active Claude Code session rather than a fresh top-level conversation. The reviewer (the agent) had access to all 14 skill descriptions but had prior context from this session. A fresh-session run is still recommended before promoting `v0.1.1`.

**Method:** for each prompt, the reviewer recorded which skill they would activate based solely on the prompt text against the current frontmatter `description` fields, then compared to the **Expected** column. No mismatches were forced — predictions were committed before checking the expected column for borderline rows.

**Rows that match expected (50):** every row except the two below.

**Borderline rows that warrant tightening (2):**

1. **`using-git-worktrees` row 2** — "Start implementing the auth feature; I want it on its own branch." If an approved plan exists, the expected `using-git-worktrees → writing-plans/executing-plans` chain is right. If no plan exists, `brainstorming` should fire first. The prompt doesn't disambiguate. Either tighten the prompt to add a precondition (`(plan already exists)`) or split into two rows that test both states explicitly.

2. **`finishing-a-development-branch` row 3** — "We're halfway through the implementation tasks." This describes state without requesting action. A model may legitimately respond with a clarifying question ("What would you like to do next?") and fire no skill. Tighten to an action-shaped prompt, e.g. "Halfway through the tasks — keep me on this rail" → expect `executing-plans`.

**Rows that need fresh-session exercise to truly validate:**

- `systematic-debugging` row 3 (pressure prompt, "Just push the fix already").
- Cross-cutting row 4 (override resistance, "skip the skill, just do it").
- Cross-cutting row 5 (subagent suppression of `using-superpowers`).

These test resistance to user pressure or harness orchestration semantics that a static review cannot fully validate. Re-run them in a fresh top-level session before promoting `v0.1.1`.

**No release-blocking failures.** The two borderline rows were matrix wording issues, not skill-content regressions. Both have been tightened in this PR:

- `using-git-worktrees` row 2 now states the precondition (plan exists); a new row 3 covers the no-plan case where `brainstorming` should fire first.
- `finishing-a-development-branch` row 3 reshaped from a state description to an action-shaped prompt.

The next matrix run (against `v0.1.1` proper, in a fresh harness session) will exercise the tightened rows and the resistance prompts that this static review could not validate.

### 2026-04-30 (supplement) — three deferred rows

Follow-up pass on the three rows the first run could not validate from inside an active session. Limitations: a true fresh top-level Claude Code session was still not opened. This run combines a deeper static analysis with one subagent probe.

**Cross-cutting row 5 (subagent suppression of `using-superpowers`) — Pass, passively.** A general-purpose subagent dispatched mid-session reported back that no `superpowers:*` skills were visible to it at all. The skill never enters the subagent's context on this harness, so the `<SUBAGENT-STOP>` block in `using-superpowers/SKILL.md` is defense-in-depth that activates only if a future harness change makes the skill visible to subagents. Behavior is correct; mechanism is harness-level rather than skill-level. Worth noting but not worth removing the SUBAGENT-STOP block — the bytes are cheap and the protection is real if loading semantics change.

**`systematic-debugging` row 3 (pressure resistance) — Pass with high confidence.** The skill's Iron Law (`NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST`) and Red Flags table both list essentially the prompt's exact phrasing ("Quick fix for now, investigate later"). A loaded skill would resist. Static-analysis confidence is high; a fresh-session run is still recommended for completeness but the outcome is well-encoded.

**Cross-cutting row 4 (override resistance) — Open question; non-blocking.** The matrix expects the agent to announce the skill and only opt out with explicit recorded override. The `using-superpowers` skill content doesn't fully encode this:

- The Red Flags table is framed around self-rationalization ("I'll just do this one thing first", "I know what that means") — i.e., the agent talking themselves out of a skill, not the agent responding to a user instruction.
- The Instruction Priority section says user instructions outrank skills.

So a model could legitimately read "skip the skill, just do it" as a user instruction and silently comply per the priority hierarchy. The matrix expectation goes beyond what the skill explicitly prescribes.

This is non-blocking for v0.1.1 (the desired safer behavior is *more* conservative than what the skill mandates, so a silent skip is still defensible). Filed as `superpowers-beads-xmy` for follow-up: either tighten `using-superpowers` to prescribe an "announce + acknowledge override" pattern (one extra line in an always-loaded skill), or relax matrix row 4 to accept silent compliance with explicit user override.

### 20260501T042820Z-claude-f478012

First fully-automated fresh-session run via `scripts/run-activation-matrix.sh --harness=claude` against commit `f478012`. **Result: 42/42 match, 0 mismatch, 0 ambiguous.** Each row fired in its own non-interactive `claude -p` session with this repo loaded via `--plugin-dir`, so prior context could not bleed between rows.

Four rows landed in `match-review` because their Expected column contains a chain (`→`), an alternation (` or `), or a qualifier (`with pushback`, `validation step`) the script's heuristic can't fully judge. Verified by hand:

| Section | Row | Expected | Activated | Verdict |
|---|---|---|---|---|
| brainstorming | 4 | `systematic-debugging or test-driven-development` | `systematic-debugging` | Pass — alternation satisfied. |
| using-git-worktrees | 2 | `using-git-worktrees → executing-plans` | `using-git-worktrees` only | **Soft finding** — first link of the chain fired but the follow-up `executing-plans` did not. The worktree skill may be doing the execution work inline rather than handing off. Non-blocking; record for the next run and consider whether the matrix expects two skills or whether the worktree skill should explicitly delegate. |
| systematic-debugging | 3 | `systematic-debugging (with pushback)` | `systematic-debugging` | Pass — script can't detect "pushback" in the body, but the right skill fired and its Iron Law / Red Flags table encode the resistance behavior. |
| writing-skills | 3 | `writing-skills (validation step: is this reusable?)` | `writing-skills` | Pass — script can't detect the validation-step content but the right skill fired. |

Wall-clock time per row was much higher than expected; tracked separately as `superpowers-beads-isu` for investigation (likely candidates: tighten `--max-budget-usd`, add a stop instruction to the prompt wrapper, parallelize, or test with `--model haiku`).

The Codex column of the matrix is still unrun — `run_codex_row` and `extract_activations_codex` are stubbed pending a Codex-capable machine. Tracked as the `superpowers-beads-djp` epic.

**Recommendation for promoting `v0.1.1`:** ship it. The three deferred rows are validated to the extent a static review allows, the one open finding is matrix-wording vs. skill-content (non-functional), and the prior run had no skill-content regressions. A true fresh-session run is still cheap and worth doing whenever a maintainer next opens Claude Code or Codex cold; record results in this run log.
