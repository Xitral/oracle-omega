# Replay Timeline Contract

ORACLE-Omega separates assurance evidence from visualization.

The assurance engine produces an evidence card. The replay builder converts that evidence plus the scenario path into a timeline that a future 3D interface can render.

## Replay bundle fields

- `scenario_id`: scenario identifier
- `scenario_family`: scenario category, such as `close_approach` or `surface_landing`
- `decision`: assurance decision
- `primary_rule_id`: first failed rule selected for timeline focus
- `primary_violation_time`: timestamp for the primary violation
- `frames`: ordered timeline frames

## Replay frame fields

- `t`: scenario timestamp
- `position`: object position for the frame
- `attitude_deg`: roll, pitch, yaw in degrees
- `active_markers`: rule markers active at that frame
- `is_primary_violation_frame`: whether the 3D view should focus this frame by default

## Marker fields

- `rule_id`: rule that created the marker
- `t`: marker timestamp
- `label`: short explanation for the marker
- `severity`: currently `review`

## Example export command

```powershell
python -m src.oracle_omega.cli oracle/scenarios/example_corridor_speed_review.yaml --replay-out data/replays/corridor-speed-replay.json
```
