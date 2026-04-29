#!/usr/bin/env sh
# Verify that plugin version is in sync between the marketplace catalog and
# the plugin manifest. Exit non-zero on mismatch.
set -eu

MARKETPLACE=".claude-plugin/marketplace.json"
PLUGIN_MANIFEST="plugins/superpowers-beads/.claude-plugin/plugin.json"

if [ ! -f "$MARKETPLACE" ] || [ ! -f "$PLUGIN_MANIFEST" ]; then
  echo "version-sync: required manifest files not found" >&2
  exit 1
fi

marketplace_version="$(jq -r '.plugins[] | select(.name=="superpowers-beads") | .version' "$MARKETPLACE")"
plugin_version="$(jq -r '.version' "$PLUGIN_MANIFEST")"

if [ -z "$marketplace_version" ] || [ "$marketplace_version" = "null" ]; then
  echo "version-sync: could not read superpowers-beads version from $MARKETPLACE" >&2
  exit 1
fi
if [ -z "$plugin_version" ] || [ "$plugin_version" = "null" ]; then
  echo "version-sync: could not read version from $PLUGIN_MANIFEST" >&2
  exit 1
fi

if [ "$marketplace_version" != "$plugin_version" ]; then
  echo "version-sync: version mismatch" >&2
  echo "  $MARKETPLACE plugins[].version = $marketplace_version" >&2
  echo "  $PLUGIN_MANIFEST .version       = $plugin_version" >&2
  echo "Bump both files together when releasing." >&2
  exit 1
fi

echo "Versions in sync: $plugin_version"
