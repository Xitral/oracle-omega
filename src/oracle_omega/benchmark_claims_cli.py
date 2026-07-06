from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.oracle_omega.benchmark_claims import (
    build_benchmark_claims,
    load_analytics_report,
    render_claims_markdown,
    write_claim_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build ORACLE-Omega benchmark claim cards.")
    parser.add_argument(
        "--analytics",
        type=Path,
        default=Path("data/experiments/benchmark-analytics.json"),
        help="Benchmark analytics JSON path.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/experiments/benchmark-claims.json"),
        help="Output path for claim-card JSON.",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("data/experiments/benchmark-claims.md"),
        help="Output path for claim-card Markdown.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    analytics = load_analytics_report(args.analytics)
    claims = build_benchmark_claims(analytics)
    write_claim_outputs(claims, args.out, args.summary_out)
    print(json.dumps(claims.model_dump(mode="json"), indent=args.indent))
    print()
    print(render_claims_markdown(claims))


if __name__ == "__main__":
    main()
