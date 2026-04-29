# Plugin Preflight

`bd preflight --check` currently runs beads' built-in Go/Nix project checks. This repository ships Claude plugin metadata and Codex-discoverable repo skills, so use the repo-local plugin preflight before opening or merging PRs:

```bash
scripts/preflight.sh
```

The script checks:

- `claude plugin validate .`
- Codex skill discovery smoke check through `.agents/skills`
- Codex plugin manifest and marketplace JSON parse checks
- `scripts/check-version-sync.sh` — Claude `marketplace.json`, Claude `plugin.json`, and Codex `plugin.json` all carry the same plugin version
- `scripts/check-codex-manifests.sh` — Codex plugin manifest and marketplace catalog have required fields, valid `./` source paths that resolve to existing directories, and a consistent plugin name
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
