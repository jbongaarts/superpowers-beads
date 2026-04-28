# Plugin Preflight

`bd preflight --check` currently runs beads' built-in Go/Nix project checks. This repository is a Claude plugin marketplace, so use the repo-local plugin preflight before opening or merging PRs:

```bash
scripts/preflight.sh
```

The script checks:

- `claude plugin validate .`
- `git diff --check`
- `bd orphans`
- `bd stale`
- no unexpected `in_progress` beads

When running the script before closing a bead that you intentionally want to keep claimed (for example, the bead implementing the preflight itself), allow that one active issue explicitly:

```bash
ALLOW_IN_PROGRESS=<active-bead-id> scripts/preflight.sh
```

For normal branch completion, close verified work first, then run `scripts/preflight.sh` with no allow-list.
