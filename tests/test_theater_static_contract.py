from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEATER = ROOT / "web" / "index.html"


def test_theater_contains_3d_scene_contract():
    html = THEATER.read_text(encoding="utf-8")

    assert "scene-root" in html
    assert "importmap" in html
    assert "three.module.js" in html
    assert "three/addons/" in html
    assert 'from "three"' in html
    assert 'from "three/addons/controls/OrbitControls.js"' in html
    assert "OrbitControls" in html
    assert "WebGLRenderer" in html
    assert "PerspectiveCamera" in html
    assert "protected-volume" in html
    assert "approach-corridor" in html
    assert "replay-path-line" in html


def test_theater_contains_replay_loader_and_timeline_controls():
    html = THEATER.read_text(encoding="utf-8")

    assert "file-input" in html
    assert "timeline" in html
    assert "renderPayload" in html
    assert "focusFrame" in html
    assert "Focus primary violation" in html


def test_theater_default_replay_matches_fixture_scenario():
    html = THEATER.read_text(encoding="utf-8")

    assert "example-corridor-speed-review" in html
    assert "PATH-SPEED-001" in html
    assert "PATH-CORRIDOR-001" in html
    assert "primary_violation_time: 5" in html


def test_theater_displays_corrective_guidance_and_severity():
    html = THEATER.read_text(encoding="utf-8")

    assert "primary-recommendation" in html
    assert "highest_severity" in html
    assert "critical" in html
    assert "safety_margin" in html
    assert "normalized_margin" in html
    assert "Reduce segment speed" in html
    assert "Re-center the path" in html


def test_theater_supports_counterfactual_ghost_replay():
    html = THEATER.read_text(encoding="utf-8")

    assert "repair_candidate" in html
    assert "original_replay" in html
    assert "repaired_replay" in html
    assert "ghost-repair-path-line" in html
    assert "ghost-repair-marker" in html
    assert "ghostVehicle" in html
    assert "Counterfactual Repair" in html
