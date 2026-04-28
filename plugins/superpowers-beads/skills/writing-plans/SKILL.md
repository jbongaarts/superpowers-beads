---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Writing Plans

## Overview

Create a beads-native implementation plan: an approved feature epic with child issues for the bite-sized implementation tasks. The beads graph is the source of truth. Markdown files are optional generated exports for human review, never the authoritative plan.

Write the plan assuming the engineer has zero context for the codebase and uneven test-design judgment. Document everything they need to know: files to touch, code to write, commands to run, expected test results, and commit points. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create a beads-native implementation plan."

**Context:** This should be run in a dedicated worktree created by brainstorming or the git-worktree workflow.

**Source of truth:** `bd` issue data:
- Feature scope, architecture, and acceptance criteria live on the epic created by brainstorming, or on a new epic if no approved epic exists yet.
- Implementation steps live on child issues.
- Ordering lives in dependencies.
- Follow-up discoveries become new child issues or dependencies.

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it was not, suggest breaking it into separate epics, one per subsystem. Each epic should produce working, testable software on its own.

## File Structure

Before creating child issues, map out which files will be created or modified and what each one is responsible for. Record this in the epic's `--design` field.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large files that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, do not unilaterally restructure, but if a file you are modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each child issue should produce self-contained changes that make sense independently.

## Epic Structure

If brainstorming already created an approved feature epic, use that epic and update missing fields instead of creating a duplicate:

```bash
bd show <epic-id>
bd update <epic-id> \
  --design="[Architecture, file map, boundaries, and tradeoffs]" \
  --acceptance="[Top-level completion criteria and final verification commands]"
```

If no approved feature epic exists, create one before creating implementation tasks:

```bash
bd create --type=epic \
  --title="[Feature Name]" \
  --description="[One-paragraph goal, scope, and user-visible outcome]" \
  --design="[Architecture, file map, boundaries, and tradeoffs]" \
  --acceptance="[Top-level completion criteria and final verification commands]"
```

The epic must include:
- **Goal:** One sentence describing what this builds.
- **Architecture:** Two to four sentences about the approach.
- **File map:** Exact paths to create or modify, with each file's responsibility.
- **Tech stack:** Key technologies, libraries, and local patterns to preserve.
- **Acceptance criteria:** Observable outcomes and final verification commands.

## Child Issue Structure

Create one child issue per implementation task under the approved epic:

```bash
bd create --type=task --parent=<epic-id> \
  --title="Task N: [Component Name]" \
  --description="[Objective, context, exact files, and numbered TDD steps]" \
  --design="[Local design notes, signatures, data shapes, and code snippets]" \
  --acceptance="[Commands to run and expected pass/fail outcomes]"
```

Each child issue must include these sections in its description or design:

```markdown
Objective:
[What this task delivers.]

Files:
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test.py`

Steps:
1. Write the failing test.
   [Include exact test code.]
2. Run the test to verify it fails.
   Command: `pytest tests/path/test.py::test_name -v`
   Expected: FAIL with "function not defined"
3. Write the minimal implementation.
   [Include exact implementation code.]
4. Run the test to verify it passes.
   Command: `pytest tests/path/test.py::test_name -v`
   Expected: PASS
5. Commit.
   Command: `git add tests/path/test.py src/path/file.py && git commit -m "feat: add specific feature"`
```

Use dependencies for ordering:

```bash
bd dep add <later-task-id> <earlier-task-id>
```

That command means `<later-task-id>` depends on `<earlier-task-id>`, so the later task will not appear in `bd ready` until the earlier task is closed.

Only add dependencies that are technically necessary. Independent tasks should remain independent so agents can pick them up separately.

## Bite-Sized Task Granularity

Each step is one action that should take two to five minutes:
- Write the failing test.
- Run it to make sure it fails.
- Implement the minimal code to make the test pass.
- Run the tests and make sure they pass.
- Commit.

Each child issue should usually complete in 15 to 45 minutes. If an issue needs more than one coherent implementation area, split it.

## No Placeholders

Every child issue must contain the actual content an engineer needs. These are plan failures and must be fixed before handoff:

- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling", "add validation", "handle edge cases"
- "Write tests for the above" without actual test code
- "Similar to Task N" instead of repeating the code and commands
- Steps that describe what to do without showing how when code is required
- References to types, functions, commands, or methods not defined in any prior issue

## Self-Review

After creating the complete beads graph, review it before handoff.

1. **Spec coverage:** Skim each section or requirement in the spec. Can you point to a child issue or epic acceptance criterion that covers it? Add missing issues.
2. **Placeholder scan:** Search epic and child issue text for the red flags in "No Placeholders". Fix them.
3. **Type consistency:** Check that types, method signatures, file paths, command names, and property names match across issues.
4. **Dependency sanity:** Run `bd ready --parent <epic-id> --explain` and verify the first ready tasks are truly safe to start.
5. **Issue readability:** Run `bd show <epic-id>` and `bd list --parent <epic-id> --long`; confirm an implementer can understand the plan without reading hidden session context.

If you find gaps, update the beads inline. Do not hand off an issue graph with known ambiguity.

## Optional Export

If a human-readable artifact is requested, generate it after the epic and child issues exist. The export is a snapshot, not the source of truth.

Useful commands:

```bash
bd show <epic-id>
bd list --parent <epic-id> --long
bd export --no-memories -o docs/superpowers/plans/<feature-name>.jsonl
```

If markdown is specifically required, create it from `bd show` and `bd list --parent <epic-id> --long`, and state that future updates must be made in `bd` first.

## Execution Handoff

After creating and reviewing the epic, offer execution choices:

**"Plan complete as beads epic `<epic-id>`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per ready issue, review between tasks, fast iteration.

**2. Inline Execution** - Execute ready issues in this session using executing-plans, with checkpoints.

**Which approach?"**

If Subagent-Driven is chosen:
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development.
- Fresh subagent per ready issue plus two-stage review.

If Inline Execution is chosen:
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans.
- Use `bd ready --parent <epic-id>` to pick work and `bd close <issue-id>` when verified.

## Integration

**Required workflow skills:**
- **superpowers:brainstorming** - Creates the feature spec and should start from unclear requirements.
- **superpowers:using-git-worktrees** - Set up isolated workspace before planning or implementation.
- **superpowers:subagent-driven-development** - Recommended execution path for independent ready issues.
- **superpowers:executing-plans** - Inline execution path when subagents are unavailable.
