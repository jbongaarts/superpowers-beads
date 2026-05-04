# Changelog

All notable changes to `superpowers-beads` are recorded here. The plugin uses
semantic versioning; entries are grouped under the version they shipped in.
Bump version in `.claude-plugin/marketplace.json`,
`plugins/superpowers-beads/.claude-plugin/plugin.json`, and
`plugins/superpowers-beads/.codex-plugin/plugin.json` together — the version-sync
preflight enforces this.

## Unreleased

## v0.2.0 — 2026-05-04

First public release after the v0.1.1 maintenance churn. Adds a new skill, a sandboxed activation-matrix runner, and the policy + tooling needed to commit to a 1.0 release.

### Added

- **`cherry-picking-across-branches` skill** (PR #41) — backporting / forward-porting between long-lived branches (release, LTS, maintenance), with TDD evidence on `superpowers-beads-mt2`. Description scoped to long-lived branches so it doesn't over-trigger on routine feature-branch picks. Matrix rows added in PR #46.
- **Skill activation matrix** (`docs/skill-activation-matrix.md`) is now the behavioral acceptance test for every release that touches a `SKILL.md`. Three full-matrix automated runs landed in this release: pre-isu (`f478012`, 42/42 with one soft finding), post-isu pre-sandbox (`123d8e2`, 41/42 with the budget-cap regression), and final post-sandbox (`4d32c0a`, 42/42 clean).
- **Sandboxed matrix runner** (PR #43) — each row runs in a fresh `mktemp -d` workspace with its own `git init` + `bd init`. Earlier runs without sandboxing claimed real beads, created worktrees, and made commits to the parent repo. Side-effect containment is now structural rather than depending on a tight `--max-budget-usd` cap.
- **`scripts/check-bd-api.sh`** (PR #49) — runs `<bd command> --help` for every bd subcommand referenced in skill content (22 subcommands), failing fast on rename/removal. Wired into preflight so CI catches API drift before users do.
- **Comma-separated `ALLOW_IN_PROGRESS` allowlist** (PRs #41/#42/#43) — `scripts/preflight.sh` now accepts a comma-separated list rather than a single bead, so multiple parallel PRs can coexist without each rebasing for a single-bead allowlist.
- **`RELEASING.md`** (PR #45) — release cadence, SemVer mapping for a skills plugin, hotfix protocol, rollback / withdrawn-release remediation, deprecation policy for skills and `bd` versions. Establishes the maintainer-to-consumer contract ahead of 1.0.
- **`docs/upstream-tracking.md`** (PR #48) — quarterly review cadence for tracking `obra/superpowers` upstream without committing to a tight coupling. Initial sync SHA recorded as `bc1fbe8`.
- **`.github/dependabot.yml`** (PR #49) — weekly GitHub Actions version watch.
- **`CLAUDE_CODE_VERSION` pin** (PR #49) — `.github/workflows/validate.yml` previously installed `@anthropic-ai/claude-code` as `latest`; now pinned to a specific version. Bumped manually as part of the quarterly upstream review.

### Changed

- **`using-git-worktrees` row 2 expected** loosened from `using-git-worktrees → executing-plans` chain to `using-git-worktrees or executing-plans` (PR #43). The chain isn't encoded in skill content; the model picks one or the other empirically and neither chains automatically.
- **`using-superpowers/SKILL.md` "User Instructions" section** (PR #47) prescribes the announce-then-acknowledge pattern when the user explicitly tells the agent to skip a workflow. Closes the matrix gap from `superpowers-beads-xmy`.
- **`brainstorming/SKILL.md` and `systematic-debugging/root-cause-tracing.md`** (PR #47) mark the visual-companion harness and `find-polluter.sh` script as **experimental** — they ship as usable patterns but are not exercised by this repo's CI.
- **GitHub Actions versions** (PR #42) bumped to Node-24-compatible majors ahead of the September 2026 Node 20 deprecation: `actions/checkout@v5`, `actions/attest-build-provenance@v4`.
- **`scripts/run-activation-matrix.sh`** (PR #38) parallelizes rows by default (`--jobs=8`). Wall-clock for the 42-row matrix dropped from ~21 minutes (sequential) to ~4 minutes.
- **README support claim** narrowed to Claude Code and Codex for 1.0 (`superpowers-beads-803`). PRs adding cross-harness fixes for Copilot CLI, Gemini CLI, etc. are welcome.

### Removed

- **Per-file MIT attribution comments** in every `SKILL.md` (PR #39). Repo-level `LICENSE` already carries the MIT notice and the "Portions of this work are derived from 'superpowers' by Jesse Vincent" line; per-file headers were redundant. Saves ~30 tokens per skill activation.
- **`metadata.version`** field in `.claude-plugin/marketplace.json` (PR #44). It was at `0.1.0` while the plugin was at `0.1.1`; nothing read the field except humans and `check-version-sync.sh` only enforces `plugins[].version`. Drift hazard removed.

### Notes for consumers

- This release is the testing target for `superpowers-beads-ngq` — verifying that `/plugin marketplace update` in Claude Code and the Codex equivalent actually deliver new tags to existing 0.1.x installs.
- The Codex column of the skill activation matrix is the next gate before 1.0; a Codex run is expected on or after 2026-05-05 once the maintainer's test machine session limit clears.
- Feedback / bug reports go to [GitHub Issues](https://github.com/jbongaarts/superpowers-beads/issues) (`superpowers-beads-wjd`).

## v0.1.1 — 2026-04-30

Maintenance release. Hardens the release pipeline and contributor surface; introduces no behavioral changes for skill consumers.

### Added

- `superpowers-parallel-burst` formula now wired into `dispatching-parallel-agents` for the 4-lane prototype-burst sub-pattern.
- `CHANGELOG.md`.
- `CONTRIBUTING.md` — onboarding, branch/PR flow, and skill-authoring guidance for new contributors.
- `SECURITY.md` — vulnerability disclosure path and threat model.
- `scripts/check-codex-manifests.sh` now validates marketplace `category` consistency across the Claude marketplace, Codex marketplace, and Codex plugin manifest.
- `scripts/check-skill-references.sh` (wired into preflight) — verifies every `superpowers:<name>`, `./<file>`, `references/<file>`, and `skills/<plugin>/<file>` reference inside a SKILL.md resolves to an existing target.
- `.github/workflows/release.yml` now handles pre-release tags (`v*.*.*-rc1`, `v*.*.*-beta.2`, etc.): strips the suffix for the manifest-version match and marks the GitHub Release as `--prerelease`.

### Changed

- Marketplace `category` normalized to `"Productivity"` across all three manifests (was `"engineering"` in `.claude-plugin/marketplace.json`).
- `finishing-a-development-branch/SKILL.md` softened the "canonical preflight" language: prefers project-specific preflight (e.g. `scripts/preflight.sh`) when present, falls back to bd commands otherwise.
- `docs/codex-publishing.md`: removed the manifest-consistency item from "Follow-Up Work" (delivered in v0.1.0 via PR #25); updated stale `superpowers-beads-zr6` reference; added a brief note on the `.agents/skills` symlink discovery path.
- Trim of the always-loaded `using-superpowers/SKILL.md` (-32%) and other skills (-10% across the plugin), replacing DOT decision-flow graphs with numbered lists and compressing redundant prose. No prescribed behavior changed; see PR #26.
- `bd lint` and the `superpowers-*` workflow formulas are now wired into the relevant skills (`writing-skills`, `brainstorming`, `writing-plans`, `systematic-debugging`, `receiving-code-review`, `executing-plans`); see PR #28.

## v0.1.0 — 2026-04-29

Initial public release.

### Highlights

- 14 beads-native skills derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent), rewritten to use `bd` (beads) as the persistence layer instead of `TodoWrite` and markdown plan files.
- Cross-harness packaging for Claude Code and Codex from a single skill source via the `.agents/skills` symlink.
- Five workflow formulas under `.beads/formulas/` (`superpowers-feature`, `superpowers-bugfix`, `superpowers-skill-authoring`, `superpowers-code-review-response`, `superpowers-parallel-burst`).
- Plugin preflight (`scripts/preflight.sh`) enforces version sync across Claude marketplace + plugin and Codex plugin manifests, validates Codex manifest/marketplace structure, validates SKILL.md frontmatter, and runs `bd orphans` / `bd stale` hygiene checks.
- CI workflow (`.github/workflows/validate.yml`) runs the full preflight on PRs and main.
- Tag-based release workflow (`.github/workflows/release.yml`): `v*.*.*` tags trigger preflight, source tarball + sha256, GitHub Actions build-provenance attestation, and a GitHub Release with auto-generated notes.

### Notable changes that shipped between scaffolding and tag

- Trimmed plugin token surface ~10% without changing prescribed behavior — replaced DOT decision-flow graphs with numbered lists, compressed the bd-availability section in `using-superpowers`, deduped redundant prose, removed two orphaned reviewer-prompt templates (PR #26).
- Wired `bd lint` and the workflow formulas into the relevant skills so model-driven self-review and manual bead-creation chains are replaced by deterministic tool calls (PR #28).
- Added `scripts/check-codex-manifests.sh` and extended `check-version-sync.sh` to cover the Codex plugin manifest, closing a silent drift gap between Claude and Codex versions (PR #25).
