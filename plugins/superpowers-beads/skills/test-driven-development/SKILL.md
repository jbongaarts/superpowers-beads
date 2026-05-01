---
name: test-driven-development
description: Use when implementing any feature, bugfix, refactor, or behavior change before writing production code - enforces failing-test-first development and records RED/GREEN/REFACTOR evidence in beads
---

# Test-Driven Development

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Then refactor while staying green.

**Core principle:** if you did not watch the test fail for the expected reason, you do not know whether the test proves the behavior.

## When To Use

Use for:
- New features
- Bug fixes
- Refactoring
- Behavior changes

Ask the human partner before skipping TDD for throwaway prototypes, generated code, or configuration-only changes.

## Iron Law

```text
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If production code was written before the test, delete or discard it before starting the TDD cycle. Keeping it as a reference turns TDD into tests-after.

## Beads Tracking

Use the existing work bead as the source of truth.

For non-trivial work, create child beads for the cycle:

```bash
bd create --type=task --parent=<work-id> --title="RED: <behavior>" --description="Write the failing test and record the expected failure."
bd create --type=task --parent=<work-id> --title="GREEN: <behavior>" --description="Implement the smallest code change that passes the RED test."
bd create --type=task --parent=<work-id> --title="REFACTOR: <behavior>" --description="Clean up while keeping the test suite green."
bd dep add <green-id> <red-id>
bd dep add <refactor-id> <green-id>
```

Claim and close those child beads as the cycle progresses. Record command evidence on the relevant child bead:

```bash
bd comment <red-id> "RED verification: <test command> -> failed for expected reason: <summary>."
bd comment <green-id> "GREEN verification: <test command> -> passed."
bd comment <refactor-id> "REFACTOR verification: <test command> -> still passed."
```

For small work where child beads would add noise, keep the cycle on the existing bead:

```bash
bd comment <work-id> "TDD evidence: RED <command> failed as expected; GREEN <command> passed; REFACTOR <command> still passed."
```

Do not use markdown checklists or in-session todo lists for TDD state.

## The Cycle

### 1. RED: Write One Failing Test

Write one minimal test that states the desired behavior.

Good tests:
- Have a name that describes behavior.
- Exercise real code, with mocks only when unavoidable.
- Test one behavior at a time.
- Show the intended API or user outcome.

Run only the focused test first:

```bash
<test command for the focused test>
```

Confirm:
- The test fails.
- The failure is expected.
- The failure is because behavior is missing, not because of typos or setup errors.

If it passes immediately, it is not a useful RED test. Fix the test or choose a missing behavior.

### 2. GREEN: Minimal Code

Write the smallest production code that passes the failing test.

Do not:
- Add extra features.
- Refactor unrelated code.
- Broaden scope beyond the test.
- Change the test to fit the implementation unless the test itself is wrong.

Run the focused test again, then the relevant nearby suite:

```bash
<focused test command>
<nearby suite command>
```

Fix production code until both pass.

### 3. REFACTOR: Clean Up

Only refactor after GREEN.

Allowed refactors:
- Improve names.
- Remove duplication.
- Extract helpers.
- Simplify structure without changing behavior.

Run the same verification after refactoring. If it fails, fix the refactor or revert it.

## Bug Fix Pattern

For a bug, the RED test reproduces the bug:

```text
1. Write a test that fails with the current bug.
2. Verify it fails for the bug, not setup noise.
3. Fix the bug minimally.
4. Verify the test now passes.
5. Run the regression-relevant suite.
```

Never fix a bug without a regression test unless the human partner explicitly accepts the risk.

## When Existing Tests Are Missing

Add the smallest useful test harness around the behavior being changed. If the existing design makes testing difficult, treat that as design feedback and simplify the seam before implementing behavior.

If the test harness setup becomes larger than the behavior under test, pause and reassess the interface.

## Testing Anti-Patterns

When adding mocks, test utilities, or test-only hooks, read `testing-anti-patterns.md`.

Load it before:
- Asserting on mocks.
- Adding production methods only used by tests.
- Mocking high-level dependencies.
- Creating partial mock API responses.

## Completion Gate

Before closing the work bead:

```bash
<full verification command>
bd comment <work-id> "Verification: <command> -> passed; TDD evidence recorded in <child ids or parent comment>."
bd close <work-id> --reason="<summary>; verification passed; TDD evidence recorded."
```

Do not close a bead if:
- The RED failure was never observed.
- The failure reason was not checked.
- The GREEN run was not observed.
- Refactor verification is missing.
- Tests pass only by testing mocks rather than behavior.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test is usually small. |
| "I'll test after" | Tests-after prove what you built, not what you needed. |
| "I already manually tested" | Manual checks are not repeatable regression coverage. |
| "Keep the code as reference" | That is tests-after. Discard and start from the test. |
| "Test is hard" | The interface may be unclear or too coupled. Improve it. |

## Red Flags

Stop when:
- Production code appears before a failing test.
- A test passes immediately.
- You cannot explain the failure.
- You are changing tests to match implementation.
- You are about to close a bead without recorded TDD evidence.

## Integration

Pairs with:
- `superpowers:systematic-debugging` for root-cause bug investigation before the RED test.
- `superpowers:verification-before-completion` before closing beads or creating PRs.
- `superpowers:finishing-a-development-branch` after TDD evidence and verification are recorded.
