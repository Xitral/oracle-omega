from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review an ORACLE-Omega scenario file.")
    parser.add_argument("scenario", type=Path, help="Path to a YAML scenario file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="Path to a YAML rule file.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scenario = read_scenario(args.scenario)
    rules = read_rule_file(args.rules)
    evidence = review(scenario, rules)

    print(json.dumps(evidence.model_dump(mode="json"), indent=args.indent))


if __name__ == "__main__":
    main()
