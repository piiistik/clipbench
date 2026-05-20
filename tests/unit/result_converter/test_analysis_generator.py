import json
import os
import tempfile
from unittest.mock import Mock
import pytest

from clipbench.result_converter.analysis_generator import save_analysis, _compute_statistics


class MockExperiment:
    """Mock experiment for testing analysis_generator."""

    def __init__(self, num_vars: int = 2, max_int_per_var: int = 9):
        self.num_vars = num_vars
        self.max_int_per_var = max_int_per_var

    def get_search_space_definition(self):
        return tuple((0, self.max_int_per_var) for _ in range(self.num_vars))

    def get_variable_values(self, vector):
        return tuple(f"--var_{i+1} {v}" for i, v in enumerate(vector))


def test_save_analysis_basic():
    """Test basic analysis generation with simple search space."""
    results = {
        (0, 0): 1.0,
        (1, 0): 1.5,
        (2, 0): 2.0,
        (0, 1): 1.2,
        (1, 1): 1.8,
        (2, 1): 2.5,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # Verify file was created
        assert os.path.exists(json_file)

        # Verify JSON structure
        with open(json_file, "r") as f:
            analysis = json.load(f)

        assert "variables" in analysis
        assert "importances_mean" in analysis
        assert "importances_std" in analysis

        assert len(analysis["variables"]) == 2
        assert len(analysis["importances_mean"]) == 2
        assert len(analysis["importances_std"]) == 2

        assert analysis["variables"] == ["var_1", "var_2"]

        # Verify importances are normalized and sum to 1.0
        total = sum(analysis["importances_mean"])
        assert 0.99 < total < 1.01  # Allow small floating point error


def test_save_analysis_with_none_values():
    """Test that None values are filtered out correctly."""
    results = {
        (0, 0): 1.0,
        (1, 0): 1.5,
        (0, 1): None,  # This should be filtered out
        (1, 1): 2.0,
        (2, 1): 2.5,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # Verify file was created
        assert os.path.exists(json_file)

        with open(json_file, "r") as f:
            analysis = json.load(f)

        # Should still have 2 variables
        assert len(analysis["variables"]) == 2


def test_save_analysis_constant_values():
    """Test handling of constant y values (no variance)."""
    results = {
        (0, 0): 1.0,
        (1, 0): 1.0,
        (0, 1): 1.0,
        (1, 1): 1.0,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # Verify file was created
        assert os.path.exists(json_file)

        with open(json_file, "r") as f:
            analysis = json.load(f)

        # All importances should be zero
        assert all(v == 0.0 for v in analysis["importances_mean"])
        assert all(v == 0.0 for v in analysis["importances_std"])


def test_save_analysis_empty_results():
    """Test handling of empty results."""
    results = {}
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # File should not be created for empty results
        assert not os.path.exists(json_file)


def test_save_analysis_all_none_values():
    """Test handling of all None values."""
    results = {
        (0, 0): None,
        (1, 0): None,
        (0, 1): None,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # File should not be created (no valid results)
        assert not os.path.exists(json_file)


def test_save_analysis_single_sample():
    """Test handling of single sample (should be skipped)."""
    results = {
        (0, 0): 1.0,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        # File should not be created (need at least 2 samples)
        assert not os.path.exists(json_file)


def test_save_analysis_different_variable_counts():
    """Test with different numbers of variables."""
    # Test with 3 variables
    results = {
        (0, 0, 0): 1.0,
        (1, 0, 0): 1.5,
        (2, 0, 0): 2.0,
        (0, 1, 0): 1.2,
        (1, 1, 0): 1.8,
        (2, 1, 0): 2.5,
    }
    experiment = MockExperiment(num_vars=3)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        with open(json_file, "r") as f:
            analysis = json.load(f)

        assert len(analysis["variables"]) == 3
        assert analysis["variables"] == ["var_1", "var_2", "var_3"]


def test_save_analysis_with_negative_sentinel_values():
    """Test sentinel negative values are excluded from log-transformed modeling."""
    results = {
        (0, 0): 1.0,
        (1, 0): 2.0,
        (2, 0): -1e9,  # timeout sentinel
        (0, 1): -2e9,  # error sentinel
        (1, 1): 3.5,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        assert os.path.exists(json_file)

        with open(json_file, "r") as f:
            analysis = json.load(f)

    assert len(analysis["importances_mean"]) == 2
    assert len(analysis["importances_std"]) == 2
    assert analysis["statistics"]["sample_count"] == 5


# ---------------------------------------------------------------------------
# _compute_statistics unit tests
# ---------------------------------------------------------------------------

class MockExperimentForStats:
    """Mock experiment with configurable space definition for statistics tests."""

    def __init__(self, space_definition):
        # space_definition: tuple of (min_int, max_int) per variable
        self._space_definition = space_definition

    def get_search_space_definition(self):
        return self._space_definition

    def get_variable_values(self, vector):
        return tuple(f"--p{i+1} {v}" for i, v in enumerate(vector))


def _make_experiment_1d(max_int):
    return MockExperimentForStats(((0, max_int),))


def test_statistics_min_max_mean_median():
    results = {
        (0,): 1.0,
        (1,): 2.0,
        (2,): 3.0,
        (3,): 4.0,
        (4,): 5.0,
    }
    experiment = _make_experiment_1d(4)
    stats = _compute_statistics(results, experiment)

    assert stats["min"]["time"] == pytest.approx(1.0)
    assert stats["min"]["config_ints"] == [0]
    assert stats["min"]["config_values"] == ["--p1 0"]

    assert stats["max"]["time"] == pytest.approx(5.0)
    assert stats["max"]["config_ints"] == [4]
    assert stats["max"]["config_values"] == ["--p1 4"]

    assert stats["mean"] == pytest.approx(3.0)
    assert stats["median"] == pytest.approx(3.0)


def test_statistics_sample_count():
    results = {(i,): float(i) for i in range(7)}
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)
    assert stats["sample_count"] == 7


def test_statistics_coverage_full():
    # Space has 5 points (max_int=4 → indices 0..4), all evaluated
    results = {(i,): float(i + 1) for i in range(5)}
    experiment = _make_experiment_1d(4)
    stats = _compute_statistics(results, experiment)
    assert stats["coverage"] == pytest.approx(1.0)


def test_statistics_coverage_partial():
    # Space has 10 points, 5 evaluated
    results = {(i,): float(i + 1) for i in range(5)}
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)
    assert stats["coverage"] == pytest.approx(0.5)


def test_statistics_coverage_2d():
    # Space is 3×3 = 9 points; 3 evaluated
    results = {(0, 0): 1.0, (1, 1): 2.0, (2, 2): 3.0}
    experiment = MockExperimentForStats(((0, 2), (0, 2)))
    stats = _compute_statistics(results, experiment)
    assert stats["coverage"] == pytest.approx(3 / 9)


def test_statistics_no_outliers():
    # Evenly spaced values — IQR-based thresholds contain all points
    results = {(i,): float(i + 1) for i in range(10)}
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)
    assert stats["low_outliers"]["count"] == 0
    assert stats["high_outliers"]["count"] == 0
    assert stats["low_outliers"]["configs"] == []
    assert stats["high_outliers"]["configs"] == []


def test_statistics_high_outlier_detected():
    # Nine tightly clustered values + one extreme high value
    results = {(i,): 1.0 + i * 0.01 for i in range(9)}
    results[(9,)] = 1000.0
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)

    assert stats["high_outliers"]["count"] == 1
    assert stats["high_outliers"]["configs"][0]["time"] == pytest.approx(1000.0)
    assert stats["high_outliers"]["configs"][0]["config_ints"] == [9]
    assert stats["low_outliers"]["count"] == 0


def test_statistics_low_outlier_detected():
    # Nine tightly clustered values + one extreme low value
    results = {(i,): 10.0 + i * 0.01 for i in range(1, 10)}
    results[(0,)] = 0.0001
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)

    assert stats["low_outliers"]["count"] == 1
    assert stats["low_outliers"]["configs"][0]["time"] == pytest.approx(0.0001)
    assert stats["low_outliers"]["configs"][0]["config_ints"] == [0]
    assert stats["high_outliers"]["count"] == 0


def test_statistics_high_outliers_sorted_by_time_descending():
    # Two high outliers — verify they are stored highest-first
    results = {(i,): 1.0 + i * 0.01 for i in range(8)}
    results[(8,)] = 500.0
    results[(9,)] = 200.0
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)

    assert stats["high_outliers"]["count"] == 2
    times = [c["time"] for c in stats["high_outliers"]["configs"]]
    assert times == sorted(times, reverse=True)


def test_statistics_low_outliers_sorted_by_time_ascending():
    # Two low outliers — verify they are stored lowest-first
    results = {(i,): 10.0 + i * 0.01 for i in range(8)}
    results[(8,)] = 0.001
    results[(9,)] = 0.0001
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)

    assert stats["low_outliers"]["count"] == 2
    times = [c["time"] for c in stats["low_outliers"]["configs"]]
    assert times == sorted(times)


def test_statistics_outlier_threshold_values():
    import numpy as np
    values = [1.0 + i * 0.1 for i in range(10)]
    arr = np.array(values)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    expected_low = q1 - 1.5 * iqr
    expected_high = q3 + 1.5 * iqr

    results = {(i,): v for i, v in enumerate(values)}
    experiment = _make_experiment_1d(9)
    stats = _compute_statistics(results, experiment)

    assert stats["q1"] == pytest.approx(q1)
    assert stats["q3"] == pytest.approx(q3)
    assert stats["iqr"] == pytest.approx(iqr)
    assert stats["low_outliers"]["threshold"] == pytest.approx(expected_low)
    assert stats["high_outliers"]["threshold"] == pytest.approx(expected_high)


def test_statistics_config_values_resolved():
    # Verify config_values are filled via get_variable_values
    results = {(2, 3): 1.5, (0, 0): 0.5, (4, 4): 9.9}
    experiment = MockExperimentForStats(((0, 4), (0, 4)))
    stats = _compute_statistics(results, experiment)

    assert stats["min"]["config_ints"] == [0, 0]
    assert stats["min"]["config_values"] == ["--p1 0", "--p2 0"]
    assert stats["max"]["config_ints"] == [4, 4]
    assert stats["max"]["config_values"] == ["--p1 4", "--p2 4"]


def test_statistics_key_present_in_save_analysis_output():
    results = {
        (0, 0): 1.0,
        (1, 0): 1.5,
        (2, 0): 2.0,
        (0, 1): 1.2,
        (1, 1): 1.8,
        (2, 1): 2.5,
    }
    experiment = MockExperiment(num_vars=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = os.path.join(tmpdir, "analysis.json")
        save_analysis(results, json_file, experiment)

        with open(json_file, "r") as f:
            analysis = json.load(f)

    assert "statistics" in analysis
    stats = analysis["statistics"]
    assert "sample_count" in stats
    assert "coverage" in stats
    assert "min" in stats
    assert "max" in stats
    assert "mean" in stats
    assert "median" in stats
    assert "q1" in stats
    assert "q3" in stats
    assert "iqr" in stats
    assert "low_outliers" in stats
    assert "high_outliers" in stats

    assert stats["sample_count"] == 6
    assert stats["min"]["time"] <= stats["mean"] <= stats["max"]["time"]
