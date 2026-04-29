---
name: executing-plans
description: Use when you have a beads epic of planned issues to execute in a separate session with review checkpoints
---

<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Executing Plans

## Overview

Inspect the epic, review critically, execute all issues via `bd ready`, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Inspect the Epic

1. View the epic and its child issues:
   ```
   bd show <epic-id>
   ```
   Optionally list open child issues:
   ```
   bd list --status=open
   ```
2. Review critically — identify any questions or concerns about the scope, ordering, or feasibility of the issues.
3. If concerns: Raise them with your human partner before starting.
4. If no concerns: Proceed to Step 2.

Do **not** read a plan file. The epic and its child issues are the source of truth.

### Step 2: Execute Issues

Loop until no ready issues remain (scoped to the epic):

```
while bd ready shows open issues:
  pick the highest-priority issue from bd ready
  bd update <id> --claim
  bd show <id>          # read the brief: steps, acceptance criteria, verifications
  follow the steps in the issue brief exactly
  run the verifications named in the issue brief
  bd close <id>
```

**Resuming in a fresh session:** Re-run `bd ready`. Issues that were in-progress or still open surface automatically. No plan file is needed — beads is the single source of truth across session boundaries.

**Formula-poured chains:** if a `superpowers-feature` (or other) workflow formula was poured upstream, its `implement` and `verify` steps will appear in `bd ready` like any other issue. Claim them the same way.

#### Handling Blockers

When you hit a blocker during an issue, do not guess — choose the appropriate response:

- **Time-based or external dependency that resolves later** (e.g., waiting for a deploy, an API key, a human action on a known schedule):
  ```
  bd defer <id> --until="<date>"
  ```
  Then continue with `bd ready` to pick up other available work.

- **Dependency on missing work** (another task must be completed first but no issue exists for it):
  ```
  bd create --title="<description of missing work>" --type=task
  bd dep add <blocked-id> <new-blocker-id>
  ```
  Then continue with `bd ready`. The original issue is now blocked and will not reappear until the blocker is closed.

- **Needs human input or decision** (ambiguous requirement, risk decision, access you cannot obtain):
  ```
  bd human <id>
  ```
  Describe what decision or input is needed in the issue comments, then continue with `bd ready` for other work or pause and ask.

### Step 3: Complete Development

After all issues complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice.

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker with no clear `bd defer`, `bd dep add`, or `bd human` resolution
- The epic has critical gaps preventing any start
- The issue brief is unclear → flag via `bd human <id>` and ask
- Verification fails repeatedly despite following the brief

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Inspect (Step 1) when:**
- Partner updates the epic or its child issues based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** — stop and ask.

## Remember
- Review the epic critically via `bd show <epic-id>` before starting
- Follow each issue's brief exactly
- Don't skip verifications
- Reference skills when the issue brief says to
- Stop when blocked, don't guess
- Handle blockers with `bd defer`, `bd dep add`, or `bd human` — never skip them
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superpowers:writing-plans** - Creates the epic + child issues this skill executes.
- **superpowers:finishing-a-development-branch** - Complete development after all issues close
