# Beads Startup States

Superpowers-beads prefers `bd` as the persistence layer, but startup should be
explicit and non-fatal when a session cannot use beads. Do not assume the user
is the repository maintainer, and do not assume the current repo wants beads.

## State 1: `bd` Is Not Installed

Detect this before running any beads command:

```bash
command -v bd >/dev/null 2>&1
```

If it fails:

- Do not run `bd init`.
- Do not install `bd` automatically.
- Tell the user beads persistence is unavailable for this session.
- Continue with session-local tracking if the user wants to proceed.
- If the user wants beads persistence, offer install options that do not assume
  global tool-install permissions.

Neutral wording:

```text
I do not see the `bd` CLI on PATH, so I cannot use beads-backed persistence in
this session. I can continue without beads for this repo/session, or you can
install `bd` using your preferred local, user-level, or project-approved method.
I will not initialize or modify this repository for beads unless you explicitly
ask for that.
```

This is a tool availability problem, not a repository initialization problem.
Handle it separately from missing `.beads` metadata.

## State 2: `bd` Is Installed But This Repo Has No Beads Workspace

This is tracked separately by `superpowers-beads-2ko`. The desired behavior is
also non-fatal: explain that no beads workspace is active, continue without
beads if appropriate, and only initialize beads when the user explicitly asks.

## State 3: `bd` Is Installed And A Beads Workspace Is Active

Use normal beads-backed workflows:

```bash
bd ready
bd show <id>
bd update <id> --claim
bd close <id>
```

When starting a session, `bd prime` can load full workflow context after the
CLI and workspace are both available.
