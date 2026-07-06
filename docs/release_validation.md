# Release Validation Gates

ORACLE-Omega uses automated validation to catch research and compatibility regressions before release.

## GitHub Actions CI

The workflow is defined in:

```text
.github/workflows/ci.yml
```

It runs on:

- push
- pull request
- manual workflow dispatch

The matrix checks:

- Python 3.10
- Python 3.11
- Python 3.12

Each CI run performs:

1. package installation with dev dependencies
2. full pytest suite
3. scenario suite evaluation
4. robustness visualization bundle generation
5. reproducible experiment generation
6. release validation harness

## Local release validation

Run:

```powershell
python -m src.oracle_omega.validate_release --out data/reports/release-validation.json
```

The validation harness checks:

- scenario suite coverage
- valid and invalid stress scenario handling
- robustness bundle generation
- fragile nominal stress replay
- buffered repair risk reduction
- reproducible experiment artifacts
- scenario and rule catalog hashes
- replay Theater static contract
- robustness Theater static contract

## Why this matters

The project targets Python 3.10 and newer. CI is required because features that work locally on one Python version may fail on another.

The release validation harness is intended to be the final gate before publishing a research archive, creating a tagged release, or minting a new DOI.
