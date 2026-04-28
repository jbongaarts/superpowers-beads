# CLAUDE.md — superpowers-beads

Repository-specific instructions for AI agents working in this repo.

## What this repo is

A Claude plugin marketplace containing one plugin (`superpowers-beads`) — a rewrite of obra's superpowers skills that uses `bd` (beads) as the persistence layer instead of `TodoWrite` and markdown plan files.

## Repo layout

```
superpowers-beads/
  .claude-plugin/
    marketplace.json                     # marketplace catalog
  plugins/
    superpowers-beads/
      .claude-plugin/
        plugin.json                      # plugin manifest
      skills/
        <skill-name>/
          SKILL.md                       # skill definition
  LICENSE
  README.md
  CLAUDE.md                              # this file
```

## Conventions

- Plugin and skill names: kebab-case
- Bump `version` in **both** `.claude-plugin/marketplace.json` and `plugins/superpowers-beads/.claude-plugin/plugin.json` together
- Source paths in `marketplace.json` always start with `./`
- Skills must have YAML frontmatter with at minimum `name` and `description`

## Validation

Before committing:

```
claude plugin validate .
```

## Beads usage

Track all work in beads — do not use `TodoWrite` or markdown TODO lists. The repo currently inherits the user-level beads workspace at `~/.beads/`; if work warrants a project-local workspace, run `bd init` in this directory.

## Lineage

Skills are derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT). When a skill is a direct rewrite, preserve attribution in a comment at the top of `SKILL.md`.
