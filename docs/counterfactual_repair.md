# Counterfactual Repair

ORACLE-Omega does not stop at detecting failed spatial checks. The counterfactual repair layer generates a minimally changed candidate path and re-runs the assurance review to measure whether the repair improved the scenario.

This is simulation-only research infrastructure. It is not a flight-control system, autonomy controller, or operational command generator.

## Research goal

The goal is to answer:

> What is the smallest scenario change that would have reduced or eliminated the detected spatial assurance failures?

This changes the system from a passive checker into a counterfactual reasoning tool.

## Current repair strategy

The first strategy is:

```text
counterfactual_minimal_path_change_v1
```

It applies deterministic repairs based on active starter checks:

- `radius_clearance`: pushes path samples outside the protected volume
- `corridor_limit`: clamps lateral offset back inside the approach corridor
- `tilt_limit`: clamps roll/pitch inside the tilt envelope
- `speed_limit`: retimes path samples so segment speed falls under the configured limit

After repair, ORACLE-Omega reviews the repaired scenario using the same check catalog.

## Repair evidence

A repair candidate reports:

- whether repair was available
- fixed rules
- remaining failures
- original failed count
- repaired failed count
- original severity
- repaired severity
- path delta score
- modified frame count
- repaired scenario
- repaired evidence

## Ghost replay

The counterfactual replay bundle contains:

- original replay
- repaired replay
- repair candidate metadata

ORACLE-Theater renders:

- original path as the primary blue path
- repaired path as a green ghost path
- original vehicle marker
- repaired ghost vehicle marker
- original violation markers
- repaired frame evidence for side-by-side comparison

## Research metrics unlocked

This layer enables experiments around:

- repair success rate
- violation count reduction
- primary violation elimination
- severity reduction
- path delta score
- modified-frame ratio
- remaining failure distribution

## Next research extensions

Future repair strategies should include:

- optimization-based repair
- uncertainty-aware repair
- repair under multiple competing objectives
- proof-carrying repair explanations
- repair search over alternate path topologies
- repair comparisons across scenario families
