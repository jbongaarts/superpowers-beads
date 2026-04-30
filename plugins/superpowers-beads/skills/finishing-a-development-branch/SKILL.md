---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Finishing a Development Branch

## Overview

Guide completion of development work by verifying evidence, checking beads hygiene, and integrating through the appropriate branch workflow.

**Core principle:** Verify tests -> run beads preflight -> present options -> execute choice -> clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Work

Use `superpowers:verification-before-completion` before any completion claim.

Run the project-specific verification commands fresh:

```bash
<test command>
<lint command>
<build or validation command>
```

If any verification fails:

```text
Verification failed. Cannot proceed with merge or PR.

<show failing command and key output>
```

Stop. Fix the issue or create a follow-up blocker bead.

### Step 2: Run Beads Preflight

Run beads hygiene checks before integration. If the repo defines its own preflight script (e.g. `scripts/preflight.sh`), prefer that — it bundles the project-specific gates plus the beads checks. Otherwise fall back to the bd commands directly:

```bash
scripts/preflight.sh   # if the repo provides one
# or, when no project-specific script exists:
bd preflight
bd orphans
bd stale
bd list --status=in_progress
```

`bd preflight --check` ships a default checklist tuned for Go/Nix projects; if it reports non-applicable checks, record that explicitly and run the applicable commands from its printed checklist manually rather than treating the whole step as failed.

Block merge or PR creation when:
- There are orphaned issues that affect this work.
- Stale issues need triage before handoff.
- In-progress issues are left claimed unintentionally.
- A completed issue lacks verification evidence.
- The branch has uncommitted changes that should be part of the work.

Resolve hygiene issues before proceeding:

```bash
bd close <completed-id> --reason="<verified completion summary>"
bd update <still-active-id> --append-notes="<handoff or blocker>"
bd create --type=task --parent=<epic-id> --title="<follow-up>" --description="<remaining work>"
```

### Step 3: Determine Base Branch

```bash
git branch --show-current
git status --short --branch
git merge-base HEAD origin/main
```

Default to `main` unless the issue or human partner names a different base branch.

### Step 4: Present Options

Present exactly these options:

```text
Implementation verified and beads preflight checked. What would you like to do?

1. Push branch and create a Pull Request
2. Merge back to <base-branch> locally
3. Keep the branch as-is
4. Discard this work

Which option?
```

For protected `main`, recommend option 1.

### Step 5: Execute Choice

#### Option 1: Push and Create PR

```bash
git push -u origin <feature-branch>
gh pr create --base <base-branch> --head <feature-branch> \
  --title "<title>" \
  --body "<summary, verification, and beads IDs>"
gh pr checks <pr-number> --watch
```

If required checks pass and policy permits merge:

```bash
gh pr merge <pr-number> --squash --delete-branch
```

After merge:

```bash
git status --short --branch
bd dolt push
```

If no Dolt remote is configured, record that it skipped. The `.beads/issues.jsonl` changes still travel through git.

#### Option 2: Merge Locally

Only use this when branch protection does not require PRs or the human partner explicitly asks for local merge.

```bash
git switch <base-branch>
git pull --rebase
git merge --ff-only <feature-branch> || git merge <feature-branch>
<test command>
bd preflight --check
git push
git branch -d <feature-branch>
```

Do not merge locally if verification or beads preflight fails.

#### Option 3: Keep As-Is

Report:

```text
Keeping branch <feature-branch>. Current state:
<git status --short --branch>
```

Do not clean up the branch or worktree.

#### Option 4: Discard

Confirm first:

```text
This will permanently delete:
- Branch <feature-branch>
- Commits: <commit-list>
- Worktree at <path, if any>

Type 'discard' to confirm.
```

Wait for exact confirmation. If confirmed:

```bash
git switch <base-branch>
git branch -D <feature-branch>
```

Only remove a worktree after confirmation.

### Step 6: Cleanup Worktree

For merged or discarded branches, check whether this is a separate worktree:

```bash
bd worktree list
```

Remove only the completed feature worktree:

```bash
bd worktree remove <worktree-path>
```

For option 3, keep the worktree.

## Quick Reference

| Option | Merge | Push | PR | Keep Worktree | Cleanup Branch |
|--------|-------|------|----|---------------|----------------|
| 1. Create PR | via PR | yes | yes | usually yes | after merge |
| 2. Merge locally | yes | yes | no | no | yes |
| 3. Keep as-is | no | no | no | yes | no |
| 4. Discard | no | no | no | no | force delete |

## Common Mistakes

**Skipping verification**
- Problem: creates failing PRs or broken merges.
- Fix: run verification before offering options.

**Skipping beads preflight**
- Problem: stale, orphaned, or in-progress beads hide handoff gaps.
- Fix: run `bd preflight`, `bd orphans`, `bd stale`, and `bd list --status=in_progress`.

**Creating PR with unresolved beads**
- Problem: review cannot tell what remains.
- Fix: create follow-up child tasks or close verified work first.

**Automatic cleanup**
- Problem: removes branch/worktree while PR still needs changes.
- Fix: cleanup only after merge or confirmed discard.

**No confirmation for discard**
- Problem: deletes work accidentally.
- Fix: require typed `discard` confirmation.

## Red Flags

Never:
- Proceed with failing verification.
- Merge or PR with unresolved beads hygiene issues.
- Delete work without confirmation.
- Force-push without explicit request.
- Claim the branch is complete without showing verification output.

Always:
- Use `superpowers:verification-before-completion`.
- Record verification on the relevant bead.
- Run beads preflight before integration.
- Prefer PR flow for protected `main`.
- Confirm destructive actions.

## Integration

Called by:
- `superpowers:subagent-driven-development` after all issues close.
- `superpowers:executing-plans` after all ready issues complete.

Pairs with:
- `superpowers:using-git-worktrees` for worktree cleanup.
- `superpowers:verification-before-completion` for evidence before closing.
