---
name: cherry-picking-across-branches
description: Use when backporting or forward-porting commits between long-lived branches (release, LTS, maintenance branches) - enforces scope analysis, correct ordering, target-context verification, and audit tracking before the picked code merges
---

# Cherry-Picking Across Long-Lived Branches

## Overview

`git cherry-pick` succeeds whenever the patch applies. Apply-clean is not the same as correct. Long-lived branches (release, LTS, maintenance) have diverged enough from the source branch that a clean apply can still ship broken behavior.

**Core principle:** scope the chain, pick in order, verify in the target's context, then propose the result through review — never push directly.

**Announce at start:** "I'm using the cherry-picking-across-branches skill to plan and verify this backport."

## When This Skill Applies

Trigger on:
- Backport requests ("backport X to release/...", "pick this fix into 1.x").
- Forward-port requests ("forward-port from release-3 to main").
- Any cross-branch pick where the source and target are both long-lived.

Do not trigger on:
- Merge or rebase requests.
- Picking onto a short-lived feature branch you just cut.
- Definition questions ("what does cherry-pick do?").

## Step 0: Confirm The Branches Are Long-Lived

Ask or verify which branches are involved and which is protected. If either branch is a short-lived feature branch, stop and use a normal merge or rebase instead. Long-lived means: release branches, LTS branches, maintenance branches, or `main` when picking back from a release line.

Claim a bead for the work before touching code:

```bash
bd create --type=task --title="Backport <summary> to <target-branch>" --description="<source SHA(s), reason, target>"
bd update <issue-id> --claim
```

## Step 1: Scope The Commit Chain

A single SHA is rarely the whole change. Before picking:

```bash
git log --oneline <source-branch> -- <paths-touched-by-fix>
git log --all --grep="<key term from the fix>"
git log --oneline <sha>^..<source-branch> -- <paths>
```

For each candidate, decide whether it is part of the same logical change:
- Original fix commit.
- Follow-up fixups (`fixup!`, `squash!`, "address review", "fix typo in <fix>").
- Dependent commits the fix relies on (refactors, helper additions, type changes).
- Test commits added separately.

Record the picked set on the bead before running any cherry-pick:

```bash
bd comment <issue-id> "Pick set (in order): <sha1> <subject>; <sha2> <subject>; ..."
```

If a dependency is too large to bring along, stop and discuss the alternatives (rewrite for the target branch, partial port, or decline) instead of force-fitting a partial pick.

## Step 2: Pick In Source Order

Cherry-pick chronologically as the commits appear on the source branch, oldest first. Out-of-order picks generate avoidable conflicts.

Branch off the target so the pick can be reviewed:

```bash
git fetch origin
git switch -c backport/<short-slug> origin/<target-branch>
```

Pick a range or list:

```bash
git cherry-pick -x <oldest-sha>^..<newest-sha>
# or for non-contiguous picks:
git cherry-pick -x <sha1> <sha2> <sha3>
```

Always pass `-x` so the original SHA is recorded in the commit message. This is the audit trail.

For a merge commit, pick with `-m 1` (or the correct parent number) only if the merge truly represents the change you want, and document the choice in the commit message:

```bash
git cherry-pick -x -m 1 <merge-sha>
```

If you cannot tell which parent to use, prefer picking the underlying commits individually instead of the merge.

## Step 3: Resolve Conflicts In The Target's Context

A clean apply does not prove correctness. A conflicting apply does not mean "pick the source side."

When conflicts appear:
- Read the surrounding code on the target branch, not just the conflict markers.
- Re-establish the **intent** of the source change in the target's structure. The line-level diff is a hint, not the answer.
- If the file has been refactored or moved on the target, port the change to the new shape.
- If a helper or type used on the source branch does not exist on the target, do not silently inline a different implementation. Either bring the helper as a separate commit (and record it in the pick set) or stop and discuss.

After conflict resolution, run:

```bash
git diff <target-branch>...HEAD -- <paths>
```

Read it as a reviewer would, with no memory of the source branch.

## Step 4: Verify In The Target's Context

Apply-clean is not enough. Run, in the target worktree:

```bash
<build command>
<unit test command>
<integration tests covering the changed area>
```

If the source branch added tests, those tests must run and pass on the target branch — not just compile. If they cannot run on the target (different framework version, missing dependency), bring the necessary plumbing as part of the pick set or stop.

Record the verification result on the bead:

```bash
bd comment <issue-id> "Backport verification on <target-branch>: <commands> -> <pass/fail>; picked SHAs: <list>."
```

## Step 5: Propose Through Review, Do Not Push

Long-lived branches are typically protected. Open a PR even if your local merge would succeed:

```bash
git push -u origin backport/<short-slug>
gh pr create --base <target-branch> --title "Backport: <summary> (<source-shas>)" --body "..."
```

The PR description should include:
- Source branch and original SHAs (the `-x` line is good but state it explicitly).
- Why the backport is needed.
- Any deviations from the source change and why.
- Verification commands run and their results.

Do not `git push` directly to the long-lived branch. Do not bypass branch protection. Do not skip review on a backport because "it already passed review on main" — the apply context is different.

## Step 6: Track Across Branches

For ongoing maintenance, keep an audit trail per long-lived branch so future backports can see what is already there:

- The `-x` trailer is the per-commit record.
- The bead is the per-task record.
- If the project tracks backports in a release-notes file or a label, update it as part of the PR.

When closing the bead:

```bash
bd close <issue-id> --reason="Backported <shas> to <target-branch>; PR <url>; verified <commands>."
```

## Common Mistakes

**Single-SHA picks of multi-commit changes**
- Problem: a "small fix" depends on an earlier refactor or a follow-up cleanup. Picking only the visible commit ships a half-broken change.
- Fix: scope the chain in Step 1; record the full pick set on the bead before picking.

**"It applied cleanly, ship it"**
- Problem: clean apply is a syntactic property. The target branch's behavior may still be wrong.
- Fix: run the full target-branch test suite covering the changed area, not just the picked tests.

**Cherry-picking a merge commit without -m**
- Problem: ambiguous parent selection produces a mangled diff or fails outright.
- Fix: prefer picking the underlying commits. If you must pick the merge, use `-m <parent>` and document why.

**Resolving conflicts by keeping source-side lines**
- Problem: drops the target branch's evolution, reintroduces fixed bugs, or breaks neighboring code.
- Fix: re-establish intent in the target's structure; read the surrounding code, not just the markers.

**Out-of-order picks**
- Problem: later commits conflict with state that earlier commits would have created.
- Fix: pick chronologically, oldest first, using `<oldest>^..<newest>` ranges when possible.

**Direct push to the long-lived branch**
- Problem: skips review, breaks audit trail, may bypass CI gating that branch protection enforces.
- Fix: always open a PR with `--base <target-branch>`, even for "obvious" backports.

**No audit trail**
- Problem: future backports re-pick the same commits, or assume something landed when it didn't.
- Fix: use `cherry-pick -x`, record the pick set on a bead, update any project-level backport tracking.

## Red Flags

Stop and reconsider when:
- You are about to pick a single SHA without searching for related commits.
- You are about to push to a long-lived branch without a PR.
- A conflict is resolved by taking the source-side hunk wholesale.
- The picked tests would not run on the target branch and you decide to skip them instead of bringing dependencies.
- A merge commit is being picked without `-m` and without a documented parent choice.
- No bead or audit record exists for the backport.

## Integration

Pairs with:
- `superpowers-beads:using-git-worktrees` — do the backport in an isolated worktree off the target branch.
- `superpowers-beads:verification-before-completion` — verification before closing the bead or merging the PR.
- `superpowers-beads:finishing-a-development-branch` — for the PR/merge/cleanup decision once the backport is verified.
