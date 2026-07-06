from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.experiment import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a reproducible ORACLE-Omega experiment run.")
    parser.add_argument("scenario", type=Path, help="Path to a YAML scenario file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="Path to a YAML check catalog.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/experiments"),
        help="Directory where experiment runs are written.",
    )
    parser.add_argument("--experiment-id", type=str, default=None, help="Optional explicit experiment ID.")
    parser.add_argument("--robustness", action="store_true", help="Include a robustness visualization bundle.")
    parser.add_argument("--samples", type=int, default=None, help="Optional robustness sample count.")
    parser.add_argument(
        "--compare-repair",
        action="store_true",
        help="Include buffered repair comparison in the robustness bundle.",
    )
    parser.add_argument("--tag", action="append", default=[], help="Optional experiment tag. Can be used more than once.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation for console manifest output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    manifest = run_experiment(
        scenario_path=args.scenario,
        rule_catalog_path=args.rules,
        output_root=args.out_dir,
        robustness=args.robustness,
        robustness_samples=args.samples,
        compare_repair=args.compare_repair,
        experiment_id=args.experiment_id,
        tags=args.tag,
    )
    print(json.dumps(manifest.model_dump(mode="json"), indent=args.indent))


if __name__ == "__main__":
    main()
