---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Persistent state:** Every debugging session is tracked in `bd` so evidence, hypotheses, failed attempts, and lessons survive compaction, restart, and handoff.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you have not completed Phase 1 and recorded the evidence in beads, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

Use this especially when:
- Under time pressure
- "Just one quick fix" seems obvious
- You have already tried multiple fixes
- A previous fix did not work
- You do not fully understand the issue

## Beads Setup

At the start of Phase 1, create or claim a bug issue:

```bash
bd create --type=bug \
  --title="<short symptom>" \
  --description="<observed behavior, expected behavior, and reproduction entry point>"
bd update <bug-id> --claim
```

If you are debugging inside an existing feature epic or task, make the bug a child of that parent:

```bash
bd create --type=bug --parent=<parent-id> \
  --title="<short symptom>" \
  --description="<observed behavior, expected behavior, and reproduction entry point>"
```

Record every durable finding on the bug issue:

```bash
bd update <bug-id> --append-notes="Evidence: <command, output summary, files, line refs>"
bd update <bug-id> --append-notes="Hypothesis: <root cause theory and why>"
bd update <bug-id> --append-notes="Result: <test performed and outcome>"
```

When the root cause teaches a reusable lesson about the project, persist it:

```bash
bd remember "<short reusable lesson>" --key <topic>
```

Close the bug issue only after Phase 4 verification passes:

```bash
bd close <bug-id> --reason="<root cause and verified fix summary>"
```

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Do not skip past errors or warnings.
   - Read stack traces completely.
   - Note line numbers, file paths, error codes, and exact command output.
   - Record the relevant evidence with `bd update <bug-id> --append-notes`.

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible, gather more data. Do not guess.

3. **Check Recent Changes**
   - What changed that could cause this?
   - Check `git diff`, recent commits, dependency changes, config changes, and environment differences.
   - Record candidate change points in the bug notes.

4. **Gather Evidence in Multi-Component Systems**

   When a system has multiple components, add diagnostic instrumentation before proposing fixes:

   ```text
   For each component boundary:
   - Log what data enters the component.
   - Log what data exits the component.
   - Verify environment and config propagation.
   - Check state at each layer.
   ```

   Run once to gather evidence showing where it breaks, then analyze that evidence to identify the failing component.

5. **Trace Data Flow**

   When the error is deep in a call stack:
   - Where does the bad value originate?
   - What called this with the bad value?
   - Keep tracing backward until you find the source.
   - Fix at source, not at symptom.

   See `root-cause-tracing.md` in this directory for the complete backward tracing technique.

**Phase 1 completion gate:** The bug issue has notes covering the symptom, reproduction, recent changes, and evidence showing where the fault originates or what remains unknown.

### Phase 2: Pattern Analysis

Find the pattern before fixing:

1. **Find Working Examples**
   - Locate similar working code in the same codebase.
   - Record the relevant files and behavior in the bug notes.

2. **Compare Against References**
   - If implementing a pattern, read the reference implementation completely.
   - Do not skim. Understand the pattern before applying it.

3. **Identify Differences**
   - List every difference between working and broken behavior.
   - Do not assume small differences cannot matter.

4. **Understand Dependencies**
   - What other components, settings, config, environment, or assumptions does this need?

**Phase 2 completion gate:** The bug issue explains the working reference, the broken case, and the meaningful differences.

### Phase 3: Hypothesis and Testing

Use the scientific method:

1. **Form a Single Hypothesis**
   - State clearly: "I think X is the root cause because Y."
   - Record it in the bug notes.

2. **Test Minimally**
   - Make the smallest possible change to test the hypothesis.
   - One variable at a time.
   - Do not fix multiple things at once.

3. **Verify Before Continuing**
   - If it worked, proceed to Phase 4.
   - If it did not work, record the result and form a new hypothesis.
   - Do not stack more fixes on top.

4. **When You Do Not Know**
   - Say "I do not understand X."
   - Research more or ask for help.
   - Do not pretend certainty.

**Phase 3 completion gate:** The bug issue records a confirmed root-cause hypothesis, including the evidence that confirmed it.

### Phase 4: Implementation

Fix the root cause, not the symptom:

1. **Create Failing Test Case**
   - Simplest possible reproduction.
   - Automated test if possible.
   - One-off test script if no framework exists.
   - MUST exist before fixing.
   - Use `superpowers:test-driven-development` for writing proper failing tests.

2. **Implement Single Fix**
   - Address the confirmed root cause.
   - One change at a time.
   - No "while I am here" improvements.
   - No bundled refactoring.

3. **Verify Fix**
   - Test passes now.
   - No other tests broke.
   - Original issue is actually resolved.
   - Record commands and outcomes in the bug notes.

4. **If Fix Does Not Work**
   - Stop.
   - Count how many fixes have been tried.
   - If fewer than three, return to Phase 1 with the new evidence.
   - If three or more, stop and question the architecture before attempting another fix.

5. **If 3+ Fixes Failed: Question Architecture**

   The pattern may be fundamentally wrong when:
   - Each fix reveals new shared state, coupling, or problems elsewhere.
   - Fixes require large refactoring to implement.
   - Each fix creates new symptoms elsewhere.

   Discuss the architecture with your human partner before attempting more fixes. Create follow-up beads for architecture work if needed:

   ```bash
   bd create --type=task --parent=<bug-or-epic-id> \
     --title="Rework architecture for <problem>" \
     --description="<why repeated fixes failed and what decision is needed>"
   ```

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I will manually verify"
- "It is probably X, let me fix that"
- "I do not fully understand but this might work"
- "Pattern says X but I will adapt it differently"
- "Here are the main problems" before investigation
- "One more fix attempt" after two failures

Stop. Return to Phase 1 and record what you know in the bug issue.

## Human Partner Signals

When your human partner says:
- "Is that not happening?"
- "Will it show us...?"
- "Stop guessing"
- "Ultrathink this"
- "We're stuck?"

Stop and return to Phase 1. Add evidence-gathering steps to the bug issue before continuing.

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|----------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Bug issue explains what and where |
| **2. Pattern** | Find working examples, compare | Bug issue lists meaningful differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed root cause recorded |
| **4. Implementation** | Create test, fix, verify | Bug closed with verified fix summary |

## When Process Reveals "No Root Cause"

If systematic investigation reveals the issue is truly environmental, timing-dependent, or external:

1. Document what you investigated in the bug issue.
2. Implement appropriate handling, such as retry, timeout, or a clear error message.
3. Add monitoring or logging for future investigation.
4. Store the reusable lesson with `bd remember --key <topic>`.

Most "no root cause" cases are incomplete investigation. Be skeptical.

## Supporting Techniques

These techniques are part of systematic debugging and available in this directory:

- `root-cause-tracing.md` - Trace bugs backward through call stack to find original trigger.
- `defense-in-depth.md` - Add validation at multiple layers after finding root cause.
- `condition-based-waiting.md` - Replace arbitrary timeouts with condition polling.

Related skills:
- `superpowers:test-driven-development` - For creating failing test case in Phase 4.
- `superpowers:verification-before-completion` - Verify fix worked before claiming success.
