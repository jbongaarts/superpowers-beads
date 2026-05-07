---
name: writing-skills
description: Use when creating a new skill, changing an existing skill, or validating whether a skill should trigger before deployment
---

# Writing Skills

## Overview

Writing skills is test-driven development for process documentation.

**Core principle:** if you did not capture baseline behavior before changing the skill, you do not know whether the skill teaches the right thing.

Use `superpowers:test-driven-development` as the mental model: pressure scenario is RED, skill prose is production code, validation is GREEN, and tightening loopholes is REFACTOR.

## When To Create Or Change A Skill

Create or update a skill when:
- The technique is reusable across projects.
- The behavior depends on judgment and cannot be enforced better by code or validation.
- Future agents need a triggerable workflow, reference, script, or domain guide.

Do not create a skill for:
- One-off project facts. Put those in the project instructions.
- Mechanical rules that can be enforced with scripts, hooks, or tests.
- Narratives about how one session solved one problem.
- Generic practices already covered by existing skills or standard docs.

## Beads Workflow

For non-trivial skill work, pour the existing formula to create the full chain in one command:

```bash
bd mol pour superpowers-skill-authoring --var title="<skill change>" --var skill_name="<skill-dir-or-name>"
```

This creates the dependency-linked chain `pressure-test → draft → validate → refactor → finish` with pre-filled descriptions. Claim and close each step as that phase completes:

```bash
bd update <step-id> --claim
bd close <step-id> --reason="<phase outcome>"
```

Do not use markdown checklists or in-session todo lists for skill state.

For a tiny edit where the formula's chain would add noise, work on the existing parent bead and record the whole cycle as one comment:

```bash
bd comment <skill-issue> "Skill TDD evidence: RED <scenario> showed <baseline failure>; GREEN <validation> passed; REFACTOR <check> still passed."
```

## RED: Pressure-Test Before Writing

Define realistic prompts before editing the skill:
- **Trigger prompts:** situations where the skill should load.
- **Anti-trigger prompts:** similar tasks where the skill would be noisy or harmful.
- **Pressure prompts:** time pressure, sunk cost, authority, fatigue, or convenience that could make an agent skip the intended behavior.
- **Failure modes:** the exact shortcuts, rationalizations, missing steps, or wrong files you expect to catch.

Run the baseline without the new or edited skill when the environment permits. If you cannot cleanly remove the skill, use the closest honest baseline: previous skill behavior, current docs, or a manual no-skill scenario. Record the limitation.

Store evidence on the pressure-test bead:

```bash
bd comment <pressure-id> "Baseline pressure evidence: prompt=<summary>; observed failure=<behavior>; rationalization=<quote or summary>; missing instruction=<gap>."
bd close <pressure-id> --reason="Baseline pressure evidence recorded."
```

If independent validation agents are available and explicitly allowed in the current environment, use them with minimal context. Do not leak the intended fix into the validation prompt.

## GREEN: Write The Minimal Skill

Every skill needs exactly one required file:

```text
skill-name/
  SKILL.md
```

Add supporting files only when they materially reduce context load or provide reusable assets:
- `references/` for large docs that should load only when needed.
- `scripts/` for deterministic repeated operations.
- `assets/` for templates, images, or other output resources.

Keep `SKILL.md` concise. Include:
- YAML frontmatter with `name` and `description`.
- A description that only describes trigger conditions, front-loads distinctive trigger words, and includes anti-trigger boundaries when they prevent likely false positives. "Use when" is allowed but not required.
- A short overview and core principle.
- The smallest workflow that changes agent behavior.
- Specific red flags, anti-patterns, or command examples only when they prevent real failure.

Avoid:
- README, changelog, installation notes, or process diaries.
- Long explanations of things an agent already knows.
- Descriptions that summarize the workflow instead of trigger conditions.
- Multiple mediocre examples where one focused example would work.

Record the draft:

```bash
bd comment <draft-id> "Drafted <skill-name>: files=<paths>; addressed baseline gaps=<summary>."
bd close <draft-id> --reason="Minimal skill draft written."
```

## GREEN Check: Validate Behavior

Validate against the scenarios from RED:
- The skill should trigger for trigger prompts.
- It should not trigger or should gracefully decline for anti-trigger prompts.
- It should resist the pressure scenario that failed in baseline.
- Referenced files, scripts, and paths should resolve.
- The plugin or skill validator should pass.

Use repository checks from the repo root when available:

```bash
scripts/preflight.sh
# or, for Claude-manifest-only validation:
claude plugin validate .
```

Record the exact evidence:

```bash
bd comment <validate-id> "GREEN evidence: <scenario/check> -> <result>; validator=<command/result>."
bd close <validate-id> --reason="Skill validation passed."
```

Do not claim the skill is done if validation only proves formatting. It must also prove the triggering and behavior risks from RED.

## REFACTOR: Tighten Without Expanding

After validation, remove or tighten:
- Vague trigger language.
- Duplicate guidance already covered by another skill.
- Instructions that would over-trigger on unrelated tasks.
- References that load too much context for common use.
- Loopholes found during validation.

If validation exposes a new failure, update the skill and rerun the affected scenario. Record the result:

```bash
bd comment <refactor-id> "REFACTOR evidence: tightened <area>; reran <scenario/check> -> <result>."
bd close <refactor-id> --reason="Skill tightened and validation stayed green."
```

## Completion Gate

Before closing the parent bead:

```bash
scripts/preflight.sh
bd comment <skill-issue> "Verification: <commands> -> passed; skill TDD evidence recorded in <child ids>."
bd close <skill-issue> --reason="<summary>; validation passed; skill TDD evidence recorded."
```

If any command cannot run, record the blocker on the bead and create follow-up work instead of closing the issue.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "It's just docs" | Skill docs control future agent behavior. Treat them like code. |
| "The trigger is obvious" | Trigger mistakes are common. Pressure-test it. |
| "I'll validate after drafting" | That is tests-after. Capture baseline first. |
| "Subagents are unavailable" | Use an honest manual or historical baseline and record the limitation. |
| "More detail is safer" | Extra context can hide the actual rule and cause over-triggering. |
| "This belongs in every project" | Project-specific facts belong in project instructions, not reusable skills. |

## Red Flags

Stop when:
- You are editing a skill before recording RED evidence.
- The description explains the workflow instead of when to use the skill.
- The skill creates local checklist state instead of beads evidence.
- You add supporting files without a clear context-saving reason.
- Validation ignores anti-triggers or pressure scenarios.
- You are about to close the bead without `bd comment` evidence.
