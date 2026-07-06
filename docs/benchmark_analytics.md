# Benchmark Analytics

ORACLE-Omega can turn an experiment index into aggregate benchmark analytics.

The analytics layer answers corpus-level research questions such as:

- How often did buffered repair succeed?
- What was the mean original failure probability?
- What was the mean repaired failure probability?
- What was the mean risk reduction?
- Which nominal scenarios were fragile under uncertainty?
- Which repaired scenarios still had residual risk?
- Which rule families drove most failures?
- Which scenario families benefited most from repair?

## Generate analytics from an index

```powershell
python -m src.oracle_omega.benchmark_analytics_cli --index data/experiments/index.json --out data/experiments/benchmark-analytics.json --summary-out data/experiments/benchmark-analytics.md
```

By default, analytics only includes benchmark-tagged runs. To include manual experiment runs too:

```powershell
python -m src.oracle_omega.benchmark_analytics_cli --index data/experiments/index.json --include-manual-runs
```

## Batch runner integration

The batch benchmark runner writes analytics automatically:

```powershell
python -m src.oracle_omega.benchmark_experiments_cli --suite oracle/scenarios --samples 100 --out-dir data/experiments
```

This produces:

```text
data/experiments/index.json
data/experiments/benchmark-summary.md
data/experiments/benchmark-analytics.json
data/experiments/benchmark-analytics.md
```

## Key aggregate metrics

The analytics report includes:

- experiment count
- robustness experiment count
- repair comparison count
- fragile nominal count
- robust nominal count
- zero-risk repaired count
- remaining-risk repaired count
- repair success count
- repair success rate
- mean original failure probability
- mean repaired failure probability
- mean absolute risk reduction
- median absolute risk reduction
- mean relative risk reduction
- median relative risk reduction

## Grouped metrics

Analytics are grouped by:

- scenario family
- primary rule or most common failure mode

## Research value

The experiment index shows individual runs. Benchmark analytics turns those runs into claims that are easier to use in papers, release notes, and research summaries.

Example claim shape:

```text
Across benchmark-tagged experiments, buffered repair reduced mean failure probability from X to Y, with mean absolute risk reduction Z.
```
