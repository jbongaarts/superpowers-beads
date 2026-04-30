# Changelog

All notable changes to `superpowers-beads` are recorded here. The plugin uses
semantic versioning; entries are grouped under the version they shipped in.
Bump version in `.claude-plugin/marketplace.json`,
`plugins/superpowers-beads/.claude-plugin/plugin.json`, and
`plugins/superpowers-beads/.codex-plugin/plugin.json` together — the version-sync
preflight enforces this.

## Unreleased

### Added

- `docs/skill-activation-matrix.md` — manual matrix of trigger and anti-trigger prompts for every skill, run before any release that touches a `SKILL.md`. Validates *behavior* where preflight only validates *packaging*.

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
