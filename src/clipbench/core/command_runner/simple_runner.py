from typing import List
from clipbench.core.command_runner.command_runner import CommandRunner
import subprocess
import timeit
from clipbench.core.registry import register


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


@register("simple_runner")
def factory_simple_runner(configuration: dict) -> SimpleRunner:
    return SimpleRunner(
        configuration.get("iterations", 10), configuration.get("iteration_timeout", 10)
    )
