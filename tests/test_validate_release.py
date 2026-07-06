from src.oracle_omega.validate_release import run_release_validation


def test_release_validation_harness_passes_core_gates():
    report = run_release_validation()

    assert report.passed is True
    names = {check.name for check in report.checks}
    assert names == {
        "scenario-suite",
        "robustness-bundles",
        "experiment-run",
        "theater-contracts",
    }
    assert all(check.passed for check in report.checks)
