from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.benchmark_analytics import (
    build_benchmark_analytics,
    load_experiment_index,
    render_analytics_markdown,
    write_analytics_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build aggregate ORACLE-Omega benchmark analytics.")
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("data/experiments/index.json"),
        help="Experiment index JSON path.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/experiments/benchmark-analytics.json"),
        help="Output path for analytics JSON.",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("data/experiments/benchmark-analytics.md"),
        help="Output path for analytics Markdown summary.",
    )
    parser.add_argument(
        "--repair-success-threshold",
        type=float,
        default=0.05,
        help="Maximum repaired failure probability counted as a successful repair.",
    )
    parser.add_argument(
        "--include-manual-runs",
        action="store_true",
        help="Analyze all indexed experiments instead of benchmark-tagged runs only.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    index = load_experiment_index(args.index)
    report = build_benchmark_analytics(
        index,
        repair_success_threshold=args.repair_success_threshold,
        benchmark_only=not args.include_manual_runs,
    )
    write_analytics_outputs(report, args.out, args.summary_out)
    print(json.dumps(report.model_dump(mode="json"), indent=args.indent))
    print()
    print(render_analytics_markdown(report))


if __name__ == "__main__":
    main()
