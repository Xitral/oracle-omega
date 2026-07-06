# External Adapters and Physics Checks

ORACLE-Omega now supports two research-extension layers:

1. local physics-derived checks
2. offline-first external vector-data adapters

The core benchmark suite remains deterministic. Live external API calls are optional and are not required for tests or release validation.

## Local physics checks

The first physics-derived check is `acceleration_limit`.

A rule can be added to a YAML check catalog like this:

```yaml
- id: PATH-ACCEL-001
  type: acceleration_limit
  families:
    - close_approach
    - surface_landing
  max_acceleration: 5.0
  reason: Path segment acceleration feasibility check.
  recommendation: Smooth the path timing or geometry before accepting the scenario.
```

The check estimates segment velocities from adjacent path samples, then estimates acceleration from the velocity change between neighboring segments.

This is still simulation-only. It is intended to flag path feasibility issues inside generated scenarios, not to operate a real system.

## JPL Horizons adapter

The Horizons adapter can build a URL for JPL Horizons vector queries, optionally fetch a live JSON response, and parse saved Horizons vector text from JSON fixtures.

Show the generated URL without fetching:

```powershell
python -m src.oracle_omega.adapters.horizons_cli --command 499 --center 500@399 --start 2026-01-01 --stop 2026-01-02 --step "1 h" --show-url
```

Fetch live data explicitly:

```powershell
python -m src.oracle_omega.adapters.horizons_cli --command 499 --center 500@399 --start 2026-01-01 --stop 2026-01-02 --step "1 h" --fetch --out data/external/horizons/mars_vectors.json
```

Parse a saved Horizons response:

```powershell
python -m src.oracle_omega.adapters.horizons_cli --input data/external/horizons/mars_vectors.json --out data/external/horizons/mars_series.json
```

## Scenario factory

Saved Horizons vector data can be converted into an ORACLE-Omega scenario YAML file:

```powershell
python -m src.oracle_omega.adapters.scenario_factory_cli --input data/external/horizons/mars_vectors.json --out oracle/scenarios/external/mars_vector_demo.yaml --scenario-id horizons-mars-demo --name "Horizons Mars Demo" --command 499 --center 500@399 --position-scale 0.001 --recenter
```

The generated scenario can then be reviewed with the normal pipeline:

```powershell
python -m src.oracle_omega.cli oracle/scenarios/external/mars_vector_demo.yaml
```

## Design rule

External data is normalized into ORACLE-Omega scenario YAML before entering the benchmark pipeline:

```text
JPL Horizons response
→ parsed vector series
→ ORACLE-Omega scenario YAML
→ standard review / robustness / benchmark pipeline
```

This keeps the research pipeline reproducible and prevents live network availability from affecting tests.
