---
name: using-git-worktrees
description: Use when starting feature work that needs an isolated workspace, dispatching parallel agents, or executing an implementation plan - creates a bd-managed worktree and claims the underlying issue before work starts
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Using Git Worktrees

## Overview

Create isolated workspaces with `bd worktree`, not raw `git worktree`.

**Core principle:** claim the bead first, create the worktree through `bd`, verify the isolated baseline, then start work.

**Announce at start:** "I'm using the using-git-worktrees skill to set up a bd-managed worktree."

## Step 0: Detect Current State

First confirm beads is usable. If `bd` is missing or no beads workspace is active, follow the fallback rules in `superpowers:using-superpowers` (do not auto-install or auto-init). This skill cannot create a bd-managed worktree without both — only continue if the user explicitly wants a non-beads worktree fallback.

Then check whether you are already in a linked worktree:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
git branch --show-current
bd worktree info
```

If `GIT_DIR` differs from `GIT_COMMON`, you are already in a linked worktree. Do not create a nested worktree. Claim the bead and continue there unless the user explicitly asks for another workspace.

If the branch is empty, you are on a detached HEAD. Do not create branches or PRs until the environment is clarified.

## Step 1: Resolve And Claim The Bead

Every worktree needs a bead that owns the work.

If an issue ID is provided:

```bash
bd show <issue-id>
bd update <issue-id> --claim
```

If no issue exists yet, create one before creating the worktree:

```bash
bd create --type=task --title="<work summary>" --description="<why this work exists and what done means>"
bd update <new-issue-id> --claim
```

Do not create the worktree before the issue is claimed. This prevents untracked, ownerless work.

## Step 2: Choose Name, Path, And Branch

Use a short slug based on the bead or feature:

```text
Issue: superpowers-beads-abc
Slug: superpowers-beads-abc
Branch: work/superpowers-beads-abc
Path: .worktrees/superpowers-beads-abc
```

Path selection:
- Use the user-provided path if one was given.
- Otherwise prefer `.worktrees/<slug>` for project-local worktrees.
- If the repo already has a documented worktree location, use that convention.

`bd worktree create` adds an in-repo worktree path to `.gitignore` when needed and shares the same beads database automatically. If `.gitignore` changes, include that change in the branch.

## Step 3: Create The Worktree

Create with `bd worktree create`:

```bash
bd worktree create .worktrees/<slug> --branch work/<slug>
cd .worktrees/<slug>
bd worktree info
bd show <issue-id>
```

Do not use `git worktree add` for normal skill flow. It bypasses the beads-specific setup and safety behavior.

## Step 4: Run Project Setup

Auto-detect setup commands from project files:

```bash
if [ -f package.json ]; then npm install; fi
if [ -f Cargo.toml ]; then cargo build; fi
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ] && command -v poetry >/dev/null 2>&1; then poetry install; fi
if [ -f go.mod ]; then go mod download; fi
```

Use the repo's documented setup command when it exists. Do not install dependencies blindly when the environment or package manager is unclear.

## Step 5: Verify Clean Baseline

Run the relevant baseline checks before implementation:

```bash
<test command>
<lint command>
<build or validation command>
```

If checks fail, report the failing command and key output, then ask whether to investigate the baseline failure or continue with known failing checks. Record the baseline status on the bead:

```bash
bd comment <issue-id> "Worktree baseline: <commands run>; <pass/fail summary>."
```

## Step 6: Report Ready State

Report:

```text
Worktree ready at <path>
Branch: <branch>
Bead: <issue-id> claimed
Baseline: <commands and result>
```

Then start implementation in the worktree.

## Cleanup

Use `bd worktree` for cleanup:

```bash
bd worktree list
bd worktree remove <path-or-name>
```

Only remove a worktree after the work is merged, explicitly discarded, or the user confirms cleanup. Use `--force` only after explicit confirmation because it skips safety checks.

## Common Mistakes

**Using raw git worktree commands**
- Problem: bypasses beads-aware setup and safety checks.
- Fix: use `bd worktree create`, `bd worktree list`, and `bd worktree remove`.

**Creating the worktree before claiming**
- Problem: work starts without an owner in beads.
- Fix: `bd update <issue-id> --claim` first.

**Skipping baseline verification**
- Problem: later failures are ambiguous.
- Fix: run and record the baseline checks before implementation.

**Creating nested worktrees**
- Problem: confusing branch and database behavior.
- Fix: compare `git rev-parse --git-dir` and `--git-common-dir` first.

**Ignoring .gitignore changes**
- Problem: worktree paths can appear as uncommitted setup changes.
- Fix: inspect `.gitignore` after `bd worktree create` and commit intentional changes.

## Red Flags

Never:
- Use `git worktree add` or `git worktree remove` for normal flow.
- Start isolated work without a claimed bead.
- Create a nested worktree.
- Skip baseline verification.
- Force-remove a worktree without explicit confirmation.

Always:
- Announce this skill.
- Claim the bead before creating the worktree.
- Use `bd worktree create`.
- Run `bd worktree info` inside the new worktree.
- Record baseline verification on the bead.

## Integration

Called by:
- `superpowers:brainstorming` when approved design moves to implementation.
- `superpowers:subagent-driven-development` before dispatching workers.
- `superpowers:executing-plans` before implementation starts.

Pairs with:
- `superpowers:finishing-a-development-branch` for PR, merge, and cleanup.
