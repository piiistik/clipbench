import json

from clipbench.configuration.configuration import ConfigurationBuilder, Configuration


def provide_configuration(config_path: str) -> Configuration:
    with open(config_path, "r") as f:
        config_dict = json.load(f)

    return (
        ConfigurationBuilder()
        .set_budget(config_dict["budget"])
        .set_command_runner_configuration(config_dict["command_runner_configuration"])
        .set_search_method_configuration(config_dict["search_method_configuration"])
        .build()
    )
