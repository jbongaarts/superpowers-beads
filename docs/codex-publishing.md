# Codex Publishing and Installation Plan

This document records the plan for making `superpowers-beads` installable by
Codex users. It is about distribution and installation; the cross-harness
content work that paired with it landed under `superpowers-beads-zr6` (closed).

## Current Codex Surfaces

Codex has two relevant extension surfaces:

- Skills are local authoring units. Codex reads skills from repository, user,
  admin, and system skill directories. This is useful for development, local
  experimentation, and repo-scoped workflows. Cross-harness skill content lives
  in `plugins/superpowers-beads/skills/` and Codex discovers it through the
  `.agents/skills` symlink.
- Plugins are the installable distribution unit. A plugin can bundle skills,
  app mappings, MCP configuration, and presentation assets. Codex installs
  plugins from marketplaces.

The Codex CLI in this environment exposes marketplace management with:

```bash
codex plugin marketplace add <source>
codex plugin marketplace upgrade [marketplace-name]
codex plugin marketplace remove <marketplace-name>
```

Codex can read repository marketplaces from:

```text
$REPO_ROOT/.agents/plugins/marketplace.json
```

Codex plugin manifests live at:

```text
<plugin>/.codex-plugin/plugin.json
```

References:

- <https://developers.openai.com/codex/plugins>
- <https://developers.openai.com/codex/plugins/build>
- <https://developers.openai.com/codex/skills>

## Chosen Plan

Publish `superpowers-beads` as a Codex marketplace from this repository.

The repo contains:

```text
.agents/
  plugins/
    marketplace.json              # Codex marketplace catalog
  skills -> ../plugins/superpowers-beads/skills
plugins/
  superpowers-beads/
    .codex-plugin/
      plugin.json                 # Codex plugin manifest
    .claude-plugin/
      plugin.json                 # Claude plugin manifest
    skills/
      <skill-name>/
        SKILL.md
```

The repository marketplace entry points at the plugin with a relative local
source path:

```json
{
  "name": "superpowers-beads",
  "source": {
    "source": "local",
    "path": "./plugins/superpowers-beads"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

Users can add this repository as a marketplace:

```bash
codex plugin marketplace add jbongaarts/superpowers-beads
```

Users who want to pin a release can add a tagged ref:

```bash
codex plugin marketplace add jbongaarts/superpowers-beads@v0.1.0
```

Local checkout and fork workflows should remain first-class:

```bash
# Local development checkout
codex plugin marketplace add /path/to/superpowers-beads

# Fork or branch testing
codex plugin marketplace add owner/superpowers-beads@branch-name
```

## Why This Plan

This repo already has the shape of a plugin marketplace, and Codex supports
repository marketplaces. Keeping the marketplace in this repo means:

- Releases, docs, manifests, and skills can version together.
- Contributors can test from a fork or local checkout without a separate
  registry.
- The install path works before any official marketplace submission process
  exists for this plugin.
- A later official or curated marketplace can point at the same plugin artifact.

Direct `$skill-installer` installation is not the main distribution path. It is
useful for local development and one-off experiments, but plugins are the
reusable distribution unit for skills. This plugin bundles many skills and may
later include MCP or app integration metadata, so plugin packaging is the right
long-term install surface.

## Versioning, Updates, and Trust

Use semver and keep all publish-facing versions in lockstep:

- `.claude-plugin/marketplace.json`
- `plugins/superpowers-beads/.claude-plugin/plugin.json`
- `plugins/superpowers-beads/.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`

For stable installs, users should prefer release tags. For stronger provenance,
release automation should also publish checksums for a source archive or
generated artifact. If Codex later supports signature or checksum verification
directly in marketplace entries, add that to the catalog.

For updates:

```bash
codex plugin marketplace upgrade superpowers-beads
```

Users should restart Codex after installing or upgrading if new skills do not
appear immediately.

## Release Flow

1. Update shared skill source on a branch and merge to `main`.
2. Bump `version` in lockstep across:
   - `.claude-plugin/marketplace.json`
   - `plugins/superpowers-beads/.claude-plugin/plugin.json`
   - `plugins/superpowers-beads/.codex-plugin/plugin.json`
   `scripts/check-version-sync.sh` enforces this.
3. Run `scripts/preflight.sh` locally.
4. Push a signed tag matching the plugin version, e.g. `git tag v0.1.0 && git push origin v0.1.0`.
5. `.github/workflows/release.yml` runs on `v*.*.*` and `v*.*.*-*` (pre-release) tags and:
   - re-asserts that the tag matches the plugin manifest version,
   - re-runs the full preflight,
   - builds a source tarball plus `.sha256` checksum,
   - attaches build provenance via `actions/attest-build-provenance`,
   - creates a GitHub Release with auto-generated notes and the tarball/checksum attached.
6. Users install or upgrade from the repository marketplace; the same commit is the install source for both Claude (`/plugin marketplace add`) and Codex (`codex plugin marketplace add`).

The release artifact is source-based: `git archive` of the tag tree. There is
no separate build step, signing key, or registry to manage. Provenance is
provided by GitHub Actions attestation, which can be verified with
`gh attestation verify`. Sigstore/GPG signing or a packaged build artifact can
be added later without changing the install path for consumers.

## Follow-Up Work

Open items:

- Update install docs whenever Codex marketplace behavior changes.
- Decide whether to submit to an official or curated Codex marketplace if and
  when such a path opens up for this plugin.

CI/release validation of Codex and Claude manifest/version consistency landed
in PR #25 (`scripts/check-codex-manifests.sh`, version-sync extended to all
three manifests).
