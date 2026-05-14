import json
import os
import tempfile
from unittest.mock import Mock
import pytest

from clipbench.result_converter.analysis_generator import save_analysis


class MockExperiment:
    """Mock experiment for testing analysis_generator."""

    def __init__(self, num_vars: int = 2):
        self.num_vars = num_vars


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
