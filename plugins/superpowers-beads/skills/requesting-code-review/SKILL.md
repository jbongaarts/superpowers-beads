---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Dispatch a focused reviewer to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation, not your session history.

**Core principle:** Review early, review often, and persist the result in beads.

## When to Request Review

Mandatory:
- After each task in subagent-driven development.
- After completing a major feature.
- Before merge to `main`.

Optional but valuable:
- When stuck and needing a fresh perspective.
- Before refactoring, to establish a baseline.
- After fixing a complex bug.

## Beads State

Identify the issue or epic being reviewed:

```bash
bd show <issue-id>
```

If there is no parent issue for the work, create one:

```bash
bd create --type=task \
  --title="Review <change>" \
  --description="<what changed, branch or PR, and intended outcome>"
```

After the reviewer responds, store the review summary on the issue:

```bash
bd comment <issue-id> --stdin
```

Use this comment shape:

```markdown
Code review summary for `<base-sha>..<head-sha>`:

Assessment: <Ready to merge | With fixes | Not ready>

Critical:
- <item or none>

Important:
- <item or none>

Minor:
- <item or none>

Follow-up:
- <child issue IDs created, or none>
```

If review feedback requires work, use `superpowers:receiving-code-review` to evaluate it and create child tasks for accepted items.

When review follow-up tasks close, surface newly unblocked work:

```bash
bd close <review-task-id> --suggest-next
```

## How to Request

### 1. Get Git SHAs

Choose the correct base for the work under review:

```bash
BASE_SHA=$(git merge-base origin/main HEAD)
HEAD_SHA=$(git rev-parse HEAD)
```

For task-by-task review, use the previous task commit or the issue's starting SHA if recorded:

```bash
BASE_SHA=<task-start-sha>
HEAD_SHA=$(git rev-parse HEAD)
```

### 2. Gather Beads Context

```bash
bd show <issue-id>
bd list --parent <issue-id> --long
```

Use the issue's description, design, acceptance criteria, and child issue state as the plan/requirements context.

### 3. Dispatch Reviewer

Use the platform's reviewer/subagent mechanism when available. Fill the template at `code-reviewer.md`.

Placeholders:
- `{WHAT_WAS_IMPLEMENTED}` - What you just built.
- `{PLAN_REFERENCE}` - `bd show <issue-id>` output, acceptance criteria, and any relevant child issues.
- `{BASE_SHA}` - Starting commit.
- `{HEAD_SHA}` - Ending commit.
- `{DESCRIPTION}` - Brief summary.
- `{ISSUE_ID}` - Bead receiving the review comment.

### 4. Persist and Act

After review:

1. Add the review summary as a `bd comment <issue-id>`.
2. Fix Critical issues immediately.
3. Fix Important issues before proceeding.
4. Note Minor issues as child tasks if they are real work.
5. Push back if reviewer is wrong, with technical reasoning recorded in the issue comment.

## Example

```bash
BASE_SHA=$(git merge-base origin/main HEAD)
HEAD_SHA=$(git rev-parse HEAD)
bd show superpowers-beads-abc
```

Dispatch reviewer with:

```text
WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index.
PLAN_REFERENCE: superpowers-beads-abc, including acceptance criteria and child tasks.
BASE_SHA: a7981ec
HEAD_SHA: 3df7661
DESCRIPTION: Added verifyIndex() and repairIndex() with four issue types.
ISSUE_ID: superpowers-beads-abc
```

Reviewer returns:

```text
Assessment: With fixes
Important: Missing progress indicators
Minor: Magic number for reporting interval
```

Persist it:

```bash
bd comment superpowers-beads-abc "Code review summary for a7981ec..3df7661: Assessment: With fixes. Important: Missing progress indicators. Minor: Magic number for reporting interval."
```

Then use `superpowers:receiving-code-review` to create follow-up child tasks or record pushback.

## Integration with Workflows

**Subagent-Driven Development**
- Review after each task.
- Persist review summary as a comment on the task or epic.
- Fix before moving to the next issue.

**Executing Plans**
- Review after each batch.
- Persist review summary on the epic.
- Create child tasks for accepted feedback.

**Ad-Hoc Development**
- Review before merge.
- Review when stuck.
- Store the review on the issue that owns the branch.

## Red Flags

Never:
- Skip review because "it is simple".
- Ignore Critical issues.
- Proceed with unfixed Important issues.
- Keep review feedback only in chat.
- Close the reviewed issue without recording the review result.

If the reviewer is wrong:
- Push back with technical reasoning.
- Show code or tests that prove it works.
- Request clarification if needed.
- Record the reasoning in `bd comment`.

See template at: `requesting-code-review/code-reviewer.md`
