import json

import pytest

from clipbench.configuration.configuration import Configuration
from clipbench.configuration_converter.configuration_provider import provide_configuration


def test_provide_configuration_reads_valid_json(tmp_path):
    path = tmp_path / "configuration.json"
    path.write_text(
        json.dumps(
            {
                "search_method_configuration": {"name": "grid_sample"},
                "command_runner_configuration": {"name": "c_runner"},
                "budget": 9,
            }
        ),
        encoding="utf-8",
    )

    configuration = provide_configuration(str(path))

    assert isinstance(configuration, Configuration)
    assert configuration.search_method_configuration["name"] == "grid_sample"
    assert configuration.command_runner_configuration["name"] == "c_runner"
    assert configuration.budget == 9


def test_provide_configuration_raises_for_missing_file(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        provide_configuration(str(missing))


def test_provide_configuration_raises_for_invalid_json(tmp_path):
    path = tmp_path / "configuration.json"
    path.write_text("{ this is invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        provide_configuration(str(path))


def test_provide_configuration_raises_for_missing_required_keys(tmp_path):
    path = tmp_path / "configuration.json"
    path.write_text(
        json.dumps(
            {
                "budget": 5,
                "command_runner_configuration": {"name": "c_runner"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        provide_configuration(str(path))
