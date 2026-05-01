# Releasing superpowers-beads

This document covers release cadence, versioning policy, hotfix procedure,
rollback options, and skill / `bd` deprecation policy. It is the contract
between the maintainer and consumers of the plugin.

## Versioning

The plugin uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).
Version is set in three manifests in lockstep, enforced by
`scripts/check-version-sync.sh`:

- `.claude-plugin/marketplace.json`
- `plugins/superpowers-beads/.claude-plugin/plugin.json`
- `plugins/superpowers-beads/.codex-plugin/plugin.json`

### What counts as a breaking change for a skills plugin

The plugin ships **prose instructions to AI agents**, not executable code, so
SemVer mapping is non-obvious. The rule of thumb:

**MAJOR** — breaking change for consumers:
- Skill renamed or removed.
- Skill's frontmatter `name` changed.
- Required external dependency added (e.g. requiring `bd >= X` where X is newer
  than the current floor) without a deprecation period.
- Reference from one skill to another (`superpowers:<name>`) renamed in a way
  that breaks invocation flow.
- File-layout change that breaks an existing harness's plugin discovery
  (`.agents/skills` symlink target, `.claude-plugin/` structure, etc.).
- Any change to the skill activation matrix's expected outcomes that would
  flip a previously-passing run to a fail.

**MINOR** — additive, no consumer breakage:
- New skill added.
- New supporting file added under an existing skill (`references/<file>.md`).
- New workflow formula added.
- New CI check, preflight gate, or developer tool.
- Skill description tightened in a way that *narrows* trigger scope (some
  prompts that previously activated may no longer; record in CHANGELOG).
- Skill body reorganized or trimmed without changing prescribed behavior.

**PATCH** — fixes that don't change behavior or add features:
- Typos, grammar, formatting.
- Internal refactors of supporting scripts that don't change their CLI.
- Documentation corrections.
- Pinning of CI dependencies.

Borderline cases (description loosened, anti-trigger row added, formula step
renamed) default to **MINOR** unless the maintainer can show the change does
not affect any reasonable existing trigger flow.

### Pre-release tags

Pre-release versions use `-rcN`, `-betaN`, or `-alphaN` suffixes (e.g.
`v0.2.0-rc1`). The release workflow:

- Strips the suffix when matching against the manifest version (so `v0.2.0-rc1`
  matches plugin version `0.2.0`).
- Marks the GitHub Release as `--prerelease`.

Prereleases are encouraged for any change that touches a `SKILL.md`, since
behavioral validation depends on a fresh-session matrix run.

## Cadence

Releases are **ad-hoc, demand-driven**. There is no fixed cadence. Targets:

- **PATCH** — within 1–2 days of a merged fix.
- **MINOR** — when a coherent set of additive changes accumulates, typically
  every few weeks.
- **MAJOR** — only with a written migration note and at least one prerelease
  cycle.

The maintainer may bundle multiple in-flight changes into one release if they
land close together; long delays between merged-to-main and tagged are
discouraged.

## Standard release procedure

1. **Confirm green main.**

   ```bash
   git switch main && git pull --rebase
   scripts/preflight.sh
   ```

2. **Bump version** in all three manifests (Claude marketplace, Claude plugin,
   Codex plugin) on a release branch:

   ```bash
   git switch -c bump-to-vX.Y.Z
   # edit the three manifests
   scripts/check-version-sync.sh    # confirms lockstep
   ```

3. **Update `CHANGELOG.md`.** Move `## Unreleased` content into a new
   `## vX.Y.Z — YYYY-MM-DD` section. Group under `### Added`, `### Changed`,
   `### Fixed`, `### Removed`. Reference PRs and beads.

4. **Run the skill activation matrix** if any `SKILL.md` changed since the
   prior tag. Both Claude and Codex columns are required for a `vX.Y.Z` tag
   (not `-rcN`). Record results in `docs/skill-activation-matrix.md` run log.

5. **Land the bump** via PR (preflight must pass; do not skip).

6. **Tag and push:**

   ```bash
   git switch main && git pull --rebase
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

   The `release.yml` workflow runs preflight, builds the source tarball + sha256,
   attaches a GitHub Actions build-provenance attestation, and creates the
   GitHub Release with auto-generated notes.

7. **Verify users get the update** — see `superpowers-beads-ngq`. Smoke-test
   `/plugin marketplace update` in Claude Code and the Codex equivalent before
   announcing.

## Hotfix protocol

When a critical bug ships in `vX.Y.Z` and the next regular release would carry
unrelated in-flight work:

1. **Branch from the tag**, not from main:

   ```bash
   git fetch --tags
   git switch -c hotfix/<short-slug> vX.Y.Z
   ```

2. **Apply the minimal fix.** Cherry-pick from main if the fix already exists
   there; otherwise commit directly. Use `git cherry-pick -x` so the original
   SHA is recorded.

3. **Bump PATCH** (`vX.Y.Z` → `vX.Y.Z+1`) on the hotfix branch. Do **not** pull
   in unrelated commits from main.

4. **Open a PR against main** so the hotfix branch is reviewed in the normal
   flow. Even though it doesn't merge into main directly, the diff is part of
   the audit trail.

5. **Merge the hotfix PR into main** (squash). Then re-create the hotfix branch
   from the post-merge tag if needed for the actual release.

6. **Tag and push** `vX.Y.Z+1` from the hotfix branch.

7. **Forward-port** any commits that were already on main but don't conflict
   with the hotfix — typically just the version bump itself.

If the bug is severe enough to warrant pulling the bad release, see Rollback
below.

## Rollback / bad-release remediation

GitHub tags cannot be cleanly unpublished — once a tag is fetched by users,
deleting it locally won't recall it. The remediation path:

1. **Yank the GitHub Release.** Edit the release page and mark it as
   `Draft` (or delete it entirely). The git tag still exists but the
   distribution artifacts no longer point at it.

2. **Add a CHANGELOG entry** clearly marking the version as withdrawn:

   ```
   ## vX.Y.Z — 2026-MM-DD (WITHDRAWN)
   This release contained a critical bug (see #NNN) and was withdrawn on
   2026-MM-DD. Use vX.Y.Z+1 or later. Do not install or pin to vX.Y.Z.
   ```

3. **Ship a superseding tag** (`vX.Y.Z+1`) via the hotfix protocol. The
   release notes for `vX.Y.Z+1` should explicitly mention that it supersedes
   the withdrawn release.

4. **Communicate.** If the project has a feedback channel
   (`superpowers-beads-wjd`), post the withdrawal there. Update README if the
   bug affects install instructions.

5. **Decide whether to delete the bad git tag.** Default: **retain** with the
   CHANGELOG marker. Deleting the tag breaks anyone who pinned to the bad
   version (their install fails); retaining it lets them at least diagnose
   what happened. Only delete if the bug is so severe that we want broken
   pins to fail loudly.

## Deprecation and support policy

### Skills

When a skill needs to be renamed or removed:

1. **Announce in CHANGELOG** at least one MINOR release before the breaking
   change (e.g. announce in `v0.5.0`, ship the breaking change in `v0.6.0`
   or `v1.0.0`).

2. During the deprecation window, the old skill name remains a stub that
   delegates to the new one (or fires a no-op announcement noting the
   rename).

3. The breaking change ships at the next MAJOR.

### `bd` version support

The plugin pins a `BD_VERSION` in `.github/workflows/validate.yml`. The
support contract:

- **Floor:** the pinned `BD_VERSION` is the *minimum* supported. Older `bd`
  versions may work but are not tested.
- **Bumps:** raising `BD_VERSION` is a MINOR change if the floor stays
  compatible (no new required commands), MAJOR if skills now use commands
  not present in the prior pin.
- **Window:** the project supports the current pinned version and the
  immediately-prior pinned version. Two versions back is best-effort.

When `bd` introduces a breaking change to a command a skill depends on
(e.g. renaming `bd ready --explain`), the plugin treats it as if a skill
were being renamed: announce one MINOR ahead, ship the cutover at the next
MAJOR or coordinated MINOR.

### Workflow formulas

Formulas under `.beads/formulas/` are versioned together with the plugin.
A formula rename or removal follows the same skill deprecation rule: announce
one MINOR ahead, ship the change at the next MAJOR.

## Cross-harness verification

A `vX.Y.Z` tag (not `-rcN`) requires a fresh-session skill activation matrix
run for **every harness the plugin claims to support**. Currently:

- **Claude Code** — automated via `scripts/run-activation-matrix.sh --harness=claude`.
- **Codex** — automated via `scripts/run-activation-matrix.sh --harness=codex`.

Other harnesses (Copilot CLI, Gemini CLI, etc.) require manual smoke per the
matrix doc until automation lands. A release that adds a new harness to the
support list MUST include a matrix run-log entry for that harness.

## Open follow-ups for the 1.0 commitment

1.0 implies a stronger SemVer commitment than 0.x. Before tagging `v1.0.0`:

- `superpowers-beads-ngq` — verify upgrade path delivers new tags to installed
  users (Claude marketplace + Codex).
- `superpowers-beads-803` — cross-platform smoke (Windows native + at least
  one of Copilot CLI / Gemini CLI).
- `superpowers-beads-6og` — bd API compatibility smoke in CI, so silent bd
  upstream changes don't break skills without warning.
- `superpowers-beads-wjd` — establish a user feedback channel.

Until those land, prefer `0.X` releases.
