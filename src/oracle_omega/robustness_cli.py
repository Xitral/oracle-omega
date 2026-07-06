from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.robustness import build_robustness_report
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario


def write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ORACLE-Omega uncertainty robustness evaluation.")
    parser.add_argument("scenario", type=Path, help="Path to a YAML scenario file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="Path to a YAML check catalog.",
    )
    parser.add_argument("--samples", type=int, default=None, help="Optional sample count override.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output path for robustness JSON.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scenario = read_scenario(args.scenario)
    rules = read_rule_file(args.rules)
    report = build_robustness_report(scenario, rules, sample_override=args.samples)
    payload = json.dumps(report.model_dump(mode="json"), indent=args.indent)
    print(payload)
    if args.out is not None:
        write_json(args.out, payload)


if __name__ == "__main__":
    main()
