# Research Suite Evaluation

ORACLE-Omega is designed to support repeatable spatial assurance experiments.

A single scenario review answers whether one simulated path satisfies the active checks. A suite evaluation runs many scenarios and produces aggregate metrics that can be used for regression testing, coverage analysis, and research reporting.

## Validation layer

Every loaded scenario is checked before review.

Current validation requirements:

- scenario family must be known
- planned path must contain at least one sample
- timestamps must be strictly increasing
- timestamps must be finite
- positions must be finite
- attitude values must be finite

Invalid scenarios are rejected during single-scenario review. During suite evaluation, invalid scenarios are recorded without stopping the full run.

## Check catalog layer

Suite runs are parameterized by a YAML check catalog.

The default catalog is:

```text
oracle/rules/starter_rules.yaml
```

Researchers can create alternate catalogs to compare stricter or looser spatial envelopes without changing Python code.

Example comparison dimensions:

- speed limits
- corridor limits
- clearance radius
- tilt envelope
- scenario-family scoping
- recommendation wording

## Suite output

The suite summary reports:

- total cases
- valid cases
- invalid cases
- decision counts
- severity counts
- scenario family counts
- primary rule counts
- per-case review metadata

## Example command

```powershell
python -m src.oracle_omega.cli --suite oracle/scenarios --out data/reports/scenario-suite-summary.json
```

## Research use

This lets the project answer questions such as:

- Which scenario families are covered?
- Which checks most often become the primary finding?
- How many scenarios require review?
- How often do critical findings appear?
- Which fixtures are malformed or scientifically unusable?
- How do findings change under alternate check catalogs?

This is the beginning of ORACLE-Omega as a benchmarkable research platform rather than a single-scenario demonstration.
