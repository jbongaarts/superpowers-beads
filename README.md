# superpowers-beads

A beads-native rewrite of [obra's superpowers](https://github.com/obra/superpowers) skills, built around [`bd` (beads)](https://github.com/steveyegge/beads) for cross-session continuity.

## Why

The original superpowers skills persist work as markdown plan/spec files and in-session `TodoWrite` checklists. That works well within a single session but loses state on compaction, restart, or hand-off. `bd` gives us a local, dependency-aware issue store that survives all of those — so the same workflows can be expressed as graphs of issues that any future session can pick up via `bd ready`.

This plugin rewrites the skills to use `bd` as the source of truth for plans, tasks, debugging evidence, code-review feedback, and lessons learned — while keeping the rigor (TDD, verification-before-completion, systematic debugging) of the originals.

## Supported harnesses

The plugin is verified against:

- **Claude Code** — installed via `/plugin marketplace add jbongaarts/superpowers-beads`. The skill activation matrix is run against this harness on every release.
- **Codex** — installed via `codex plugin marketplace add jbongaarts/superpowers-beads`. Same skill source loads via the repo-level `.agents/skills` symlink. Matrix is run against this harness on every release.

Other harnesses (Copilot CLI, Gemini CLI, etc.) may pick up the skills via their own discovery mechanisms but are **not actively supported** in 1.0. PRs adding cross-harness fixes or smoke coverage are welcome — see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

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
- `cherry-picking-across-branches` — scope, order, and verify backports / forward-ports between long-lived branches with `bd` as the audit trail
- `writing-skills` — TDD for skills themselves

Open work is tracked as `bd` issues — run `bd ready` to see what's queued.

## Install

Claude Code:

```
/plugin marketplace add jbongaarts/superpowers-beads
/plugin install superpowers-beads@superpowers-beads
```

Codex:

```bash
codex plugin marketplace add jbongaarts/superpowers-beads
```

For local checkout or fork testing:

```bash
git clone https://github.com/jbongaarts/superpowers-beads.git
cd superpowers-beads
codex plugin marketplace add "$(pwd)"
codex
```

Codex scans `.agents/skills`, which links to the shared skill source under
`plugins/superpowers-beads/skills`. The repository also exposes a Codex plugin
marketplace at `.agents/plugins/marketplace.json`; restart Codex after
installing or upgrading if newly installed skills do not appear immediately.

## Requirements

For beads-backed persistence:

- [`bd`](https://github.com/steveyegge/beads) installed and on `PATH`
- A beads workspace initialized in the project (`bd init`) or a parent directory

If `bd` is not installed, the skills should continue without beads for that
session rather than installing tools or initializing a repository automatically.
If `bd` is installed but no beads workspace is active, initialization is still
opt-in. See [docs/beads-startup.md](docs/beads-startup.md). See
[docs/codex-publishing.md](docs/codex-publishing.md) for Codex distribution
details.

## Workflow formulas

The repo includes beads-native workflow formulas in `.beads/formulas/`.
Use `bd formula list` to see them, `bd cook <name> --dry-run --var title="..."` to preview them, and `bd mol pour <name> --var title="..."` to instantiate a workflow graph.

See [docs/formulas.md](docs/formulas.md) for the current formula catalog.

## Feedback and bug reports

- **Functional bugs / feature requests:** open a [GitHub Issue](https://github.com/jbongaarts/superpowers-beads/issues). Include the plugin version (`bd export | jq -r '.version'` or check `.claude-plugin/marketplace.json`), the harness (Claude Code / Codex) and version, and a reproduction prompt where possible.
- **Security vulnerabilities:** see [`SECURITY.md`](./SECURITY.md) — please do not file public issues for vulnerabilities.

## Credits

Derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent). Beads concepts and commands from [steveyegge/beads](https://github.com/steveyegge/beads).

This plugin is a rewrite, not a fork. See [docs/upstream-tracking.md](docs/upstream-tracking.md) for the cadence and decision process used to keep an eye on upstream changes without committing to a tight coupling.

## License

MIT — see [LICENSE](LICENSE).
