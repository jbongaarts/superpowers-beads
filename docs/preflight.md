# Plugin Preflight

`bd preflight --check` currently runs beads' built-in Go/Nix project checks. This repository ships Claude plugin metadata and Codex-discoverable repo skills, so use the repo-local plugin preflight before opening or merging PRs:

```bash
scripts/preflight.sh
```

The script checks:

- `claude plugin validate .`
- Codex skill discovery smoke check through `.agents/skills`
- Codex plugin manifest and marketplace JSON parse checks
- `scripts/check-version-sync.sh` — `marketplace.json` and `plugin.json` carry the same plugin version
- `scripts/check-skill-frontmatter.sh` — every `SKILL.md` has YAML frontmatter with non-empty `name` and `description`
- `git diff --check`
- `bd orphans`
- `bd stale`
- no unexpected `in_progress` beads

When running the script before closing a bead that you intentionally want to keep claimed (for example, the bead implementing the preflight itself), allow that one active issue explicitly:

```bash
ALLOW_IN_PROGRESS=<active-bead-id> scripts/preflight.sh
```

For normal branch completion, close verified work first, then run `scripts/preflight.sh` with no allow-list.
