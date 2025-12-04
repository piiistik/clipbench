from typing import List
from clipex.core.command_runner.command_runner import CommandRunner
import subprocess
import timeit


# timeit runs subprocess multiple times and returns avg time
class SimpleRunner(CommandRunner):
    def __init__(self, iterations: int = 10, iteration_timeout: int = 10):
        super().__init__()

        self.__iterations = iterations
        self.__iteration_timeout = iteration_timeout

    def run(self, commands: List[str]) -> List[float]:
        results = []

        for command in commands:
            print(command)
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
