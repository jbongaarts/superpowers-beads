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

After the CLI check succeeds, inspect workspace resolution before running any
workflow command such as `bd ready`:

```bash
bd where --json
```

If it returns `no_beads_directory`, no beads workspace is active. Distinguish
the surrounding state with read-only checks:

```bash
git rev-parse --show-toplevel >/dev/null 2>&1
```

- If the command succeeds, the session is in a git repository that has no active
  beads metadata in the repo or its parents.
- If it fails, the session is outside a git repository and also has no active
  beads workspace.

In both cases:

- Do not run `bd init` automatically.
- Do not create `.beads/`, hooks, AGENTS files, or ignore rules automatically.
- Do not assume the user is the maintainer or has permission to add project
  files.
- Continue without beads for the session if that is appropriate.
- If the user wants beads, explain the difference between project-local,
  contributor/stealth, and personal/global setup options and wait for explicit
  direction before changing the repo.

Neutral wording inside a repository:

```text
The `bd` CLI is installed, but this repository does not have an active beads
workspace. I can continue without beads for this repo/session, use the repo's
existing tracker, or initialize beads only if you explicitly want that and have
permission to add it here.
```

Neutral wording outside a repository:

```text
The `bd` CLI is installed, but this session is not inside a git repository or an
active beads workspace. I can continue without beads for this session, or you can
move me to a repository/workspace where beads should be used.
```

## State 2b: Beads Metadata Exists But Is Invalid

If `bd where --json` or `bd context --json` reports an error other than
`no_beads_directory`, treat it as a degraded workspace, not as permission to
repair or reinitialize it.

- Report the command and concise error.
- Do not run destructive init flags, migration, restore, or repair commands
  without explicit user intent.
- Continue without beads if the task can proceed safely.
- If persistence is required, file or record a blocker in the available tracker
  and move to other work.

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
