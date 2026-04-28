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
scripts/preflight.sh
```

See `docs/preflight.md` for the plugin-specific preflight checks. The built-in `bd preflight --check` command currently uses beads' default Go/Nix checklist, which is not the right gate for this plugin repo.

## Beads usage

Track all work in beads — do not use `TodoWrite` or markdown TODO lists. The repo currently inherits the user-level beads workspace at `~/.beads/`; if work warrants a project-local workspace, run `bd init` in this directory.

## Lineage

Skills are derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT). When a skill is a direct rewrite, preserve attribution in a comment at the top of `SKILL.md`.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
