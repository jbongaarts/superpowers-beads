# superpowers-beads

A beads-native rewrite of [obra's superpowers](https://github.com/obra/superpowers) skills, built around [`bd` (beads)](https://github.com/steveyegge/beads) for cross-session continuity.

## Why

The original superpowers skills persist work as markdown plan/spec files and in-session `TodoWrite` checklists. That works well within a single session but loses state on compaction, restart, or hand-off. `bd` gives us a local, dependency-aware issue store that survives all of those — so the same workflows can be expressed as graphs of issues that any future session can pick up via `bd ready`.

This plugin rewrites the skills to use `bd` as the source of truth for plans, tasks, debugging evidence, code-review feedback, and lessons learned — while keeping the rigor (TDD, verification-before-completion, systematic debugging) of the originals.

## Status

Early scaffold. Skills are being ported one tier at a time:

- Tier A — direct policy conflicts with `bd` (TodoWrite usage)
- Tier B — persist what's currently ephemeral (plans, debug evidence, review feedback)
- Tier C — wire `bd preflight` and `bd remember` into the existing gates
- Tier D — light-touch touch-ups

## Install

```
/plugin marketplace add jhbongaarts/superpowers-beads
/plugin install superpowers-beads@superpowers-beads
```

## Requirements

- [`bd`](https://github.com/steveyegge/beads) installed and on `PATH`
- A beads workspace initialized in the project (`bd init`) or a parent directory

## Credits

Derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent). Beads concepts and commands from [steveyegge/beads](https://github.com/steveyegge/beads).

## License

MIT — see [LICENSE](LICENSE).
