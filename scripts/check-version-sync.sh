#!/usr/bin/env sh
# Verify plugin version is in sync across:
#   - Claude marketplace catalog (.claude-plugin/marketplace.json)
#   - Claude plugin manifest    (plugins/superpowers-beads/.claude-plugin/plugin.json)
#   - Codex plugin manifest     (plugins/superpowers-beads/.codex-plugin/plugin.json)
# Exit non-zero on any mismatch or missing file.
set -eu

CLAUDE_MARKETPLACE=".claude-plugin/marketplace.json"
CLAUDE_MANIFEST="plugins/superpowers-beads/.claude-plugin/plugin.json"
CODEX_MANIFEST="plugins/superpowers-beads/.codex-plugin/plugin.json"

for f in "$CLAUDE_MARKETPLACE" "$CLAUDE_MANIFEST" "$CODEX_MANIFEST"; do
  if [ ! -f "$f" ]; then
    echo "version-sync: required manifest file not found: $f" >&2
    exit 1
  fi
done

marketplace_version="$(jq -r '.plugins[] | select(.name=="superpowers-beads") | .version' "$CLAUDE_MARKETPLACE")"
claude_version="$(jq -r '.version' "$CLAUDE_MANIFEST")"
codex_version="$(jq -r '.version' "$CODEX_MANIFEST")"

check_value() {
  label="$1"
  value="$2"
  if [ -z "$value" ] || [ "$value" = "null" ]; then
    echo "version-sync: could not read version from $label" >&2
    exit 1
  fi
}

check_value "$CLAUDE_MARKETPLACE (plugins[].version)" "$marketplace_version"
check_value "$CLAUDE_MANIFEST (.version)" "$claude_version"
check_value "$CODEX_MANIFEST (.version)" "$codex_version"

if [ "$marketplace_version" != "$claude_version" ] ||
   [ "$marketplace_version" != "$codex_version" ]; then
  echo "version-sync: version mismatch" >&2
  echo "  $CLAUDE_MARKETPLACE plugins[].version = $marketplace_version" >&2
  echo "  $CLAUDE_MANIFEST .version             = $claude_version" >&2
  echo "  $CODEX_MANIFEST .version              = $codex_version" >&2
  echo "Bump all three files together when releasing." >&2
  exit 1
fi

echo "Versions in sync: $marketplace_version (Claude marketplace + manifest, Codex manifest)"
