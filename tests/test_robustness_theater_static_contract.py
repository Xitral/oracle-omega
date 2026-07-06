from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEATER = ROOT / "web" / "robustness.html"


def test_robustness_theater_contains_3d_scene_contract():
    html = THEATER.read_text(encoding="utf-8")

    assert "Robustness Theater" in html
    assert "scene-root" in html
    assert "importmap" in html
    assert 'from "three"' in html
    assert 'from "three/addons/controls/OrbitControls.js"' in html
    assert "WebGLRenderer" in html
    assert "PerspectiveCamera" in html
    assert "protected-volume" in html
    assert "approach-corridor" in html


def test_robustness_theater_supports_bundle_fields():
    html = THEATER.read_text(encoding="utf-8")

    assert "robustness_report" in html
    assert "nominal_replay" in html
    assert "stress_replay" in html
    assert "buffered_repair_replay" in html
    assert "failure_probability" in html
    assert "absolute_risk_reduction" in html
    assert "relative_risk_reduction" in html


def test_robustness_theater_renders_three_path_layers():
    html = THEATER.read_text(encoding="utf-8")

    assert "nominal-replay-path" in html
    assert "stress-replay-path" in html
    assert "buffered-repair-replay-path" in html
    assert "Blue = nominal" in html
    assert "Red = stress" in html
    assert "Green = buffered repair" in html


def test_robustness_theater_has_interactive_controls():
    html = THEATER.read_text(encoding="utf-8")

    assert "file-input" in html
    assert "timeline" in html
    assert "focus-primary" in html
    assert "renderBundle" in html
    assert "focusFrame" in html
