# Experiment Index

ORACLE-Omega can scan a directory of reproducible experiment runs and generate an aggregate research index.

This turns separate experiment folders into a benchmark archive.

## Generate experiment runs

Example fragile nominal run:

```powershell
python -m src.oracle_omega.experiment_cli oracle/scenarios/close_approach/fragile_corridor_pass.yaml --robustness --samples 100 --experiment-id fragile-corridor-demo --tag fragile
```

Example buffered repair run:

```powershell
python -m src.oracle_omega.experiment_cli oracle/scenarios/example_corridor_speed_review.yaml --robustness --samples 100 --compare-repair --experiment-id corridor-speed-repair-demo --tag repair
```

## Build the index

```powershell
python -m src.oracle_omega.experiment_index_cli --root data/experiments --index-out data/experiments/index.json --summary-out data/experiments/benchmark-summary.md
```

This writes:

```text
data/experiments/index.json
data/experiments/benchmark-summary.md
```

## Index fields

Each indexed experiment entry includes:

- experiment ID
- created timestamp
- scenario ID
- scenario family
- nominal decision
- failed count
- highest severity
- primary rule
- robustness flags
- original failure probability
- repaired failure probability
- absolute risk reduction
- relative risk reduction
- most common uncertainty failure
- scenario SHA-256
- rule catalog SHA-256
- artifact paths
- tags

## Benchmark summary

`benchmark-summary.md` contains a human-readable table for comparing experiments.

It is intended for:

- research notes
- release summaries
- paper drafting
- benchmark archive inspection

## Research value

The experiment index makes it possible to answer aggregate questions, such as:

- Which scenarios were nominally allowed but fragile?
- Which failing scenarios were repaired successfully?
- How much risk reduction did buffered repair produce?
- Which rule fails most often under uncertainty?
- Which scenario families need more benchmark coverage?
