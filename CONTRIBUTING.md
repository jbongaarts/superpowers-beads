# Contributing to superpowers-beads

Thanks for your interest. This guide gets you from a fresh clone to a mergeable PR.

## What this repo is

A cross-harness Claude Code + Codex plugin that ships beads-native rewrites of [obra/superpowers](https://github.com/obra/superpowers) workflow skills. The shared skill source lives under `plugins/superpowers-beads/skills/`; everything else is packaging, validation, or release machinery.

Read [`AGENTS.md`](./AGENTS.md) for the canonical agent and contributor instructions. `CLAUDE.md` is a symlink to it.

## Prerequisites

- Git and a recent shell (POSIX-compatible).
- [`bd`](https://github.com/steveyegge/beads) on `PATH` (Homebrew on macOS, `tar` install on Linux per `.github/workflows/validate.yml`).
- `jq` for the validation scripts.
- `node` only if you intend to run the brainstorming visual-companion locally; not required for normal contributions.
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`) for `claude plugin validate`.

## First-time setup

```bash
git clone https://github.com/jbongaarts/superpowers-beads
cd superpowers-beads
bd bootstrap            # clone the Beads Dolt DB from refs/dolt/data and install bd git hooks
chmod 700 .beads        # bd recommends; otherwise it warns on every command
git config beads.role contributor   # quiets a startup warning
```

Run `scripts/preflight.sh` once to confirm your environment is sane:

```bash
scripts/preflight.sh
```

This validates the plugin manifest, version sync across all three manifests (Claude marketplace + Claude plugin + Codex plugin), Codex manifest schema, skill frontmatter, intra-skill cross-references, and beads hygiene.

## Workflow

This repo uses `bd` for all task tracking. Do **not** use `TodoWrite`, `TaskCreate`, or markdown TODO lists.

```bash
bd dolt pull          # sync bead updates from other systems before editing beads
bd ready              # find available work
bd show <id>          # read the brief for an issue
bd update <id> --claim
# do the work
bd close <id> --reason="<verified completion summary>"
bd dolt push          # publish bead updates for other systems
```

Conventions for new beads, dependencies, and commit/push hygiene live in `AGENTS.md`. The `bd prime` command prints the full reference.

## Branch and PR flow

`main` is protected: no direct pushes, no force-pushes, required CI check ("Claude plugin validate"). All changes land via PR.

```bash
git checkout -b <short-feature-name>
# edit, run scripts/preflight.sh, commit
git push -u origin <short-feature-name>
gh pr create --base main --title "<short title>" --body "<see existing PRs for the shape>"
```

After CI is green:

```bash
gh pr merge <pr-number> --squash --delete-branch
```

After your PR merges:

```bash
git checkout main
git pull --rebase
git branch -D <feature-branch>
```

## Adding or changing a skill

The `writing-skills/SKILL.md` skill is the canonical guide for AI agents authoring skills here. Human contributors should follow the same TDD rhythm:

1. **Pressure-test** — define when the skill should and shouldn't trigger before writing prose. Capture trigger prompts, anti-trigger prompts, and the failure modes you want to prevent.
2. **Draft** — write the smallest `SKILL.md` that addresses the failure modes. Add supporting files only when they materially reduce context load.
3. **Validate** — run `scripts/preflight.sh` and exercise the skill manually against your trigger prompts.
4. **Refactor** — tighten loophole language, remove duplication with other skills, prune over-broad triggers.

For non-trivial skill work, pour the formula instead of building the bead chain by hand:

```bash
bd mol pour superpowers-skill-authoring --var title="<skill change>" --var skill_name="<skill-dir-or-name>"
```

Mandatory shape:

- YAML frontmatter with `name` (kebab-case) and `description` (must start with "Use when" and describe trigger conditions only — `scripts/check-skill-frontmatter.sh` enforces non-empty fields).

Attribution for skills derived from obra/superpowers is carried at the repo level by `LICENSE` (MIT notice plus the "Portions of this work are derived from 'superpowers' by Jesse Vincent" line). Per-file headers are not required.

When a skill references another skill (`superpowers:<name>`) or a supplementary file (`./helper.md`, `references/foo.md`), `scripts/check-skill-references.sh` verifies the target exists.

## Validation gates

Before opening a PR, every change must pass:

```bash
scripts/preflight.sh
```

CI runs the same script on every PR and on `main`. See [`docs/preflight.md`](./docs/preflight.md) for the individual checks.

For changes that touch any `SKILL.md`, also run the skill activation matrix manually before merging — preflight verifies *packaging* but not *behavior*. See [`docs/skill-activation-matrix.md`](./docs/skill-activation-matrix.md) for the prompts and procedure. A run takes ~15 minutes per harness.

## Releasing

Releases are tag-driven. Bump version in **all three** manifests in lockstep:

- `.claude-plugin/marketplace.json`
- `plugins/superpowers-beads/.claude-plugin/plugin.json`
- `plugins/superpowers-beads/.codex-plugin/plugin.json`

Tag and push:

```bash
git tag v0.X.Y
git push origin v0.X.Y
```

`.github/workflows/release.yml` runs preflight, builds a source tarball + sha256, attaches a GitHub Actions build-provenance attestation, and creates a GitHub Release with auto-generated notes.

For pre-release tags (e.g. `v0.X.Y-rc1`), the workflow extracts the base version for the manifest match and marks the GitHub Release as a prerelease.

## Reporting issues and security

- Functional bugs / feature requests: open a GitHub issue (or, if you have write access, a `bd` issue).
- Security vulnerabilities: see [`SECURITY.md`](./SECURITY.md) — please do not file public issues for vulnerabilities.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](./LICENSE), consistent with the rest of the project.
