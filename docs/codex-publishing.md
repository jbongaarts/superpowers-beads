# Codex Publishing and Installation Plan

This document records the plan for making `superpowers-beads` installable by
Codex users. It is about distribution and installation; making the shared skill
content itself work well in Codex is tracked by
`superpowers-beads-zr6`.

## Current Codex Surfaces

Codex has two relevant extension surfaces:

- Skills are local authoring units. Codex reads skills from repository, user,
  admin, and system skill directories. This is useful for development, local
  experimentation, and repo-scoped workflows.
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

1. Update shared skill source.
2. Update Claude and Codex manifests together.
3. Run repo preflight and plugin validators.
4. Tag the release, for example `v0.1.0`.
5. Publish the tag and GitHub release notes.
6. Attach checksums or generated artifacts if release automation produces them.
7. Users install or upgrade from the repository marketplace.

The first implementation can be source-based. A generated release artifact is
optional until the repo has a real build step or until Codex marketplace
support requires packaged assets.

## Follow-Up Work

The chosen plan requires implementation beads for:

- Updating install docs when Codex marketplace behavior changes.
- Extending CI/release validation to check Codex and Claude manifest/version
  consistency.
- Deciding later whether to submit to an official or curated Codex marketplace
  once such a path is available for this plugin.
