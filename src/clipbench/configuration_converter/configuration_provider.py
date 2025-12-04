import json

from clipbench.configuration.configuration import Configuration


def provide_configuration(config_path: str) -> Configuration:
    with open(config_path, "r") as f:
        config_dict = json.load(f)

    return Configuration(
        command_runner_configuration=config_dict["command_runner_configuration"],
        search_method_configuration=config_dict["search_method_configuration"],
        budget=config_dict["budget"],
    )