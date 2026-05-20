import pytest

from clipbench.configuration.configuration import Configuration, ConfigurationBuilder


def test_builder_builds_configuration():
    search_config = {"name": "grid_sample"}
    runner_config = {"name": "c_runner", "timeout_seconds": 5.0}

    configuration = (
        ConfigurationBuilder()
        .set_search_method_configuration(search_config)
        .set_command_runner_configuration(runner_config)
        .set_budget(10)
        .build()
    )

    assert isinstance(configuration, Configuration)
    assert configuration.search_method_configuration == search_config
    assert configuration.command_runner_configuration == runner_config
    assert configuration.budget == 10


def test_builder_setters_are_chainable():
    builder = ConfigurationBuilder()

    assert builder.set_search_method_configuration({"name": "grid_sample"}) is builder
    assert builder.set_command_runner_configuration({"name": "c_runner"}) is builder
    assert builder.set_budget(3) is builder


def test_builder_copies_input_config_dicts():
    search_config = {"name": "grid_sample"}
    runner_config = {"name": "c_runner"}

    configuration = (
        ConfigurationBuilder()
        .set_search_method_configuration(search_config)
        .set_command_runner_configuration(runner_config)
        .set_budget(4)
        .build()
    )

    search_config["name"] = "changed"
    runner_config["name"] = "changed"

    assert configuration.search_method_configuration["name"] == "grid_sample"
    assert configuration.command_runner_configuration["name"] == "c_runner"


def test_builder_casts_budget_to_int():
    configuration = (
        ConfigurationBuilder()
        .set_search_method_configuration({"name": "grid_sample"})
        .set_command_runner_configuration({"name": "c_runner"})
        .set_budget("7")
        .build()
    )

    assert configuration.budget == 7


def test_builder_requires_non_empty_search_method_configuration():
    with pytest.raises(ValueError, match="search_method_configuration"):
        (
            ConfigurationBuilder()
            .set_search_method_configuration({})
            .set_command_runner_configuration({"name": "c_runner"})
            .set_budget(1)
            .build()
        )


def test_builder_requires_non_empty_command_runner_configuration():
    with pytest.raises(ValueError, match="command_runner_configuration"):
        (
            ConfigurationBuilder()
            .set_search_method_configuration({"name": "grid_sample"})
            .set_command_runner_configuration({})
            .set_budget(1)
            .build()
        )


@pytest.mark.parametrize("budget", [0, -1])
def test_builder_requires_positive_budget(budget):
    with pytest.raises(ValueError, match="budget"):
        (
            ConfigurationBuilder()
            .set_search_method_configuration({"name": "grid_sample"})
            .set_command_runner_configuration({"name": "c_runner"})
            .set_budget(budget)
            .build()
        )
