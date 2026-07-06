from __future__ import annotations

import argparse
from pathlib import Path

from src.oracle_omega.adapters.horizons import load_horizons_result, parse_horizons_vectors
from src.oracle_omega.adapters.scenario_factory import scenario_from_horizons_vectors, write_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build ORACLE-Omega scenario YAML from saved Horizons vector data.")
    parser.add_argument("--input", type=Path, required=True, help="Saved Horizons JSON response with a result field.")
    parser.add_argument("--out", type=Path, required=True, help="Scenario YAML output path.")
    parser.add_argument("--scenario-id", required=True, help="Scenario id to write.")
    parser.add_argument("--name", required=True, help="Scenario display name.")
    parser.add_argument("--family", default="close_approach", help="Scenario family.")
    parser.add_argument("--command", default=None, help="Optional source command metadata.")
    parser.add_argument("--center", default=None, help="Optional source center metadata.")
    parser.add_argument("--position-scale", type=float, default=0.001, help="Scale applied to Horizons km positions.")
    parser.add_argument("--max-samples", type=int, default=None, help="Optional maximum samples to include.")
    parser.add_argument("--recenter", action="store_true", help="Subtract the first vector position before scaling.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    text = load_horizons_result(args.input)
    series = parse_horizons_vectors(text, command=args.command, center=args.center)
    scenario = scenario_from_horizons_vectors(
        series,
        scenario_id=args.scenario_id,
        name=args.name,
        family=args.family,
        position_scale=args.position_scale,
        recenter=args.recenter,
        max_samples=args.max_samples,
    )
    write_scenario(scenario, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
