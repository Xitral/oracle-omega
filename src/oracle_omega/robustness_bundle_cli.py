from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.robustness_bundle import build_robustness_visualization_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario


def write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build an ORACLE-Omega robustness visualization bundle.")
    parser.add_argument("scenario", type=Path, help="Path to a YAML scenario file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="Path to a YAML check catalog.",
    )
    parser.add_argument("--samples", type=int, default=None, help="Optional sample count override.")
    parser.add_argument(
        "--compare-repair",
        action="store_true",
        help="Include buffered repair replay and repair robustness comparison.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    parser.add_argument("--out", type=Path, default=None, help="Output path for the bundle JSON.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scenario = read_scenario(args.scenario)
    rules = read_rule_file(args.rules)
    bundle = build_robustness_visualization_bundle(
        scenario,
        rules,
        sample_override=args.samples,
        compare_repair=args.compare_repair,
    )
    payload = json.dumps(bundle.model_dump(mode="json"), indent=args.indent)
    print(payload)
    if args.out is not None:
        write_json(args.out, payload)


if __name__ == "__main__":
    main()
