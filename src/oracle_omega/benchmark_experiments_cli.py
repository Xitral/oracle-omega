from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.benchmark_experiments import run_benchmark_experiments


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ORACLE-Omega benchmark experiments for a scenario suite.")
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path("oracle/scenarios"),
        help="Scenario suite root to scan.",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="YAML check catalog path.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/experiments"),
        help="Experiment output root.",
    )
    parser.add_argument("--samples", type=int, default=100, help="Robustness sample count for every valid scenario.")
    parser.add_argument(
        "--index-out",
        type=Path,
        default=None,
        help="Optional experiment index JSON output path. Defaults to <out-dir>/index.json.",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=None,
        help="Optional benchmark summary Markdown output path. Defaults to <out-dir>/benchmark-summary.md.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_benchmark_experiments(
        suite_root=args.suite,
        rule_catalog_path=args.rules,
        output_root=args.out_dir,
        samples=args.samples,
        index_path=args.index_out,
        summary_path=args.summary_out,
    )
    print(json.dumps(summary.model_dump(mode="json"), indent=args.indent))


if __name__ == "__main__":
    main()
