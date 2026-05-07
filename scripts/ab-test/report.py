"""Summarize a JSONL run file into per-(variant, model) activation rates."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence


def _iter_rows(path: Path) -> Iterable[Mapping]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def summarize(path: Path) -> List[dict]:
    buckets: dict = defaultdict(
        lambda: {
            "n": 0,
            "activations": 0,
            "excluded_unvalidated": 0,
            "rate_limited": 0,
        }
    )
    order: list = []
    for row in _iter_rows(Path(path)):
        key = (row["variant_id"], row["model"])
        if key not in buckets:
            order.append(key)
        bucket = buckets[key]
        if not row.get("harness_validated", False):
            bucket["excluded_unvalidated"] += 1
            continue
        bucket["n"] += 1
        if row.get("rate_limit_status"):
            bucket["rate_limited"] += 1
        if row.get("activated"):
            bucket["activations"] += 1

    cells = []
    for key in order:
        b = buckets[key]
        rate = (b["activations"] / b["n"]) if b["n"] else 0.0
        cells.append(
            {
                "variant_id": key[0],
                "model": key[1],
                "n": b["n"],
                "activations": b["activations"],
                "activation_rate": rate,
                "excluded_unvalidated": b["excluded_unvalidated"],
                "rate_limited": b["rate_limited"],
            }
        )
    return cells


def format_summary(cells: Sequence[Mapping]) -> str:
    headers = ["variant", "model", "rate", "count", "excluded", "rate_limited"]
    rows = [
        [
            str(c["variant_id"]),
            str(c["model"]),
            f"{c['activations']}/{c['n']}" if c["n"] else "0/0",
            f"{c['activation_rate'] * 100:.0f}%" if c["n"] else "—",
            str(c["excluded_unvalidated"]),
            str(c.get("rate_limited", 0)),
        ]
        for c in cells
    ]
    widths = [
        max([len(headers[i])] + [len(r[i]) for r in rows])
        for i in range(len(headers))
    ]

    def fmt(parts):
        return "  ".join(p.ljust(widths[i]) for i, p in enumerate(parts))

    sep = "  ".join("-" * w for w in widths)
    lines = [fmt(headers), sep] + [fmt(r) for r in rows]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize an ab-test results JSONL into an activation-rate table."
    )
    parser.add_argument("results", type=Path, help="Path to results-*.jsonl")
    args = parser.parse_args(argv)

    cells = summarize(args.results)
    print(format_summary(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
