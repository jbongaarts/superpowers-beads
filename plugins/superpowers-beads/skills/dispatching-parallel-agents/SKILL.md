---
name: dispatching-parallel-agents
description: Use when facing 2 or more independent tasks, failures, or work domains that can proceed concurrently without shared state or sequential dependencies
---

# Dispatching Parallel Agents

## Overview

Parallel delegation is a beads workflow first and an agent workflow second.

**Core principle:** create one durable bead per independent work domain, validate the dependency graph, then dispatch one worker per ready bead.

Delegation requires host support and current-session permission. If delegation is not available, still use the beads structure to organize the work, then execute the ready beads locally or sequentially.

## When To Use

Use when:
- Two or more failures or tasks are independent.
- Each worker can succeed with a narrow issue brief.
- Write sets, test resources, or worktrees can be kept separate.
- The parent issue can be represented as an epic with child tasks.
- Dependencies are real blockers, not a preferred ordering.

Do not use when:
- A shared root cause is likely.
- Workers would edit the same files without clear ownership.
- The next local step is blocked on one specific answer.
- You need whole-system reasoning before decomposition.

## Step 1: Model The Work In Beads

**Prototype burst (4 sibling approaches, then synthesize):** if the goal is to explore N≈4 alternative implementations of the same problem and pick one, pour the formula instead of building the graph by hand:

```bash
bd mol pour superpowers-parallel-burst --var title="<investigation>" --var output_contract="<what each lane should return>"
```

This creates `frame → lane-1..lane-4 (parallel) → synthesize → verify → finish` with the right dependencies. Skip to Step 2.

**General parallel work** (N independent domains, no fixed shape): build the graph manually. Use an existing parent epic when one exists, otherwise create one:

```bash
bd create --type=epic --title="<parallel work goal>" --description="<what done means>"
bd update <epic-id> --claim
```

Create one child bead per independent domain:

```bash
bd create --type=task --parent=<epic-id> --title="<domain A>" --description="<focused scope, constraints, verification>"
bd create --type=task --parent=<epic-id> --title="<domain B>" --description="<focused scope, constraints, verification>"
bd create --type=task --parent=<epic-id> --title="<domain C>" --description="<focused scope, constraints, verification>"
```

Add dependencies only for true blockers:

```bash
bd dep add <blocked-id> <blocker-id>
```

Do not create dependencies to express "do this first" when the tasks can run in parallel.

## Step 2: Validate And Create The Swarm

Validate the graph before dispatch:

```bash
bd swarm validate <epic-id>
bd swarm create <epic-id>
bd swarm status <epic-id>
bd ready --parent <epic-id>
```

Fix cycles, missing blockers, vague child scopes, or disconnected work before assigning workers. `bd swarm status` is computed from beads, so it stays current as workers claim and close issues.

## Step 3: Dispatch Ready Beads

For each ready child:

```bash
bd show <child-id>
bd update <child-id> --claim
```

Dispatch with the child bead as the contract. The prompt should include:
- `bd show <child-id>` output.
- Files or modules the worker owns.
- Files or modules the worker must not touch.
- Verification commands to run.
- Requirement to record evidence with `bd comment`.
- Requirement to close with `bd close <child-id> --suggest-next` only after verification passes.

Worker prompt skeleton:

```markdown
You are responsible for bead <child-id>.

Scope:
- Own: <paths/domains>
- Avoid: <paths/domains owned by other workers>

Use beads as the source of truth:
1. Read the supplied `bd show <child-id>` brief.
2. Do the smallest change that satisfies this bead only.
3. Run <verification command>.
4. Record evidence:
   `bd comment <child-id> "Verification: <command> -> <result>."`
5. Close only when verified:
   `bd close <child-id> --suggest-next --reason="<summary>; verification passed."`

Return: changed files, verification output summary, bead status, and any follow-up beads created.
```

If multiple workers will edit the repository, use separate branches or `superpowers:using-git-worktrees` so write sets and test artifacts do not collide.

## Step 4: Review Returns

When a worker returns:

```bash
bd show <child-id>
bd swarm status <epic-id>
git status --short
<worker verification command, rerun or spot-check>
```

Review:
- Did the worker stay inside the bead scope?
- Is evidence recorded on the bead?
- Was `bd close <child-id> --suggest-next` used after verification?
- Did closing unblock more ready beads?
- Are there conflicts with other workers' changes?

If the worker did not close the bead, close it yourself only after verification:

```bash
bd comment <child-id> "Controller verification: <command> -> <result>."
bd close <child-id> --suggest-next --reason="<summary>; controller verification passed."
```

The `--suggest-next` output is the handoff point for the next parallel wave. Use it with `bd ready --parent <epic-id>` and `bd swarm status <epic-id>` before dispatching more workers.

## Step 5: Integrate The Swarm

After all child beads are closed:

```bash
bd swarm status <epic-id>
<full verification command>
bd comment <epic-id> "Swarm verification: <command> -> <result>; children closed=<ids>."
bd close <epic-id> --reason="<summary>; swarm verified."
```

Then use `superpowers:finishing-a-development-branch` to run preflight, commit, push, create the PR, wait for checks, and merge through the protected flow.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Dispatching raw tasks without beads | Create child beads first; each worker owns one bead. |
| Using dependencies as a schedule | Add `bd dep add` only for true blockers. |
| Giving workers the whole epic | Give each worker one focused `bd show <child-id>` brief. |
| Forgetting review after return | Inspect bead evidence and rerun or spot-check verification. |
| Closing in chat only | Use `bd close <child-id> --suggest-next` so the next wave is visible. |
| Parallel edits to same files | Split ownership or use sequential work for that area. |

## Red Flags

Stop and regroup when:
- You cannot name independent child beads.
- Two workers need the same file ownership.
- `bd swarm validate <epic-id>` reports cycles or disconnected work you cannot explain.
- A worker returns without verification evidence.
- You are about to dispatch another wave without checking `bd swarm status`.
