# Robustness Theater

`web/robustness.html` is a focused ORACLE-Theater page for robustness visualization bundles.

It renders three path layers from one JSON artifact:

- blue: nominal replay
- red: directed stress replay
- green: buffered repair replay

It also displays robustness metrics such as failure probability, most common failure, stress perturbation size, repaired failure probability, and risk reduction.

## Generate a fragile nominal bundle

```powershell
python -m src.oracle_omega.robustness_bundle_cli oracle/scenarios/close_approach/fragile_corridor_pass.yaml --samples 100 --out data/bundles/fragile-corridor-bundle.json
```

Expected viewer behavior:

- blue nominal path is shown
- red stress path is shown
- green repair path is absent
- metrics show nonzero uncertainty failure probability

## Generate a buffered repair bundle

```powershell
python -m src.oracle_omega.robustness_bundle_cli oracle/scenarios/example_corridor_speed_review.yaml --samples 100 --compare-repair --out data/bundles/corridor-speed-repair-bundle.json
```

Expected viewer behavior:

- blue failing nominal path is shown
- green buffered repair path is shown
- red stress path is absent because the nominal scenario already requires review
- metrics show original-vs-repaired risk reduction

## Open locally

From the repository root:

```powershell
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/web/robustness.html
```

Use the file picker to load a bundle from `data/bundles/`.
