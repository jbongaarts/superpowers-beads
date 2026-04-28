---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Code Review Reception

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

**Persistent state:** Review evaluations and follow-up work live in `bd`, not hidden chat history.

## Beads Workflow

Identify the parent issue, epic, or PR-tracking bead for the work under review. If none exists, create one:

```bash
bd create --type=task \
  --title="Address review feedback for <change>" \
  --description="<review source, PR/commit, and review summary>"
```

For each review item:

1. Add an evaluation comment to the parent:
   ```bash
   bd comment <parent-id> "Review item <n>: <feedback>. Evaluation: <accepted|rejected|needs clarification>. Reason: <technical reason>."
   ```
2. If accepted and still needs work, create a child task:
   ```bash
   bd create --type=task --parent=<parent-id> \
     --title="Review item <n>: <short fix>" \
     --description="<requirement, code refs, implementation notes, and verification command>"
   ```
3. If unclear, do not implement. Add a comment with the exact question and ask the human partner.
4. If rejected, add the technical reason as a comment and do not create work.

Use dependencies when one review item must be resolved before another:

```bash
bd dep add <later-review-task-id> <earlier-review-task-id>
```

## The Response Pattern

When receiving code review feedback:

1. **READ:** Complete feedback without reacting.
2. **UNDERSTAND:** Restate the requirement in your own words or ask.
3. **VERIFY:** Check against codebase reality.
4. **EVALUATE:** Decide whether it is technically sound for this codebase.
5. **RECORD:** Add the evaluation to `bd comment <parent-id>`.
6. **IMPLEMENT:** Create and execute one child task at a time, testing each.

## Forbidden Responses

Never:
- "You're absolutely right!"
- "Great point!" or "Excellent feedback!"
- "Let me implement that now" before verification.

Instead:
- Restate the technical requirement.
- Ask clarifying questions.
- Push back with technical reasoning if wrong.
- Create beads for accepted work and start executing them.

## Handling Unclear Feedback

If any item is unclear:

```text
STOP - do not implement anything yet.
Record the unclear item as a bd comment.
Ask for clarification on the unclear items.
```

Why: items may be related. Partial understanding produces wrong implementation.

Example:

```text
Human partner: "Fix 1-6"
You understand 1,2,3,6. Unclear on 4,5.

Correct response:
"I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

Also record:

```bash
bd comment <parent-id> "Review items 4 and 5 need clarification before implementation: <specific questions>."
```

## Source-Specific Handling

### From Your Human Partner

- Trusted, but still verify scope and details.
- Ask if scope is unclear.
- No performative agreement.
- Skip to action or use a technical acknowledgment.

### From External Reviewers

Before implementing:

1. Check whether the suggestion is technically correct for this codebase.
2. Check whether it breaks existing functionality.
3. Check the reason for the current implementation.
4. Check platform and version compatibility.
5. Check whether the reviewer has full context.

If the suggestion seems wrong, push back with technical reasoning and record the evaluation:

```bash
bd comment <parent-id> "Review item <n> rejected: <suggestion> would <breakage/reason>. Evidence: <files/tests>."
```

If you cannot easily verify, say what is missing and ask whether to investigate, ask the reviewer, or proceed.

If it conflicts with the human partner's prior decisions, stop and discuss with the human partner first.

## YAGNI Check

If a reviewer suggests "implementing properly":

```bash
rg "<endpoint|function|feature name>"
```

If unused, ask whether to remove the unused feature instead. If used, implement it properly.

Record the result:

```bash
bd comment <parent-id> "Review item <n> YAGNI check: <used|unused>. Decision: <fix|remove|defer>."
```

## Implementation Order

For multi-item feedback:

1. Clarify anything unclear first.
2. Create child tasks for accepted work.
3. Order child tasks by:
   - Blocking issues: breakage, security, data loss.
   - Simple fixes: typos, imports, obvious local corrections.
   - Complex fixes: refactoring, behavior changes, architecture.
4. Test each fix individually.
5. Verify no regressions before closing each child task.

## When To Push Back

Push back when:
- Suggestion breaks existing functionality.
- Reviewer lacks full context.
- Suggestion violates YAGNI.
- Suggestion is technically incorrect for this stack.
- Legacy or compatibility reasons exist.
- It conflicts with architectural decisions.

How to push back:
- Use technical reasoning, not defensiveness.
- Ask specific questions.
- Reference working tests and code.
- Involve the human partner when architectural.
- Record the reasoning in `bd comment`.

## Acknowledging Correct Feedback

When feedback is correct:

```text
"Fixed. <brief description of what changed>"
"Verified this and implemented <specific fix> in <location>."
```

Avoid gratitude and performative agreement. The fix and verification are the acknowledgment.

If you pushed back and were wrong:

```text
"You were right - I checked <X> and it does <Y>. Implementing now."
"Verified this and you're correct. My initial understanding was wrong because <reason>. Fixing."
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One child task at a time, test each |
| Assuming reviewer is right | Check whether it breaks things |
| Avoiding pushback | Technical correctness over comfort |
| Partial implementation | Clarify all items first |
| Can't verify, proceed anyway | State limitation and ask |

## GitHub Thread Replies

When replying to inline review comments on GitHub, reply in the comment thread:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment-id}/replies \
  --method POST \
  --field body="<technical response>"
```

Do not reply to inline review comments as a top-level PR comment.

## Completion

Before closing the parent review issue:

1. Every review item has an evaluation comment.
2. Every accepted item has a child task or a comment explaining why no code was needed.
3. Every child task is closed after its verification passes.
4. Any rejected item has a technical reason and evidence.
5. Any unclear item has an explicit question for the human partner.

Then close the parent:

```bash
bd close <parent-id> --reason="All review feedback evaluated; accepted items implemented and verified."
```

## The Bottom Line

External feedback is input to evaluate, not orders to follow.

Verify. Question. Record. Then implement.
