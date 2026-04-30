#!/usr/bin/env sh
# Validate Codex plugin manifest and Codex marketplace catalog against the
# minimum required structure for installation. This is a lightweight, jq-based
# check — no JSON Schema runtime — intended to catch shape regressions
# (missing required fields, empty values, malformed source paths) before
# release. Pair with `jq empty` parse checks already done in preflight.
set -eu

CODEX_MANIFEST="plugins/superpowers-beads/.codex-plugin/plugin.json"
CODEX_MARKETPLACE=".agents/plugins/marketplace.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "check-codex-manifests: jq is required but was not found on PATH" >&2
  exit 1
fi

failed=0

require() {
  file="$1"
  label="$2"
  expr="$3"
  value="$(jq -r "$expr" "$file" 2>/dev/null || true)"
  if [ -z "$value" ] || [ "$value" = "null" ]; then
    echo "check-codex-manifests: $file: missing or empty $label" >&2
    failed=$((failed + 1))
  fi
}

require_array_nonempty() {
  file="$1"
  label="$2"
  expr="$3"
  count="$(jq -r "$expr | length" "$file" 2>/dev/null || echo 0)"
  if [ -z "$count" ] || [ "$count" = "null" ] || [ "$count" -eq 0 ]; then
    echo "check-codex-manifests: $file: $label is missing or empty array" >&2
    failed=$((failed + 1))
  fi
}

# --- Codex plugin manifest ---------------------------------------------------
if [ ! -f "$CODEX_MANIFEST" ]; then
  echo "check-codex-manifests: required file not found: $CODEX_MANIFEST" >&2
  exit 1
fi

require "$CODEX_MANIFEST" ".name"                       '.name'
require "$CODEX_MANIFEST" ".version"                    '.version'
require "$CODEX_MANIFEST" ".description"                '.description'
require "$CODEX_MANIFEST" ".skills"                     '.skills'
require "$CODEX_MANIFEST" ".interface.displayName"      '.interface.displayName'

# Skills path should be a relative directory reference under the plugin.
skills_path="$(jq -r '.skills' "$CODEX_MANIFEST" 2>/dev/null || true)"
case "$skills_path" in
  ./*) ;;
  '') ;;  # already reported by `require`
  *)
    echo "check-codex-manifests: $CODEX_MANIFEST: .skills should start with './' (got: $skills_path)" >&2
    failed=$((failed + 1))
    ;;
esac

# Resolve the skills directory relative to the manifest and confirm it exists.
manifest_dir="$(dirname "$CODEX_MANIFEST")"
plugin_root="$(dirname "$manifest_dir")"
if [ -n "$skills_path" ] && [ "$skills_path" != "null" ]; then
  resolved="$plugin_root/${skills_path#./}"
  if [ ! -d "$resolved" ]; then
    echo "check-codex-manifests: $CODEX_MANIFEST: .skills path does not resolve to a directory: $resolved" >&2
    failed=$((failed + 1))
  fi
fi

# --- Codex marketplace catalog ----------------------------------------------
if [ ! -f "$CODEX_MARKETPLACE" ]; then
  echo "check-codex-manifests: required file not found: $CODEX_MARKETPLACE" >&2
  exit 1
fi

require              "$CODEX_MARKETPLACE" ".name"                          '.name'
require_array_nonempty "$CODEX_MARKETPLACE" ".plugins[]"                   '.plugins'
require              "$CODEX_MARKETPLACE" ".plugins[0].name"               '.plugins[0].name'
require              "$CODEX_MARKETPLACE" ".plugins[0].source.source"      '.plugins[0].source.source'
require              "$CODEX_MARKETPLACE" ".plugins[0].source.path"        '.plugins[0].source.path'

# Validate the source path points at the plugin directory we ship.
source_path="$(jq -r '.plugins[0].source.path' "$CODEX_MARKETPLACE" 2>/dev/null || true)"
case "$source_path" in
  ./*) ;;
  '') ;;
  *)
    echo "check-codex-manifests: $CODEX_MARKETPLACE: plugins[0].source.path should start with './' (got: $source_path)" >&2
    failed=$((failed + 1))
    ;;
esac
if [ -n "$source_path" ] && [ "$source_path" != "null" ]; then
  resolved_plugin="${source_path#./}"
  if [ ! -d "$resolved_plugin" ]; then
    echo "check-codex-manifests: $CODEX_MARKETPLACE: plugins[0].source.path does not resolve to a directory: $resolved_plugin" >&2
    failed=$((failed + 1))
  fi
  expected_manifest="$resolved_plugin/.codex-plugin/plugin.json"
  if [ ! -f "$expected_manifest" ]; then
    echo "check-codex-manifests: $CODEX_MARKETPLACE: plugins[0].source.path missing Codex plugin manifest at $expected_manifest" >&2
    failed=$((failed + 1))
  fi
fi

# Cross-manifest consistency: marketplace plugin name should match plugin manifest name.
mk_plugin_name="$(jq -r '.plugins[0].name' "$CODEX_MARKETPLACE" 2>/dev/null || true)"
mf_plugin_name="$(jq -r '.name' "$CODEX_MANIFEST" 2>/dev/null || true)"
if [ -n "$mk_plugin_name" ] && [ "$mk_plugin_name" != "null" ] &&
   [ -n "$mf_plugin_name" ] && [ "$mf_plugin_name" != "null" ] &&
   [ "$mk_plugin_name" != "$mf_plugin_name" ]; then
  echo "check-codex-manifests: plugin name mismatch:" >&2
  echo "  $CODEX_MARKETPLACE plugins[0].name = $mk_plugin_name" >&2
  echo "  $CODEX_MANIFEST    .name           = $mf_plugin_name" >&2
  failed=$((failed + 1))
fi

# Cross-manifest category consistency. The Claude marketplace lives outside this
# script's primary scope, but category drift between Claude and Codex catalogs is
# a recurring authoring mistake — check it here so a single command catches it.
CLAUDE_MARKETPLACE=".claude-plugin/marketplace.json"
if [ -f "$CLAUDE_MARKETPLACE" ]; then
  claude_category="$(jq -r '.plugins[] | select(.name=="superpowers-beads") | .category' "$CLAUDE_MARKETPLACE" 2>/dev/null || true)"
  codex_mk_category="$(jq -r '.plugins[0].category' "$CODEX_MARKETPLACE" 2>/dev/null || true)"
  codex_mf_category="$(jq -r '.interface.category' "$CODEX_MANIFEST" 2>/dev/null || true)"
  for label in "$CLAUDE_MARKETPLACE:.plugins[].category=$claude_category" \
               "$CODEX_MARKETPLACE:.plugins[0].category=$codex_mk_category" \
               "$CODEX_MANIFEST:.interface.category=$codex_mf_category"; do
    value="${label##*=}"
    if [ -z "$value" ] || [ "$value" = "null" ]; then
      echo "check-codex-manifests: missing category at ${label%=*}" >&2
      failed=$((failed + 1))
    fi
  done
  if [ "$claude_category" != "$codex_mk_category" ] || [ "$claude_category" != "$codex_mf_category" ]; then
    echo "check-codex-manifests: category mismatch across manifests:" >&2
    echo "  $CLAUDE_MARKETPLACE plugins[].category = $claude_category" >&2
    echo "  $CODEX_MARKETPLACE  plugins[0].category = $codex_mk_category" >&2
    echo "  $CODEX_MANIFEST     interface.category = $codex_mf_category" >&2
    failed=$((failed + 1))
  fi
fi

if [ "$failed" -ne 0 ]; then
  echo "check-codex-manifests: $failed problem(s) found" >&2
  exit 1
fi

echo "Codex manifest + marketplace OK"
