from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.adapters.horizons import (
    HorizonsQuery,
    build_horizons_url,
    fetch_horizons_json,
    load_horizons_result,
    parse_horizons_vectors,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch or parse JPL Horizons vector data for ORACLE-Omega.")
    parser.add_argument("--command", default="499", help="Horizons target command, for example 499 for Mars.")
    parser.add_argument("--center", default="500@399", help="Horizons center, for example 500@399 for Earth geocenter.")
    parser.add_argument("--start", default="2026-01-01", help="Start time passed to Horizons.")
    parser.add_argument("--stop", default="2026-01-02", help="Stop time passed to Horizons.")
    parser.add_argument("--step", default="1 h", help="Horizons step size.")
    parser.add_argument("--input", type=Path, default=None, help="Parse an existing saved Horizons JSON response instead of fetching.")
    parser.add_argument("--out", type=Path, default=None, help="Optional output JSON path.")
    parser.add_argument("--fetch", action="store_true", help="Perform a live Horizons API request.")
    parser.add_argument("--show-url", action="store_true", help="Print the generated Horizons URL.")
    parser.add_argument("--indent", type=int, default=2)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    query = HorizonsQuery(
        command=args.command,
        center=args.center,
        start_time=args.start,
        stop_time=args.stop,
        step_size=args.step,
    )

    if args.show_url:
        print(build_horizons_url(query))

    if args.input is not None:
        text = load_horizons_result(args.input)
        series = parse_horizons_vectors(text, command=args.command, center=args.center)
        payload = series.model_dump(mode="json")
    elif args.fetch:
        response = fetch_horizons_json(query)
        series = parse_horizons_vectors(str(response["result"]), command=args.command, center=args.center)
        payload = {"query_url": build_horizons_url(query), "raw_response": response, "series": series.model_dump(mode="json")}
    else:
        payload = {"query_url": build_horizons_url(query)}

    rendered = json.dumps(payload, indent=args.indent)
    print(rendered)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
