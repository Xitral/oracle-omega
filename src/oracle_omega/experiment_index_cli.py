from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.experiment_index import (
    build_benchmark_summary,
    build_experiment_index,
    write_index_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an ORACLE-Omega experiment index.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data/experiments"),
        help="Experiment root directory to scan.",
    )
    parser.add_argument(
        "--index-out",
        type=Path,
        default=Path("data/experiments/index.json"),
        help="Output path for index JSON.",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("data/experiments/benchmark-summary.md"),
        help="Output path for Markdown benchmark summary.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation for console output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    index = build_experiment_index(args.root)
    write_index_outputs(index, args.index_out, args.summary_out)
    print(json.dumps(index.model_dump(mode="json"), indent=args.indent))
    print()
    print(build_benchmark_summary(index))


if __name__ == "__main__":
    main()
