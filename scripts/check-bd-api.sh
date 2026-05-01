#!/usr/bin/env sh
# Verify the bd command surface that skills depend on still exists in the
# pinned bd version. If bd renames or removes a subcommand a skill references,
# this catches it before users hit a broken skill flow.
#
# Strategy: run `<bd command> --help` for each subcommand and assert exit 0.
# `--help` is a stable, side-effect-free probe; renamed or removed subcommands
# fail with non-zero. Multi-token commands (e.g. `bd dolt push`) probe at the
# leaf so missing intermediate subcommand groups are also caught.
#
# The command list is hand-maintained from a grep over the skills tree, kept
# narrow to commands that actually appear in shipped SKILL.md content. New
# commands referenced by future skill edits should be added here so CI catches
# upstream renames.
#
# Run locally:  scripts/check-bd-api.sh
# Run in CI:    wired via scripts/preflight.sh

set -eu

if ! command -v bd >/dev/null 2>&1; then
  echo "check-bd-api: bd not on PATH" >&2
  exit 1
fi

# Commands referenced in plugins/superpowers-beads/skills/**/SKILL.md as of
# this script's authorship. Keep alphabetized; one command per line.
COMMANDS="
bd close
bd comment
bd create
bd defer
bd dep
bd dolt pull
bd dolt push
bd export
bd formula
bd human
bd init
bd lint
bd list
bd mol
bd orphans
bd preflight
bd ready
bd remember
bd show
bd stale
bd update
bd where
"

failed=""
echo "Probing $(echo "$COMMANDS" | grep -c .) bd subcommands..."

# Use a here-document so the loop body runs in the parent shell and can
# accumulate $failed across iterations (POSIX-portable; avoids the
# pipe-into-while subshell trap).
while IFS= read -r cmd; do
  [ -z "$cmd" ] && continue
  if eval "$cmd --help" >/dev/null 2>&1; then
    printf '  OK   %s\n' "$cmd"
  else
    printf '  FAIL %s\n' "$cmd" >&2
    failed="${failed}${cmd}
"
  fi
done <<EOF
$COMMANDS
EOF

if [ -n "$failed" ]; then
  echo "" >&2
  echo "bd API drift detected — the following commands failed --help:" >&2
  printf '%s' "$failed" | sed 's/^/  /' >&2
  echo "" >&2
  echo "Either the pinned bd version has changed the command surface, or" >&2
  echo "scripts/check-bd-api.sh's command list is out of date with what skills" >&2
  echo "actually reference. Reconcile by either updating the COMMANDS list" >&2
  echo "(if the rename is intentional) or pinning bd to the prior version." >&2
  exit 1
fi

echo "bd API surface OK ($(echo "$COMMANDS" | grep -c .) subcommands probed against $(bd --version 2>/dev/null | head -1))"
