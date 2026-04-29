---
name: using-superpowers
description: Use when starting any conversation - establishes how to find and activate skills before any response, including clarifying questions
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## Instruction Priority

Superpowers skills override default system prompt behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests) — highest priority
2. **Superpowers skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

If CLAUDE.md, GEMINI.md, or AGENTS.md says "don't use TDD" and a skill says "always use TDD," follow the user's instructions. The user is in control.

## How to Access Skills

**In Claude Code:** Use the `Skill` tool. When you invoke a skill, its content is loaded and presented to you—follow it directly. Never use the Read tool on skill files.

**In Codex:** Skills are discovered from installed plugins and from `.agents/skills` in the current repository. Use `$<skill-name>` or the `/skills` picker for explicit invocation; otherwise follow the skill when Codex activates it implicitly.

**In Copilot CLI:** Use the `skill` tool. Skills are auto-discovered from installed plugins. The `skill` tool works the same as Claude Code's `Skill` tool.

**In Gemini CLI:** Skills activate via the `activate_skill` tool. Gemini loads skill metadata at session start and activates the full content on demand.

**In other environments:** Check your platform's documentation for how skills are loaded.

## Platform Adaptation

Skills use Claude Code tool names. Non-CC platforms: see `references/copilot-tools.md` (Copilot CLI), `references/codex-tools.md` (Codex), and `references/gemini-tools.md` (Gemini CLI) for tool equivalents.

## Beads Availability Check

Before running `bd` from any skill, check the CLI and workspace state. Treat each degraded state as a separate problem; never auto-install or auto-init.

```bash
command -v bd >/dev/null 2>&1   # state 1: CLI present?
bd where --json                 # state 2: workspace active? (returns no_beads_directory if not)
git rev-parse --show-toplevel   # state 3: inside a git repo?
```

In every degraded state, you must:

1. **Not** run `bd init`, install `bd`, or modify the repo.
2. Tell the user which state you're in (CLI missing / workspace missing inside a repo / outside any repo / invalid bd metadata).
3. Offer to continue session-locally or use the repo's existing tracker.
4. Initialize or install only on explicit user request and only when they have permission.

Example wording when `bd` is missing (adapt for the other states):

> I do not see the `bd` CLI on PATH, so beads-backed persistence is unavailable. I can continue session-locally, or you can install `bd` your preferred way. I will not initialize or modify this repository unless you explicitly ask.

If `bd` reports invalid or degraded metadata, do not repair, migrate, or reinitialize automatically. Report the error concisely and continue without beads if the task can proceed safely.

See `docs/beads-startup.md` for the full state matrix.

# Using Skills

## The Rule

**Invoke relevant or requested skills BEFORE any response or action.** Even a 1% chance a skill might apply means you should invoke the skill to check. If an invoked skill turns out to be wrong for the situation, you don't need to use it.

Decision flow on every user message, before responding (including before clarifying questions):

1. **About to plan formally?** If yes and you haven't already brainstormed, invoke `superpowers:brainstorming` first.
2. **Might any skill apply, even 1%?** If yes → activate it. If definitely not → respond directly.
3. **After activating:** announce "Using [skill] to [purpose]".
4. **Does the skill have a checklist?** If yes → `bd create` one issue per item before doing the work. If no → follow the skill exactly.
5. Then respond.

When a skill provides a checklist, materialize each item as a `bd` issue (`bd create --title="..." --type=task`) so the work survives compaction, restart, or session hand-off. Track progress with `bd ready` / `bd update --claim` / `bd close` rather than in-session todo state.

## Red Flags

These thoughts mean STOP—you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach the task
2. **Implementation skills second** (frontend-design, mcp-builder) - these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → debugging first, then domain-specific skills.

## Skill Types

**Rigid** (TDD, debugging): Follow exactly. Don't adapt away discipline.

**Flexible** (patterns): Adapt principles to context.

The skill itself tells you which.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.
