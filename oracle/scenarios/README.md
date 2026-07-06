# ORACLE-Omega Scenario Corpus

This directory is the initial benchmark corpus for ORACLE-Omega.

The corpus is intentionally split into valid research cases and invalid stress cases.

## Valid scenario families

### `close_approach`

Scenarios for path review near a protected spatial volume.

Current cases:

- `nominal.yaml`: expected to pass
- `corridor_drift.yaml`: path leaves the lateral corridor
- `excessive_speed.yaml`: path segment speed exceeds the starter limit
- `combined_failure.yaml`: multiple spatial checks fail in one path

### `surface_landing`

Scenarios for final surface-contact style review.

Current cases:

- `nominal.yaml`: expected to pass
- `tilt_failure.yaml`: attitude exceeds the tilt limit
- `clearance_failure.yaml`: protected-volume clearance fails
- `speed_failure.yaml`: segment speed exceeds the starter limit

## Stress cases

The `stress/` directory contains intentionally invalid fixtures. These are not meant to pass review. They exist to prove the validation and suite evaluation systems can reject malformed scenarios while still completing a benchmark run.

Current stress cases:

- `empty_path.yaml`
- `repeated_time.yaml`
- `unknown_family.yaml`

## Research purpose

The corpus supports repeatable evaluation of:

- scenario family coverage
- check activation coverage
- primary finding selection
- invalid input handling
- severity distribution
- regression behavior across code changes
