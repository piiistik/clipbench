from typing import List
from clipbench.core.command_runner.command_runner import CommandRunner
import subprocess
import timeit
from clipbench.core.registry import (
    register_command_runner as register_instance,
    register_command_runner_configuration as register_configuration,
)


# timeit runs subprocess multiple times and returns avg time
class SimpleRunner(CommandRunner):
    def __init__(self, iterations: int = 10, iteration_timeout: int = 10):
        super().__init__()

        self.__iterations = iterations
        self.__iteration_timeout = iteration_timeout

    def run(self, commands: List[str]) -> List[float]:
        results = []

        for command in commands:
            results.append(self.__benchmark_command(command))

        return results

    def __benchmark_command(self, command: str) -> float:
        return (
            timeit.timeit(
                lambda: subprocess.run(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    timeout=self.__iteration_timeout,
                ),
                number=self.__iterations,
            )
            / self.__iterations
        )


@register_configuration("simple_runner")
def configuration_simple_runner() -> dict:
    return {
        "iterations": {
            "type": "int",
            "description": "Number of iterations to run each command for timing",
            "default": 10,
        },
        "iteration_timeout": {
            "type": "int",
            "description": "Timeout in seconds for each individual command execution",
            "default": 10,
        },
    }


@register_instance("simple_runner")
def factory_simple_runner(configuration: dict) -> SimpleRunner:
    default_iterations = configuration_simple_runner()["iterations"]["default"]
    default_iteration_timeout = configuration_simple_runner()["iteration_timeout"][
        "default"
    ]
    return SimpleRunner(
        configuration.get("iterations", default_iterations),
        configuration.get("iteration_timeout", default_iteration_timeout),
    )
