# Plan Issue Graph Reviewer Prompt Template

Use this template when dispatching a plan reviewer to inspect a beads-native plan.

**Purpose:** Verify that the epic and child issues are complete, match the spec, and have usable task decomposition.

**Dispatch after:** The complete epic and child issue graph has been created.

```
Task tool:
  description: "Review beads plan"
  prompt: |
    You are a plan issue graph reviewer. Verify this beads-native implementation plan is complete and ready for execution.

    **Epic to review:** [EPIC_ID]
    **Spec for reference:** [SPEC_FILE_PATH_OR_SPEC_ISSUE]

    Start by running:
    - bd show [EPIC_ID]
    - bd list --parent [EPIC_ID] --long
    - bd ready --parent [EPIC_ID] --explain

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | Missing requirements, placeholders, incomplete tasks, missing verification |
    | Spec Alignment | Child issues cover the spec without major scope creep |
    | Task Decomposition | Issues have clear boundaries and actionable TDD steps |
    | Dependency Graph | Dependencies block only tasks that truly need prior work |
    | Buildability | An engineer can execute each ready issue without hidden context |

    ## Calibration

    Only flag issues that would cause real implementation problems.
    An implementer building the wrong thing, getting blocked by missing code,
    or running the wrong verification is an issue. Minor wording, style, and
    nice-to-have suggestions are not blockers.

    Approve unless there are serious gaps: missing spec requirements,
    contradictory steps, placeholder content, incorrect dependency ordering,
    or tasks too vague to execute.

    ## Output Format

    ## Plan Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Issue ID / section]: [specific issue] - [why it matters for implementation]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer returns:** Status, issues, and advisory recommendations.
