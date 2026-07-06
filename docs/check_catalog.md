# YAML Check Catalog

ORACLE-Omega uses YAML check catalogs to define simulation-only spatial assurance checks without changing Python code.

This is the first step toward a full rule DSL. The catalog is intentionally simple, explicit, and testable.

## Catalog shape

```yaml
catalog_id: oracle-omega-starter-checks
version: 0.2.0
description: Starter simulation-only spatial assurance check catalog for ORACLE-Omega.
checks:
  - id: PATH-SPEED-001
    type: speed_limit
    families:
      - close_approach
      - surface_landing
    max_speed: 0.65
    reason: Path segment speed check.
    recommendation: Reduce segment speed and regenerate the path preview before continuing.
```

The loader also accepts the legacy top-level key `rules`, but new catalogs should use `checks`.

## Supported check types

### `radius_clearance`

Required fields:

- `id`
- `type`
- `center`
- `radius`
- `reason`

Optional fields:

- `families`
- `recommendation`

### `tilt_limit`

Required fields:

- `id`
- `type`
- `max_deg`
- `reason`

Optional fields:

- `families`
- `recommendation`

### `corridor_limit`

Required fields:

- `id`
- `type`
- `max_offset`
- `reason`

Optional fields:

- `families`
- `recommendation`

### `speed_limit`

Required fields:

- `id`
- `type`
- `max_speed`
- `reason`

Optional fields:

- `families`
- `recommendation`

## Validation

The catalog loader rejects:

- malformed YAML structures
- missing `checks`
- non-mapping check entries
- duplicate check IDs
- unsupported check types
- missing required fields
- invalid family lists
- non-positive numeric limits
- malformed radius centers

## Research value

YAML-backed catalogs allow experiments to compare:

- different safety envelopes
- different scenario-family scopes
- different recommendation text
- stricter or looser speed, corridor, clearance, and tilt thresholds
- check activation coverage across a benchmark suite

This makes ORACLE-Omega configurable enough for repeated experiments instead of one fixed demo configuration.
