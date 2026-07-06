# Reproducible Experiment Runs

ORACLE-Omega can package a scenario review into a reproducible experiment directory.

An experiment run records:

- scenario path
- scenario SHA-256 hash
- rule catalog path
- rule catalog SHA-256 hash
- engine version
- timestamp
- nominal evidence
- replay bundle
- optional robustness visualization bundle
- Markdown summary

## Basic experiment

```powershell
python -m src.oracle_omega.experiment_cli oracle/scenarios/close_approach/fragile_corridor_pass.yaml --experiment-id fragile-corridor-demo
```

This creates:

```text
data/experiments/fragile-corridor-demo/
  manifest.json
  summary.md
  evidence.json
  replay.json
```

## Robustness experiment

```powershell
python -m src.oracle_omega.experiment_cli oracle/scenarios/example_corridor_speed_review.yaml --robustness --samples 100 --compare-repair --experiment-id corridor-speed-repair-demo
```

This creates:

```text
data/experiments/corridor-speed-repair-demo/
  manifest.json
  summary.md
  evidence.json
  replay.json
  robustness_bundle.json
```

## Manifest

`manifest.json` is the run index. It records provenance and points to the generated artifacts.

Important fields:

- `experiment_id`
- `engine_version`
- `created_at_utc`
- `scenario_sha256`
- `rule_catalog_sha256`
- `decision`
- `failed_count`
- `highest_severity`
- `primary_rule_id`
- `robustness_enabled`
- `repair_comparison_enabled`
- `artifacts`

## Summary

`summary.md` is a human-readable research summary generated from the manifest.

It is intended for quick inspection, release notes, lab notebooks, and paper drafting.

## Evidence and replay

`evidence.json` stores the nominal review evidence.

`replay.json` stores the nominal 3D replay timeline.

If robustness is enabled, `robustness_bundle.json` stores the robustness report and visualization bundle for ORACLE-Theater.

## Research value

Experiment runs make ORACLE-Omega easier to audit and reproduce. Instead of only producing console output, each run becomes a timestamped artifact directory that records its inputs, outputs, and hashes.
