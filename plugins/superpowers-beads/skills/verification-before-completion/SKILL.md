---
name: verification-before-completion
description: Use when about to take an action that locks in a completion claim — committing, pushing, opening a PR, closing an issue, or telling the user work is done/fixed/passing. Do NOT trigger for code-reading, explaining code, or knowledge questions where no completion claim is being made.
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Beads rule:** Do not `bd close` an issue until the verification command output has been shown in the same turn and recorded on the issue.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not run the verification command in this message, you cannot claim it passes.

If you have not recorded verification on the bead, you cannot close it.

## The Gate Function

Before claiming any status, closing a bead, committing, pushing, opening a PR, or expressing satisfaction:

1. **IDENTIFY:** What command proves this claim?
2. **RUN:** Execute the full command fresh.
3. **READ:** Read the full output, exit code, and failure count.
4. **VERIFY:** Does output confirm the claim?
   - If no, state actual status with evidence.
   - If yes, state the claim with evidence.
5. **RECORD:** Add a concise verification comment to the relevant bead.
6. **ONLY THEN:** Close the bead or make the completion claim.

Skip any step and the work is not verified.

## Beads Completion Pattern

For every issue you close:

```bash
bd show <issue-id>
<verification command>
bd comment <issue-id> "Verification: <command> -> <exit code and key output summary>"
bd close <issue-id> --reason="<what was completed; verification: <command> passed>"
```

When the verification output is lengthy, show the important lines in your response and store a concise summary in beads. Do not hide failing output behind summaries.

Examples:

```bash
scripts/preflight.sh
bd comment superpowers-beads-abc "Verification: scripts/preflight.sh -> exit 0; validation passed."
bd close superpowers-beads-abc --reason="Ported skill; verification: scripts/preflight.sh passed."
```

```bash
go test ./...
bd comment superpowers-beads-def "Verification: go test ./... -> exit 1; TestFoo failed in pkg/bar."
# Do not close. Fix or create follow-up work.
```

## Common Claims and Required Evidence

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output with zero failures | Previous run, "should pass" |
| Linter clean | Linter output with zero errors | Partial check, extrapolation |
| Build succeeds | Build command exit 0 | Linter passing |
| Bug fixed | Original symptom reproduced and now passing | Code changed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff and verification command | Agent report |
| Requirements met | Requirement-by-requirement check | Tests passing alone |
| Bead complete | Verification comment plus close reason | Chat-only claim |

## Red Flags - Stop

- Using "should", "probably", or "seems to".
- Expressing satisfaction before verification.
- About to commit, push, PR, or `bd close` without verification.
- Trusting agent success reports without checking.
- Relying on partial verification.
- Thinking "just this once".
- Any wording implying success without fresh evidence.

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the verification |
| "I am confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter is not compiler/test coverage |
| "Agent said success" | Verify independently |
| "I am tired" | Exhaustion is not evidence |
| "Partial check is enough" | Partial proves little |
| "I will record it later" | Record before close |

## Key Patterns

### Tests

```text
Correct: Run test command, read "34 passed", then say "Tests pass: 34/34."
Wrong: "Should pass now."
```

### Regression Tests

```text
Correct: Write test -> run pass -> revert fix -> run fail -> restore fix -> run pass.
Wrong: "I wrote a regression test" without proving it fails without the fix.
```

### Build

```text
Correct: Run build, see exit 0, then claim build passes.
Wrong: Linter passed, therefore build is fine.
```

### Requirements

```text
Correct: Re-read issue acceptance criteria, verify each, report gaps or completion.
Wrong: Tests pass, therefore requirements are complete.
```

### Agent Delegation

```text
Correct: Agent reports success -> inspect diff -> run verification -> report actual state.
Wrong: Trust the agent report.
```

## When To Apply

Always before:
- Any success or completion claim.
- Any positive statement about work state.
- `bd close`.
- Commit, push, PR creation, or merge.
- Moving to the next issue.
- Delegating or accepting delegated work.

Rule applies to exact phrases, paraphrases, implications, and summaries.

## If Verification Cannot Run

Do not close the issue as complete. Instead:

1. Record what blocked verification:
   ```bash
   bd comment <issue-id> "Verification blocked: <command> could not run because <reason>."
   ```
2. Create a blocker or follow-up if needed:
   ```bash
   bd create --type=task --parent=<issue-id> \
     --title="Restore verification for <area>" \
     --description="<missing dependency, environment issue, or access requirement>"
   bd dep add <issue-id> <blocker-id>
   ```
3. Ask for help when the blocker requires human input.

## The Bottom Line

No shortcuts for verification.

Run the command. Read the output. Record the evidence. Then close the bead.
