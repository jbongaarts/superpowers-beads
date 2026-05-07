"""A/B harness entry point.

Runs combinatorial cells of (variant, prompt, model, rep), invokes the claude
CLI hermetically per cell, classifies whether Skill(<target>) fires as the
first tool action on turn 1, and writes per-run JSONL records.

Usage:
    python3 scripts/ab-test/run.py --n 1 --yes
    python3 scripts/ab-test/run.py --variants current,a --models sonnet --n 5 --yes
"""

import argparse
import json
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
from detect import analyze_stream
from report import format_summary, summarize
from runner import extract_usage, run_cell


def _load_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _resolve_models(models_arg: list[str] | None) -> list[str]:
    return models_arg or ["claude-sonnet-4-6"]


def _filter(items: list[dict], ids: list[str] | None, key: str) -> list[dict]:
    if not ids:
        return items
    wanted = set(ids)
    out = [i for i in items if i[key] in wanted]
    missing = wanted - {i[key] for i in items}
    if missing:
        raise SystemExit(f"unknown ids in --{key.split('_')[0]}s filter: {sorted(missing)}")
    return out


def _build_cells(
    variants: list[dict],
    prompts: list[dict],
    models: list[str],
    n: int,
) -> list[dict]:
    cells = []
    for variant in variants:
        for prompt in prompts:
            for model in models:
                for rep in range(n):
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


def _print_preflight(
    cells: list[dict],
    variants: list[dict],
    prompts: list[dict],
    models: list[str],
    n: int,
    output: Path,
    yes: bool,
) -> None:
    print(f"A/B harness preflight ({datetime.now(timezone.utc).isoformat()})")
    print(f"  variants: {len(variants)} -> {[v['id'] for v in variants]}")
    print(f"  prompts:  {len(prompts)} -> {[p['id'] for p in prompts]}")
    print(f"  models:   {len(models)} -> {models}")
    print(f"  reps:     {n}")
    print(f"  total cells: {len(cells)}")
    print(f"  output: {output}")
    print(
        "  auth: subscription via your installed `claude` CLI (Pro 5h bucket). "
        "Token usage is logged per cell so you can extrapolate."
    )
    if not yes:
        print()
        print("Refusing to start without --yes. Re-run with --yes to proceed.")


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
        "returncode": result["returncode"],
        "stderr_excerpt": (result["stderr"] or "")[:500],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the A/B activation-rate harness over (variant, prompt, model, rep) cells.",
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
        help="One or more model identifiers (e.g. claude-sonnet-4-6). Default: claude-sonnet-4-6.",
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
        help="Output JSONL path. Default: results/run-<utc-ts>.jsonl alongside this script.",
    )
    parser.add_argument(
        "--claude",
        type=str,
        default="claude",
        help="Path to the claude CLI. Default: 'claude' (resolved via PATH).",
    )
    parser.add_argument(
        "--target-plugin",
        type=str,
        default="superpowers-beads",
        help="Plugin name used in the temp variant tree and in the activation match (plugin:skill).",
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
    args = parser.parse_args(argv)

    variants_data = _load_yaml(args.variants_file)
    prompts_data = _load_yaml(args.prompts_file)

    variants = _filter(variants_data["variants"], _split_csv(args.variants), "id")
    prompts = _filter(prompts_data["prompts"], _split_csv(args.prompts), "id")
    models = _resolve_models(args.models)

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

    _print_preflight(cells, variants, prompts, models, args.n, output, args.yes)
    if not args.yes:
        return 1

    if shutil.which(args.claude) is None and not Path(args.claude).is_file():
        raise SystemExit(
            f"claude CLI not found at {args.claude!r}; pass --claude /path/to/claude"
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

        with output.open("w") as fh:
            for index, cell in enumerate(cells, start=1):
                print(
                    f"[{index}/{len(cells)}] variant={cell['variant_id']} "
                    f"prompt={cell['prompt_id']} model={cell['model']} rep={cell['rep']}",
                    flush=True,
                )
                try:
                    record = _record_for_cell(
                        cell=cell,
                        target_plugin=args.target_plugin,
                        target_skill=args.target_skill,
                        plugin_dir=plugin_dirs[cell["variant_id"]],
                        claude_path=args.claude,
                        timeout_seconds=args.cell_timeout,
                    )
                except subprocess.TimeoutExpired:
                    record = {
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
                        "duration_ms": args.cell_timeout * 1000,
                        "total_cost_usd": None,
                        "returncode": None,
                        "stderr_excerpt": "TIMEOUT",
                    }
                fh.write(json.dumps(record) + "\n")
                fh.flush()
                status = "ACT" if record.get("activated") else "----"
                tool = record.get("first_tool_call") or "(none)"
                print(f"    -> {status} first_tool={tool}", flush=True)
    finally:
        shutil.rmtree(work_root, ignore_errors=True)

    print()
    print(f"Wrote {len(cells)} records to {output}")
    print()
    print(format_summary(summarize(output)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
