"""A/B harness entry point.

Runs combinatorial cells of (variant, prompt, model, rep), invokes the selected
agent harness hermetically per cell, classifies whether the target skill fires
as the first tool action on turn 1, and writes per-run JSONL records.

Usage:
    python3 scripts/ab-test/run.py --n 1 --yes
    python3 scripts/ab-test/run.py --variants current,a --models sonnet --n 5 --yes
    python3 scripts/ab-test/run.py --harness codex --variants current,a --n 1 --yes
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_plugin import build_variant_plugin
from codex_runner import analyze_codex_stream, run_codex_cell
from detect import analyze_stream
from executor import execute_cells
from report import format_summary, summarize
from runner import extract_rate_limit_status, extract_usage, run_cell


MIN_CLAUDE_VERSION = (2, 1, 132)
ESTIMATED_INPUT_TOKENS_PER_CELL = 10_000


def _load_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _resolve_models(harness: str, models_arg: list[str] | None) -> list[str]:
    if models_arg:
        return models_arg
    if harness == "codex":
        return ["default"]
    return ["claude-sonnet-4-6"]


def _parse_claude_version(output: str) -> tuple[int, int, int] | None:
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", output)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def _check_claude_version(claude_path: str) -> None:
    try:
        proc = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"could not check claude CLI version: {exc}") from exc
    output = f"{proc.stdout}\n{proc.stderr}"
    if proc.returncode != 0:
        raise SystemExit(f"could not check claude CLI version: {output.strip()}")
    version = _parse_claude_version(output)
    if version is None:
        raise SystemExit(f"could not parse claude CLI version from: {output.strip()}")
    if version < MIN_CLAUDE_VERSION:
        raise SystemExit(
            "claude CLI is too old for this harness: "
            f"found {_format_version(version)}, need >= {_format_version(MIN_CLAUDE_VERSION)}"
        )


def _filter(
    items: list[dict],
    ids: list[str] | None,
    key: str,
    flag_name: str,
) -> list[dict]:
    if not ids:
        return items
    wanted = set(ids)
    out = [i for i in items if i[key] in wanted]
    missing = wanted - {i[key] for i in items}
    if missing:
        raise SystemExit(f"unknown ids in --{flag_name} filter: {sorted(missing)}")
    return out


def _build_cells(
    variants: list[dict],
    prompts: list[dict],
    models: list[str],
    n: int,
) -> list[dict]:
    cells = []
    for rep in range(n):
        for prompt in prompts:
            for model in models:
                for variant in variants:
                    cells.append(
                        {
                            "variant_id": variant["id"],
                            "variant_description": variant["description"],
                            "prompt_id": prompt["id"],
                            "prompt_text": prompt["text"],
                            "model": model,
                            "rep": rep,
                        }
                    )
    return cells


def _stderr_excerpt(stderr: str | None, limit: int = 500) -> str:
    return (stderr or "")[-limit:]


def _shorten(text: str, limit: int = 60) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _print_preflight(
    cells: list[dict],
    variants: list[dict],
    prompts: list[dict],
    models: list[str],
    n: int,
    output: Path,
    concurrency: int,
    yes: bool,
    harness: str = "claude",
) -> None:
    print(f"A/B harness preflight ({datetime.now(timezone.utc).isoformat()})")
    print(f"  harness:  {harness}")
    print(f"  variants: {len(variants)} -> {[v['id'] for v in variants]}")
    for variant in variants:
        print(f"    {variant['id']}: {_shorten(variant['description'])}")
    print(f"  prompts:  {len(prompts)} -> {[p['id'] for p in prompts]}")
    print(f"  models:   {len(models)} -> {models}")
    print(f"  reps:     {n}")
    print(f"  total cells: {len(cells)}")
    print(f"  concurrency: {concurrency}")
    estimated_input_tokens = len(cells) * ESTIMATED_INPUT_TOKENS_PER_CELL
    print(
        "  estimated input tokens: "
        f"~{estimated_input_tokens:,} "
        f"(~{ESTIMATED_INPUT_TOKENS_PER_CELL:,}/cell back-of-envelope)"
    )
    print(f"  output: {output}")
    if harness == "codex":
        print(
            "  auth: your installed `codex` CLI session. Codex does not expose "
            "Claude-style token usage here; start with small n/concurrency to "
            "avoid exhausting the Codex session bucket."
        )
    else:
        print(
            "  auth: subscription via your installed `claude` CLI (Pro 5h bucket). "
            "Token usage is logged per cell so you can extrapolate."
        )
    if not yes:
        print()
        print("Refusing to start without --yes. Re-run with --yes to proceed.")


def _timeout_record(cell: dict, timeout_seconds: int) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant_id": cell["variant_id"],
        "prompt_id": cell["prompt_id"],
        "model": cell["model"],
        "rep": cell["rep"],
        "harness_validated": False,
        "activated": False,
        "first_tool_call": None,
        "first_tool_skill_name": None,
        "first_tool_call_block_index": None,
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_input_tokens": None,
        "cache_creation_input_tokens": None,
        "duration_ms": timeout_seconds * 1000,
        "total_cost_usd": None,
        "rate_limit_status": None,
        "returncode": None,
        "stderr_excerpt": "TIMEOUT",
    }


def _record_for_cell(
    cell: dict,
    target_plugin: str,
    target_skill: str,
    plugin_dir: Path,
    claude_path: str,
    timeout_seconds: int,
) -> dict:
    started = time.time()
    result = run_cell(
        claude_path=claude_path,
        plugin_dir=plugin_dir,
        model=cell["model"],
        prompt=cell["prompt_text"],
        timeout_seconds=timeout_seconds,
    )
    elapsed_ms = int((time.time() - started) * 1000)
    analysis = analyze_stream(
        result["stdout_lines"],
        target_plugin=target_plugin,
        target_skill=target_skill,
    )
    usage = extract_usage(result["stdout_lines"])
    rate_limit_status = extract_rate_limit_status(result["stdout_lines"])

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant_id": cell["variant_id"],
        "prompt_id": cell["prompt_id"],
        "model": cell["model"],
        "rep": cell["rep"],
        "harness_validated": analysis["harness_validated"],
        "first_tool_call": analysis["first_tool_call"],
        "first_tool_skill_name": analysis["first_tool_skill_name"],
        "first_tool_call_block_index": analysis["first_tool_call_block_index"],
        "activated": analysis["activated"],
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cache_read_input_tokens": usage["cache_read_input_tokens"],
        "cache_creation_input_tokens": usage["cache_creation_input_tokens"],
        "duration_ms": usage["duration_ms"] or elapsed_ms,
        "total_cost_usd": usage["total_cost_usd"],
        "rate_limit_status": rate_limit_status,
        "returncode": result["returncode"],
        "stderr_excerpt": _stderr_excerpt(result["stderr"]),
    }


def _codex_workspace_has_skill(workspace_dir: Path, target_skill: str) -> bool:
    skill_path = workspace_dir / ".agents" / "skills" / target_skill / "SKILL.md"
    return skill_path.is_file()


def _record_for_codex_cell(
    cell: dict,
    target_skill: str,
    workspace_dir: Path,
    codex_path: str,
    timeout_seconds: int,
) -> dict:
    started = time.time()
    result = run_codex_cell(
        codex_path=codex_path,
        workspace_dir=workspace_dir,
        model=cell["model"],
        prompt=cell["prompt_text"],
        timeout_seconds=timeout_seconds,
    )
    elapsed_ms = int((time.time() - started) * 1000)
    analysis = analyze_codex_stream(
        result["stdout_lines"],
        target_skill=target_skill,
    )
    harness_validated = _codex_workspace_has_skill(workspace_dir, target_skill)

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "variant_id": cell["variant_id"],
        "prompt_id": cell["prompt_id"],
        "model": cell["model"],
        "rep": cell["rep"],
        "harness_validated": harness_validated,
        "first_tool_call": analysis["first_tool_call"],
        "first_tool_skill_name": analysis["first_tool_skill_name"],
        "first_tool_call_block_index": analysis["first_tool_call_block_index"],
        "activated": analysis["activated"],
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_input_tokens": None,
        "cache_creation_input_tokens": None,
        "duration_ms": elapsed_ms,
        "total_cost_usd": None,
        "rate_limit_status": None,
        "returncode": result["returncode"],
        "stderr_excerpt": _stderr_excerpt(result["stderr"]),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the A/B activation-rate harness over "
            "(variant, prompt, model, rep) cells."
        ),
    )
    parser.add_argument(
        "--harness",
        choices=["claude", "codex"],
        default="claude",
        help="Agent harness to run. Default: claude.",
    )
    parser.add_argument(
        "--variants-file",
        type=Path,
        default=HERE / "variants.yaml",
    )
    parser.add_argument(
        "--prompts-file",
        type=Path,
        default=HERE / "prompts.yaml",
    )
    parser.add_argument(
        "--variants",
        type=str,
        default=None,
        help="Comma-separated variant ids to include; defaults to all in --variants-file.",
    )
    parser.add_argument(
        "--prompts",
        type=str,
        default=None,
        help="Comma-separated prompt ids to include; defaults to all in --prompts-file.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help=(
            "One or more model identifiers. Defaults to claude-sonnet-4-6 for "
            "Claude and the Codex CLI default model for Codex."
        ),
    )
    parser.add_argument("--n", type=int, default=1, help="Reps per cell.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm token-bucket spend; required to actually run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output JSONL path. Default: results/run-<utc-ts>.jsonl "
            "alongside this script."
        ),
    )
    parser.add_argument(
        "--claude",
        type=str,
        default="claude",
        help="Path to the claude CLI. Default: 'claude' (resolved via PATH).",
    )
    parser.add_argument(
        "--codex",
        type=str,
        default="codex",
        help="Path to the codex CLI. Default: 'codex' (resolved via PATH).",
    )
    parser.add_argument(
        "--target-plugin",
        type=str,
        default="superpowers-beads",
        help=(
            "Plugin name used in the temp variant tree and in the activation "
            "match (plugin:skill)."
        ),
    )
    parser.add_argument(
        "--target-skill",
        type=str,
        default="using-superpowers",
        help="Skill name to detect activation for.",
    )
    parser.add_argument(
        "--cell-timeout",
        type=int,
        default=180,
        help="Per-cell subprocess timeout in seconds.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help=(
            "Number of cells to run in parallel via ThreadPoolExecutor. "
            "Default 4 — drop to 1 for strict sequential, raise only after "
            "a small pilot. If you see rate-limit events in stderr, lower this."
        ),
    )
    args = parser.parse_args(argv)

    variants_data = _load_yaml(args.variants_file)
    prompts_data = _load_yaml(args.prompts_file)

    variants = _filter(
        variants_data["variants"], _split_csv(args.variants), "id", "variants"
    )
    prompts = _filter(
        prompts_data["prompts"], _split_csv(args.prompts), "id", "prompts"
    )
    models = _resolve_models(args.harness, args.models)

    if not variants:
        raise SystemExit("no variants selected")
    if not prompts:
        raise SystemExit("no prompts selected")

    cells = _build_cells(variants, prompts, models, args.n)

    output = args.output
    if output is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = HERE / "results" / f"run-{ts}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)

    _print_preflight(
        cells,
        variants,
        prompts,
        models,
        args.n,
        output,
        args.concurrency,
        args.yes,
        harness=args.harness,
    )
    if not args.yes:
        return 1

    if args.harness == "claude":
        if shutil.which(args.claude) is None and not Path(args.claude).is_file():
            raise SystemExit(
                f"claude CLI not found at {args.claude!r}; pass --claude /path/to/claude"
            )
        _check_claude_version(args.claude)
    else:
        if shutil.which(args.codex) is None and not Path(args.codex).is_file():
            raise SystemExit(
                f"codex CLI not found at {args.codex!r}; pass --codex /path/to/codex"
            )

    work_root = Path(tempfile.mkdtemp(prefix="ab-test-"))
    plugin_dirs: dict[str, Path] = {}
    try:
        for variant in variants:
            plugin_dirs[variant["id"]] = build_variant_plugin(
                description=variant["description"],
                dest=work_root / f"plugin-{variant['id']}",
                plugin_name=args.target_plugin,
                skill_name=args.target_skill,
            )

        def worker(cell: dict) -> dict:
            try:
                if args.harness == "codex":
                    return _record_for_codex_cell(
                        cell=cell,
                        target_skill=args.target_skill,
                        workspace_dir=plugin_dirs[cell["variant_id"]],
                        codex_path=args.codex,
                        timeout_seconds=args.cell_timeout,
                    )
                return _record_for_cell(
                    cell=cell,
                    target_plugin=args.target_plugin,
                    target_skill=args.target_skill,
                    plugin_dir=plugin_dirs[cell["variant_id"]],
                    claude_path=args.claude,
                    timeout_seconds=args.cell_timeout,
                )
            except subprocess.TimeoutExpired:
                return _timeout_record(cell, args.cell_timeout)

        with output.open("w") as fh:
            for done_count, cell, record in execute_cells(
                cells, worker, concurrency=args.concurrency
            ):
                fh.write(json.dumps(record) + "\n")
                fh.flush()
                status = "ACT" if record.get("activated") else "----"
                tool = record.get("first_tool_call") or "(none)"
                print(
                    f"[{done_count}/{len(cells)}] variant={cell['variant_id']} "
                    f"prompt={cell['prompt_id']} model={cell['model']} rep={cell['rep']} "
                    f"-> {status} first_tool={tool}",
                    flush=True,
                )
    finally:
        shutil.rmtree(work_root, ignore_errors=True)

    print()
    print(f"Wrote {len(cells)} records to {output}")
    print()
    print(format_summary(summarize(output)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
