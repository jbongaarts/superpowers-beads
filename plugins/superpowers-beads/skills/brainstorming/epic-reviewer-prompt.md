# Feature Epic Reviewer Prompt Template

Use this template when dispatching a reviewer to inspect a brainstorming output epic.

**Purpose:** Verify that the feature epic is complete, internally consistent, and ready for implementation planning.

**Dispatch after:** The feature epic has been created or updated from the approved design.

```
Task tool:
  description: "Review feature epic"
  prompt: |
    You are a feature epic reviewer. Verify this beads epic is complete and ready for implementation planning.

    **Epic to review:** [EPIC_ID]

    Start by running:
    - bd show [EPIC_ID]

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | Missing goal, design, acceptance criteria, placeholders, incomplete sections |
    | Consistency | Internal contradictions or requirements that conflict with the design |
    | Clarity | Ambiguity that could cause the implementation plan to build the wrong thing |
    | Scope | Focused enough for a single implementation plan, not multiple independent subsystems |
    | YAGNI | Unrequested features or over-engineered architecture |
    | Acceptance | Observable success criteria and verification commands |

    ## Calibration

    Only flag issues that would cause real problems during implementation planning.
    Missing acceptance criteria, contradictions, or requirements that can be
    interpreted two different ways are issues. Minor wording improvements,
    stylistic preferences, and sections being shorter than others are not.

    Approve unless there are serious gaps that would lead to a flawed plan.

    ## Output Format

    ## Epic Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Field or section]: [specific issue] - [why it matters for planning]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer returns:** Status, issues, and advisory recommendations.
