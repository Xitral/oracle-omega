# Uncertainty Robustness Evaluation

ORACLE-Omega now supports uncertainty-aware scenario evaluation.

A deterministic scenario review asks whether one planned path satisfies the active check catalog. A robustness evaluation asks whether the scenario remains acceptable under plausible perturbations.

## Scenario uncertainty block

Scenarios can declare uncertainty assumptions inside `parameters`:

```yaml
parameters:
  uncertainty:
    position_sigma: {x: 0.02, y: 0.18, z: 0.05}
    timing_sigma: 0.2
    attitude_sigma_deg: {x: 0.4, y: 0.4, z: 0.2}
    samples: 100
    seed: 7
```

## Monte Carlo evaluation

The robustness engine generates perturbed scenario samples and reviews each sample with the same YAML check catalog.

The summary reports:

- sample count
- pass count
- fail count
- failure probability
- decision counts
- failure rule counts
- severity counts
- most common failure
- worst observed severity

## Directed stress search

In addition to random perturbations, ORACLE-Omega performs a deterministic directed stress search. It looks for a small directed path shift that changes a nominally acceptable scenario into a scenario requiring review.

Directed stress search is reserved for scenarios whose nominal decision is `ALLOW`. If the nominal scenario already requires review, the report records that stress search is not applicable.

The returned stress case includes:

- whether a failing perturbation was found
- triggered rule
- perturbation norm
- violation time
- perturbation direction
- perturbed scenario
- evidence for the perturbed scenario

## Repair robustness comparison

The robustness report can optionally compare the original path against an uncertainty-buffered repaired path.

This is different from deterministic repair:

- deterministic repair tries to make the exact scenario pass
- uncertainty-buffered repair tries to move the path away from the boundary so the repaired path stays safer under perturbation

The buffered repair currently applies conservative margins to:

- corridor offset
- protected-volume clearance
- roll and pitch tilt
- segment speed timing

## Adaptive buffered repair

Repair comparison now performs an adaptive buffer search. Instead of using a single fixed margin, ORACLE-Omega evaluates multiple sigma buffers and selects the first repaired path that reaches the target failure probability.

Current search:

```text
3.0σ, 4.0σ, 5.0σ, 6.0σ
```

Current target:

```text
failure_probability <= 0.01
```

The comparison records:

- selected sigma buffer
- target failure probability
- candidate failure probabilities for each tested buffer
- repaired failure probability
- risk reduction

This makes residual-risk cases inspectable rather than hidden.

The comparison reports:

- whether repair was available
- original failure probability
- repaired failure probability
- absolute risk reduction
- relative risk reduction
- original fail count
- repaired fail count
- fixed rules
- remaining failures

This answers a stronger research question than pass/fail repair:

> Did the repaired path become more robust under uncertainty?

## Example commands

Nominal robustness:

```powershell
python -m src.oracle_omega.robustness_cli oracle/scenarios/close_approach/fragile_corridor_pass.yaml --samples 100 --out data/robustness/fragile-corridor-robustness.json
```

Repair comparison:

```powershell
python -m src.oracle_omega.robustness_cli oracle/scenarios/example_corridor_speed_review.yaml --samples 100 --compare-repair --out data/robustness/corridor-speed-repair-robustness.json
```

## Research metrics unlocked

This subsystem enables experiments around:

- uncertainty failure probability
- scenario fragility
- common failure modes under perturbation
- worst-case perturbation magnitude
- robustness of repaired paths
- adaptive buffer selection
- sensitivity to check-catalog thresholds
- robustness differences across scenario families
- risk reduction after uncertainty-buffered repair

## Next extensions

Planned extensions:

- display uncertainty tubes in ORACLE-Theater
- display stress ghost paths in ORACLE-Theater
- compare original and repaired robustness reports in ORACLE-Theater
- add low-discrepancy sampling
- add optimization-based buffered repair objectives
