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
- `scripts/check-skill-references.sh` — every `superpowers:<name>`, `./<file>.{md,sh,...}`, `references/<file>`, and `skills/<plugin>/<file>` reference inside a SKILL.md resolves to an existing skill or file
- `cd scripts/ab-test && python3 -m unittest discover tests -q` — unit coverage for the A/B harness parser, runner helpers, report output, and cell executor
- `git diff --check`
- `bd orphans`
- `bd stale`
- no unexpected `in_progress` beads; the current claimed bead is allowed
  automatically so verification can run before closing it

When running the script before closing the bead you currently have claimed, no
extra flag is needed. `scripts/preflight.sh` asks `bd show --current --json`
for the active bead and allows that single in-progress issue automatically.

When another bead must intentionally remain in progress during preflight, allow
that additional active issue explicitly:

```bash
ALLOW_IN_PROGRESS=<other-active-bead-id> scripts/preflight.sh
```

For normal branch completion, close verified work first, then run `scripts/preflight.sh` with no allow-list.
