# Batch Benchmark Experiments

ORACLE-Omega can generate reproducible experiment runs for an entire scenario suite with one command.

The batch runner:

- scans every YAML scenario under a suite root
- skips invalid research stress fixtures
- runs robustness-enabled experiments for every valid scenario
- enables buffered repair comparison when the nominal scenario requires review
- tags each run by family, decision, severity, and repair status
- writes experiment folders
- generates `index.json`
- generates `benchmark-summary.md`

## Run the full scenario corpus

```powershell
python -m src.oracle_omega.benchmark_experiments_cli --suite oracle/scenarios --samples 100 --out-dir data/experiments
```

This writes one experiment folder per valid scenario:

```text
data/experiments/benchmark-<scenario-id>/
  manifest.json
  summary.md
  evidence.json
  replay.json
  robustness_bundle.json
```

It also writes:

```text
data/experiments/index.json
data/experiments/benchmark-summary.md
```

## Repair comparison behavior

For nominally allowed scenarios, the batch runner records uncertainty risk but does not generate a repair comparison.

For scenarios that require review, the batch runner enables buffered repair comparison automatically.

## Invalid scenarios

Invalid stress fixtures are skipped and recorded in the batch summary. This lets the benchmark corpus include negative validation cases without breaking experiment generation.

## Research value

The batch runner completes the research loop:

```text
scenario corpus
→ batch experiments
→ robustness bundles
→ repair comparisons
→ experiment index
→ benchmark summary
→ release validation
```

This makes it possible to evaluate ORACLE-Omega across the whole benchmark corpus instead of one scenario at a time.
