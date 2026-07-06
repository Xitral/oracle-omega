from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.replay import build_replay_bundle
from src.oracle_omega.rule_file import read_rule_file
from src.oracle_omega.scenario_file import read_scenario
from src.oracle_omega.reviewer import review
from src.oracle_omega.suite_runner import run_suite


def write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ORACLE-Omega scenario review or suite evaluation.")
    parser.add_argument("scenario", type=Path, nargs="?", help="Path to a YAML scenario file.")
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("oracle/rules/starter_rules.yaml"),
        help="Path to a YAML rule file.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output path for evidence JSON.")
    parser.add_argument(
        "--replay-out",
        type=Path,
        default=None,
        help="Optional output path for replay timeline JSON.",
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=None,
        help="Optional directory of scenario YAML files to evaluate as a research suite.",
    )
    return parser


def run_single_scenario(args: argparse.Namespace) -> None:
    if args.scenario is None:
        raise SystemExit("Provide a scenario path or use --suite.")

    scenario = read_scenario(args.scenario)
    rules = read_rule_file(args.rules)
    evidence = review(scenario, rules)
    payload = json.dumps(evidence.model_dump(mode="json"), indent=args.indent)

    print(payload)

    if args.out is not None:
        write_json(args.out, payload)

    if args.replay_out is not None:
        replay = build_replay_bundle(scenario, evidence)
        replay_payload = json.dumps(replay.model_dump(mode="json"), indent=args.indent)
        write_json(args.replay_out, replay_payload)


def run_suite_mode(args: argparse.Namespace) -> None:
    summary = run_suite(args.suite, args.rules)
    payload = json.dumps(summary.model_dump(mode="json"), indent=args.indent)
    print(payload)
    if args.out is not None:
        write_json(args.out, payload)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.suite is not None:
        run_suite_mode(args)
    else:
        run_single_scenario(args)


if __name__ == "__main__":
    main()
