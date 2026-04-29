---
name: brainstorming
description: "Use when starting any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements, and design before implementation."
---
<!-- Derived from obra/superpowers (MIT, (c) 2025 Jesse Vincent) - rewritten to use bd (beads) as the persistence layer. -->

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and beads-native feature epics through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you are building, present the design and get user approval. After approval, create or update a `bd` epic whose `--design` and `--acceptance` fields capture the approved design.

<HARD-GATE>
Do NOT invoke any implementation skill, write code, scaffold a project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, and a config change all have assumptions. The design can be short for simple projects, but you MUST present it and get approval.

## Beads State

Use beads as the persistent record for the brainstorm:

1. Create a brainstorming task if one does not already exist:
   ```bash
   bd create --type=task --title="Brainstorm: <topic>" --description="Explore requirements and produce an approved feature epic"
   bd update <brainstorm-id> --claim
   ```
2. As requirements become clear, update the brainstorming issue with notes:
   ```bash
   bd update <brainstorm-id> --append-notes="<decision, answer, constraint, or unresolved question>"
   ```
3. After the user approves the design, create the feature epic:
   ```bash
   bd create --type=epic \
     --title="<feature name>" \
     --description="<goal, scope, and user-visible outcome>" \
     --design="<approved architecture, components, data flow, file map, and tradeoffs>" \
     --acceptance="<observable success criteria and verification commands>"
   ```
4. Link the brainstorming task to the feature epic by noting the epic ID on the brainstorming issue, then close the brainstorming issue when the epic is reviewed.

If an appropriate feature epic already exists, update that epic instead of creating a duplicate:

```bash
bd update <epic-id> \
  --description="<refined goal, scope, and user-visible outcome>" \
  --design="<approved architecture, components, data flow, file map, and tradeoffs>" \
  --acceptance="<observable success criteria and verification commands>"
```

## Checklist

Create or update beads for each of these items and complete them in order:

1. **Explore project context** - check files, docs, recent commits, and existing beads.
2. **Offer visual companion** if the topic will involve visual questions. This is its own message, not combined with a clarifying question. See the Visual Companion section.
3. **Ask clarifying questions** - one at a time, understand purpose, constraints, and success criteria.
4. **Propose 2-3 approaches** - include tradeoffs and your recommendation.
5. **Present design** - in sections scaled to complexity; get user approval after each section.
6. **Create or update feature epic** - populate description, design, and acceptance fields from the approved design.
7. **Epic self-review** - check placeholders, contradictions, ambiguity, scope, and acceptance criteria.
8. **User reviews epic** - show `bd show <epic-id>` and ask for approval before planning.
9. **Transition to implementation planning** - invoke writing-plans with the approved epic ID.

## Process Flow

The checklist above is the flow. Two control points to enforce:

- **Visual Companion offer (if relevant) must be its own message** — no other content alongside.
- **Two approval gates** — design approval before creating the epic, and epic approval before invoking writing-plans. If approval is withheld at either gate, revise and re-present, do not proceed.

**The terminal state is invoking `superpowers:writing-plans` with the approved epic ID.** Do NOT invoke frontend-design, mcp-builder, or any other implementation skill. The ONLY skill you invoke after brainstorming is writing-plans.

## The Process

**Understanding the idea:**

- Check the current project state first: files, docs, recent commits, and existing beads.
- Before asking detailed questions, assess scope. If the request describes multiple independent subsystems, flag this immediately and help decompose it into separate feature epics.
- For appropriately scoped projects, ask questions one at a time to refine the idea.
- Prefer multiple-choice questions when possible, but open-ended is fine too.
- Only one question per message. If a topic needs more exploration, break it into multiple questions.
- Focus on understanding purpose, constraints, success criteria, and user-visible behavior.
- Persist decisions, constraints, and unresolved questions in the brainstorming issue notes.

**Exploring approaches:**

- Propose two to three different approaches with tradeoffs.
- Present options conversationally with your recommendation and reasoning.
- Lead with your recommended option and explain why.

**Presenting the design:**

- Once you believe you understand what you are building, present the design.
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced.
- Ask after each section whether it looks right so far.
- Cover architecture, components, data flow, error handling, and testing.
- Be ready to go back and clarify if something does not make sense.

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently.
- For each unit, answer: what does it do, how do you use it, and what does it depend on?
- Make boundaries clear enough that someone can understand a unit without reading its internals.
- Prefer focused files. When a file grows large, that is often a signal that it is doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work, include targeted improvements as part of the design.
- Do not propose unrelated refactoring. Stay focused on what serves the current goal.

## After the Design

**Feature epic:**

After the user approves the design, create or update the feature epic. The epic replaces the old default design document as the persistent source of truth.

The epic must contain:
- **Description:** Goal, scope, non-goals if needed, and user-visible outcome.
- **Design:** Architecture, components, data flow, file map, error handling, testing strategy, and important tradeoffs.
- **Acceptance:** Observable completion criteria and the final verification commands.

**Epic self-review:**

After creating or updating the epic, run the deterministic check first, then the judgment checks:

```bash
bd lint <epic-id>     # required-section + placeholder check
```

Fix anything `bd lint` reports, then look at the epic with fresh eyes for the items it can't catch:

1. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
2. **Scope check:** Is this focused enough for a single implementation plan, or does it need decomposition?
3. **Ambiguity check:** Could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix issues inline. No need to re-review; just update the epic and move on.

**User review gate:**

After the self-review loop passes, ask the user to review the epic before proceeding:

> "Feature epic created as `<epic-id>`. Please review `bd show <epic-id>` and let me know if you want changes before I write the implementation issues."

Wait for the user's response. If they request changes, update the epic and re-run the self-review loop. Only proceed once the user approves.

**Optional export:**

If the user or reviewer needs a standalone artifact, export from beads after the epic is current:

```bash
bd show <epic-id>
bd export --no-memories -o docs/superpowers/specs/<topic>-design.jsonl
```

If markdown is explicitly requested, create it from `bd show <epic-id>` and state that future changes must be made in the epic first.

**Implementation:**

- Invoke the writing-plans skill with the approved epic ID.
- Do NOT invoke any other skill. writing-plans is the next step.

**Optional: pour the feature formula for the standard implementation chain.**

If the work follows the canonical feature cadence (spec → plan → task → implement → verify → finish), pour the formula after the epic is approved so each downstream skill can claim its step instead of creating fresh beads:

```bash
bd mol pour superpowers-feature --var title="<feature name>" --var component="<area>"
```

The formula's `brainstorm` step duplicates the work just done; close it as accepted with a pointer to the brainstorming epic ID. `writing-plans`, `executing-plans` / `subagent-driven-development`, and `finishing-a-development-branch` will pick up subsequent steps from `bd ready`. See `bd formula list` for other workflow templates.

## Key Principles

- **One question at a time** - Do not overwhelm with multiple questions.
- **Multiple choice preferred** - Easier to answer than open-ended when possible.
- **YAGNI ruthlessly** - Remove unnecessary features from all designs.
- **Explore alternatives** - Always propose two to three approaches before settling.
- **Incremental validation** - Present design sections and get approval before moving on.
- **Persist decisions** - Important answers and approvals go into beads, not hidden session state.
- **Be flexible** - Go back and clarify when something does not make sense.

## Visual Companion

A browser-based companion for showing mockups, diagrams, and visual options during brainstorming. Available as a tool, not a mode. Accepting the companion means it is available for questions that benefit from visual treatment; it does not mean every question goes through the browser.

**Offering the companion:** When you anticipate that upcoming questions will involve visual content (mockups, layouts, diagrams), offer it once for consent:
> "Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)"

**This offer MUST be its own message.** Do not combine it with clarifying questions, context summaries, or any other content. The message should contain ONLY the offer above and nothing else. Wait for the user's response before continuing. If they decline, proceed with text-only brainstorming.

**Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**

- **Use the browser** for visual content: mockups, wireframes, layout comparisons, architecture diagrams, side-by-side visual designs.
- **Use the terminal** for text content: requirements questions, conceptual choices, tradeoff lists, scope decisions.

A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is conceptual; use the terminal. "Which wizard layout works better?" is visual; use the browser.

If they agree to the companion, read the detailed guide before proceeding:
`skills/brainstorming/visual-companion.md`
