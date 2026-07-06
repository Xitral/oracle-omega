from src.oracle_omega.adapters.horizons import HorizonsQuery, build_horizons_url, parse_horizons_vectors
from src.oracle_omega.adapters.scenario_factory import scenario_from_horizons_vectors, scenario_to_yaml

HORIZONS_TEXT = """
Header text
$$SOE
2460310.500000000 = A.D. 2024-Jan-01 00:00:00.0000 TDB
 X = 1.000000000000000E+03 Y = 2.000000000000000E+03 Z = 3.000000000000000E+03
 VX= 1.000000000000000E+00 VY= 2.000000000000000E+00 VZ= 3.000000000000000E+00
2460310.541666667 = A.D. 2024-Jan-01 01:00:00.0000 TDB
 X = 1.100000000000000E+03 Y = 2.200000000000000E+03 Z = 3.300000000000000E+03
 VX= 1.100000000000000E+00 VY= 2.100000000000000E+00 VZ= 3.100000000000000E+00
$$EOE
Footer text
"""


def test_horizons_query_builder_uses_vectors_endpoint_parameters():
    url = build_horizons_url(
        HorizonsQuery(
            command="499",
            center="500@399",
            start_time="2026-01-01",
            stop_time="2026-01-02",
            step_size="1 h",
        )
    )

    assert url.startswith("https://ssd.jpl.nasa.gov/api/horizons.api?")
    assert "COMMAND=%27499%27" in url
    assert "EPHEM_TYPE=%27VECTORS%27" in url
    assert "CENTER=%27500%40399%27" in url
    assert "STEP_SIZE=%271+h%27" in url


def test_horizons_vector_parser_extracts_state_samples():
    series = parse_horizons_vectors(HORIZONS_TEXT, command="499", center="500@399")

    assert series.command == "499"
    assert series.center == "500@399"
    assert len(series.samples) == 2
    assert series.samples[0].position_km.x == 1000.0
    assert series.samples[1].velocity_km_s.z == 3.1


def test_horizons_scenario_factory_writes_valid_scenario_yaml():
    series = parse_horizons_vectors(HORIZONS_TEXT, command="499", center="500@399")
    scenario = scenario_from_horizons_vectors(
        series,
        scenario_id="horizons-mars-demo",
        name="Horizons Mars Demo",
        position_scale=0.001,
        recenter=True,
    )
    text = scenario_to_yaml(scenario)

    assert scenario.id == "horizons-mars-demo"
    assert scenario.family == "close_approach"
    assert scenario.planned_path[0].t == 0.0
    assert scenario.planned_path[0].position.x == 0.0
    assert scenario.planned_path[1].position.x == 0.1
    assert "external_source: JPL Horizons" in text
