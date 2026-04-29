# Agent Instructions — superpowers-beads

Repository-specific instructions for AI agents working in this repo. Both Claude
Code and Codex read these instructions; `CLAUDE.md` is a symlink to this file so
the two harnesses see the same content.

## What this repo is

A cross-harness skill repository containing one shared skill set
(`superpowers-beads`) — a rewrite of obra's superpowers skills that uses `bd`
(beads) as the persistence layer instead of `TodoWrite` and markdown plan
files.

Claude Code consumes it through the Claude plugin marketplace files. Codex
consumes the same skill source through the repo-level `.agents/skills` link and
the Codex plugin marketplace files.

## Repo layout

```
superpowers-beads/
  .agents/
    plugins/
      marketplace.json                   # Codex marketplace catalog
    skills -> ../plugins/superpowers-beads/skills
  .claude-plugin/
    marketplace.json                     # Claude marketplace catalog
  plugins/
    superpowers-beads/
      .codex-plugin/
        plugin.json                      # Codex plugin manifest
      .claude-plugin/
        plugin.json                      # Claude plugin manifest
      skills/
        <skill-name>/
          SKILL.md                       # shared skill definition
  AGENTS.md                              # this file (canonical agent instructions)
  CLAUDE.md                              # symlink to AGENTS.md
  LICENSE
  README.md
```

## Conventions

- Plugin and skill names: kebab-case
- Bump `version` in **both** `.claude-plugin/marketplace.json` and `plugins/superpowers-beads/.claude-plugin/plugin.json` together
- Source paths in marketplace files always start with `./`
- Skills must have YAML frontmatter with at minimum `name` and `description`
- Keep shared skill content under `plugins/superpowers-beads/skills`; `.agents/skills` should remain a link to that source, not a copied tree

## Validation

Before committing:

```
scripts/preflight.sh
```

See `docs/preflight.md` for the plugin-specific preflight checks. The built-in
`bd preflight --check` command currently uses beads' default Go/Nix checklist,
which is not the right gate for this plugin repo.

## Beads Usage

Track all work in beads — do not use `TodoWrite` or markdown TODO lists.

This repository currently has no Dolt remote configured. Still run
`bd dolt push` during session close so the workflow stays consistent, but the
expected output is `No remote is configured — skipping.` Treat that message as
informational, not a blocker. `git push` remains mandatory for code and
`.beads/issues.jsonl` changes.

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

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
