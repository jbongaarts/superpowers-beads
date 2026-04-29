# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

Dispatch a generic agent (Claude `Task tool (general-purpose)` / Codex `spawn_agent(agent_type="worker", ...)`) and inline the contents of `../requesting-code-review/code-reviewer.md` as the prompt body, substituting the placeholders below. The plugin does not register a named `code-reviewer` agent — passing the template content inline keeps this prompt working on every supported harness.

```
Task tool (general-purpose):
  description: "Code quality review for Task N"
  prompt: |
    [Paste the full contents of ../requesting-code-review/code-reviewer.md here,
     filled in with these values:]

    WHAT_WAS_IMPLEMENTED: [from implementer's report]
    PLAN_REFERENCE: Task N from [plan-file]
    BASE_SHA: [commit before task]
    HEAD_SHA: [current commit]
    DESCRIPTION: [task summary]
    ISSUE_ID: <task-id>
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment

## Closing the Bead on Approval

When the code quality reviewer's Assessment is **Approved** (no Critical or Important issues
remain), the reviewer (or the controller immediately upon receiving an Approved verdict)
MUST close the bead:

```
bd close <task-id>
```

This is the canonical close point for each task. The spec reviewer only approves; closing
happens here — after both review stages pass — so that the bead lifecycle accurately
reflects when work is fully verified. If the controller prefers to issue `bd close`
themselves after reading the Approved verdict, that is equally valid; what matters is that
`bd close <task-id>` is called exactly once per task, and only after both reviews pass.
