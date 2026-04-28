# Superpowers Formulas

Reusable beads workflows live in `.beads/formulas/` so `bd formula list`, `bd cook`, and `bd mol pour` can discover them without extra flags.

Available formulas:

- `superpowers-feature`: brainstorm, spec, plan, task, implement, verify, finish.
- `superpowers-bugfix`: reproduce, trace, failing check, fix, verify, finish.
- `superpowers-skill-authoring`: pressure-test, draft, validate, refactor, finish.
- `superpowers-parallel-burst`: frame one problem, run four sibling prototype lanes, synthesize, verify, finish.
- `superpowers-code-review-response`: intake review feedback, create one child bead per item, triage, implement, verify, reply.

Preview a formula:

```bash
bd cook superpowers-feature --dry-run --var title="Add auth flow"
```

Instantiate a persistent workflow:

```bash
bd mol pour superpowers-feature --var title="Add auth flow"
```

Run `bd formula show <name>` to inspect the steps and variables before pouring.
