#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
tmp="${TMPDIR:-/tmp}/run-activation-matrix-codex-test.$$"

cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT INT TERM

mkdir -p "$tmp/fakebin" "$tmp/out"

cat > "$tmp/fakebin/codex" <<'FAKE_CODEX'
#!/usr/bin/env sh
set -eu

if IFS= read -r unexpected_stdin; then
  echo "fake codex received unexpected stdin: $unexpected_stdin" >&2
  exit 10
fi

prompt=""
for arg do
  prompt="$arg"
done

repo_root="$(pwd)"
emit_skill_read() {
  skill="$1"
  printf '{"type":"item.completed","item":{"type":"command_execution","command":"sed -n 1,220p %s/plugins/superpowers-beads/skills/%s/SKILL.md"}}\n' "$repo_root" "$skill"
}

printf '{"type":"thread.started","thread_id":"fake"}\n'
printf '{"type":"turn.started"}\n'
emit_skill_read "using-superpowers"

case "$prompt" in
  *"CSV export feature"*)
    emit_skill_read "brainstorming"
    ;;
  *"regex on line 42"*)
    ;;
  *)
    echo "fake codex did not recognize prompt: $prompt" >&2
    exit 11
    ;;
esac

printf '{"type":"turn.completed"}\n'
FAKE_CODEX
chmod +x "$tmp/fakebin/codex"

PATH="$tmp/fakebin:$PATH" "$repo_root/scripts/run-activation-matrix.sh" \
  --harness=codex \
  --rows=brainstorming:1,brainstorming:3 \
  --jobs=2 \
  --out="$tmp/out" > "$tmp/run.log"

artifact="$(find "$tmp/out" -maxdepth 1 -name '*-codex-*.json' -print | sort | tail -n 1)"
if [ -z "$artifact" ] || [ ! -s "$artifact" ]; then
  echo "test-run-activation-matrix-codex: missing codex artifact" >&2
  cat "$tmp/run.log" >&2
  exit 1
fi

jq -e '
  .summary.total == 2
  and .summary.matched == 2
  and .summary.mismatched == 0
  and .summary.ambiguous == 0
' "$artifact" >/dev/null

jq -e '
  any(.rows[];
    .section == "brainstorming"
    and .row == "1"
    and .activated_filtered == ["brainstorming"]
    and .outcome == "match"
  )
' "$artifact" >/dev/null

jq -e '
  any(.rows[];
    .section == "brainstorming"
    and .row == "3"
    and .activated_filtered == []
    and .outcome == "match"
  )
' "$artifact" >/dev/null

echo "Codex activation matrix runner test passed."
