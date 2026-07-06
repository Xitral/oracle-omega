from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEATER = ROOT / "web" / "index.html"


def test_theater_contains_replay_loader_and_scene_layers():
    html = THEATER.read_text(encoding="utf-8")

    assert "file-input" in html
    assert "path-layer" in html
    assert "marker-layer" in html
    assert "renderReplay" in html
    assert "Focus primary violation" in html


def test_theater_default_replay_matches_fixture_scenario():
    html = THEATER.read_text(encoding="utf-8")

    assert "example-corridor-speed-review" in html
    assert "PATH-SPEED-001" in html
    assert "PATH-CORRIDOR-001" in html
    assert "primary_violation_time: 5" in html
