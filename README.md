# superpowers-beads

A beads-native rewrite of [obra's superpowers](https://github.com/obra/superpowers) skills, built around [`bd` (beads)](https://github.com/steveyegge/beads) for cross-session continuity.

## Why

The original superpowers skills persist work as markdown plan/spec files and in-session `TodoWrite` checklists. That works well within a single session but loses state on compaction, restart, or hand-off. `bd` gives us a local, dependency-aware issue store that survives all of those — so the same workflows can be expressed as graphs of issues that any future session can pick up via `bd ready`.

This plugin rewrites the skills to use `bd` as the source of truth for plans, tasks, debugging evidence, code-review feedback, and lessons learned — while keeping the rigor (TDD, verification-before-completion, systematic debugging) of the originals.

## Status

Active. Skills currently shipped:

- `using-superpowers` — entry-point skill explaining how to find and use the others
- `brainstorming` — turn ideas into approved feature epics in `bd`
- `writing-plans` — produce a `bd` epic + child issues from an approved spec
- `executing-plans` — work a `bd` epic to completion in a single session
- `subagent-driven-development` — same-session execution with a fresh subagent per issue and two-stage review
- `dispatching-parallel-agents` — model parallel work as a `bd` swarm and dispatch one worker per ready bead
- `using-git-worktrees` — create `bd`-managed worktrees that share the beads database
- `test-driven-development` — RED/GREEN/REFACTOR cycle with evidence recorded on `bd`
- `systematic-debugging` — four-phase root-cause workflow with evidence persisted on the bug bead
- `verification-before-completion` — gate every completion claim on fresh verification recorded on the bead
- `requesting-code-review` / `receiving-code-review` — dispatch and triage reviews with `bd` as the persistent record
- `finishing-a-development-branch` — verify, run preflight, integrate, and clean up
- `writing-skills` — TDD for skills themselves

Open work is tracked as `bd` issues — run `bd ready` to see what's queued.

## Install

```
/plugin marketplace add jbongaarts/superpowers-beads
/plugin install superpowers-beads@superpowers-beads
```

## Requirements

For beads-backed persistence:

- [`bd`](https://github.com/steveyegge/beads) installed and on `PATH`
- A beads workspace initialized in the project (`bd init`) or a parent directory

If `bd` is not installed, the skills should continue without beads for that
session rather than installing tools or initializing a repository automatically.
If `bd` is installed but no beads workspace is active, initialization is still
opt-in. See [docs/beads-startup.md](docs/beads-startup.md).

## Workflow formulas

The repo includes beads-native workflow formulas in `.beads/formulas/`.
Use `bd formula list` to see them, `bd cook <name> --dry-run --var title="..."` to preview them, and `bd mol pour <name> --var title="..."` to instantiate a workflow graph.

See [docs/formulas.md](docs/formulas.md) for the current formula catalog.

## Credits

Derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent). Beads concepts and commands from [steveyegge/beads](https://github.com/steveyegge/beads).

## License

MIT — see [LICENSE](LICENSE).
