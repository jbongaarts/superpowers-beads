#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/bin"
cat >"$tmp/bin/bd" <<'EOF'
#!/usr/bin/env sh
set -eu

if [ "$1" = "list" ] && [ "${2:-}" = "--status=in_progress" ] && [ "${3:-}" = "--json" ]; then
  printf '%s\n' "${BD_IN_PROGRESS_JSON:-[]}"
  exit 0
fi

if [ "$1" = "show" ] && [ "${2:-}" = "--current" ] && [ "${3:-}" = "--json" ]; then
  if [ "${BD_CURRENT_EXIT:-0}" != "0" ]; then
    exit "$BD_CURRENT_EXIT"
  fi
  printf '%s\n' "${BD_CURRENT_JSON:-[]}"
  exit 0
fi

if [ "$1" = "show" ]; then
  printf 'issue %s\n' "$2"
  exit 0
fi

printf 'unexpected bd invocation: %s\n' "$*" >&2
exit 2
EOF
chmod +x "$tmp/bin/bd"

run_gate() {
  env -u ALLOW_IN_PROGRESS PATH="$tmp/bin:$PATH" "$@" "$repo_root/scripts/check-in-progress-beads.sh"
}

assert_success() {
  if ! output="$(run_gate "$@" 2>&1)"; then
    printf 'expected success, got failure:\n%s\n' "$output" >&2
    exit 1
  fi
}

assert_failure_contains() {
  expected="$1"
  shift
  if output="$(run_gate "$@" 2>&1)"; then
    printf 'expected failure, got success:\n%s\n' "$output" >&2
    exit 1
  fi
  case "$output" in
    *"$expected"*) ;;
    *)
      printf 'expected failure output to contain %s, got:\n%s\n' "$expected" "$output" >&2
      exit 1
      ;;
  esac
}

assert_success \
  BD_IN_PROGRESS_JSON='[]' \
  BD_CURRENT_JSON='[]'

assert_success \
  BD_IN_PROGRESS_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"}]' \
  BD_CURRENT_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"}]'

assert_failure_contains "superpowers-beads-3c0" \
  BD_IN_PROGRESS_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"},{"id":"superpowers-beads-3c0","status":"in_progress"}]' \
  BD_CURRENT_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"}]'

assert_success \
  ALLOW_IN_PROGRESS='superpowers-beads-3c0' \
  BD_IN_PROGRESS_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"},{"id":"superpowers-beads-3c0","status":"in_progress"}]' \
  BD_CURRENT_JSON='[{"id":"superpowers-beads-d3f","status":"in_progress"}]'

assert_success \
  ALLOW_IN_PROGRESS='superpowers-beads-3c0' \
  BD_IN_PROGRESS_JSON='[{"id":"superpowers-beads-3c0","status":"in_progress"}]' \
  BD_CURRENT_EXIT=1

echo "check-in-progress-beads tests passed."
