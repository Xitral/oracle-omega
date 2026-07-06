# Robustness Visualization Bundle

A robustness visualization bundle packages the evidence needed to inspect uncertainty behavior in ORACLE-Theater or another viewer.

It combines:

- the robustness report
- the nominal replay
- the directed stress replay, when a nominally allowed scenario can be pushed into review
- the buffered repair replay, when repair comparison is requested

## Bundle shape

```json
{
  "scenario_id": "example-corridor-speed-review",
  "scenario_family": "close_approach",
  "robustness_report": {},
  "nominal_replay": {},
  "stress_replay": null,
  "buffered_repair_replay": {}
}
```

## Use cases

### Fragile nominal path

A nominally allowed but fragile path should include:

- `nominal_replay`
- `stress_replay`
- robustness metrics showing nonzero failure probability

Example:

```powershell
python -m src.oracle_omega.robustness_bundle_cli oracle/scenarios/close_approach/fragile_corridor_pass.yaml --samples 100 --out data/bundles/fragile-corridor-bundle.json
```

### Already-failing repair case

An already-failing path should include:

- `nominal_replay`
- `buffered_repair_replay`
- robustness metrics showing original-vs-repaired risk reduction

Example:

```powershell
python -m src.oracle_omega.robustness_bundle_cli oracle/scenarios/example_corridor_speed_review.yaml --samples 100 --compare-repair --out data/bundles/corridor-speed-repair-bundle.json
```

## Research value

The bundle is designed to make the same run inspectable from three perspectives:

1. numerical robustness metrics
2. replay evidence
3. visual comparison between nominal, stress, and buffered repair paths

This allows ORACLE-Omega to support repeatable research claims and visual review from one artifact.
