# Changelog

All notable changes to `superpowers-beads` are recorded here. The plugin uses
semantic versioning; entries are grouped under the version they shipped in.
Bump version in `.claude-plugin/marketplace.json`,
`plugins/superpowers-beads/.claude-plugin/plugin.json`, and
`plugins/superpowers-beads/.codex-plugin/plugin.json` together — the version-sync
preflight enforces this.

## Unreleased

### Added

- `superpowers-parallel-burst` formula now wired into `dispatching-parallel-agents` for the 4-lane prototype-burst sub-pattern.
- `CHANGELOG.md` (this file).
- `scripts/check-codex-manifests.sh` now validates marketplace `category` consistency across the Claude marketplace, Codex marketplace, and Codex plugin manifest.

### Changed

- Marketplace `category` normalized to `"Productivity"` across all three manifests (was `"engineering"` in `.claude-plugin/marketplace.json`).
- `finishing-a-development-branch/SKILL.md` softened the "canonical preflight" language: prefers project-specific preflight (e.g. `scripts/preflight.sh`) when present, falls back to bd commands otherwise.
- `docs/codex-publishing.md`: removed the manifest-consistency item from "Follow-Up Work" (delivered in v0.1.0 via PR #25); updated stale `superpowers-beads-zr6` reference; added a brief note on the `.agents/skills` symlink discovery path.

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
