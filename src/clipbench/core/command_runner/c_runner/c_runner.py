from clipbench.core.registry import register
from clipbench.core.command_runner.command_runner import CommandRunner

import subprocess
import sys
from importlib import resources
from typing import List, Optional


def _get_cmd_runner_path():
    """
    Return the absolute path to the packaged cmd_runner executable.
    """
    pkg = "clipbench.core.command_runner.c_runner"
    name = "cmd_runner.exe" if sys.platform == "win32" else "cmd_runner"

    path = resources.files(pkg) / name
    if not path.exists():
        raise FileNotFoundError(f"cmd_runner binary not found at {path}")

    return str(path)


def write_commands_to_file(commands: List[str], filepath: str):
    """Utility function to write commands to a temporary file."""
    with open(filepath, "w", encoding="utf-8") as f:
        for cmd in commands:
            f.write(cmd + "\n")


class CRunner(CommandRunner):
    def __init__(self, timeout: Optional[float] = None):
        super().__init__()
        self._timeout = timeout

    def run(self, commands: list[str]) -> list[float]:
        """
        Run a list of shell commands via the cmd_runner binary and return a list of floats.
        """
        # Resolve installed cmd_runner executable
        runner_path = _get_cmd_runner_path()

        # Prepare stdin payload (one command per line)
        stdin_payload = "\n".join(commands)
        if not stdin_payload.endswith("\n"):
            stdin_payload += "\n"

        try:
            proc = subprocess.Popen(
                [runner_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to start cmd_runner at '{runner_path}': {e}"
            ) from e

        try:
            stdout, stderr = proc.communicate(stdin_payload, timeout=self._timeout)
        except subprocess.TimeoutExpired as e:
            proc.kill()
            try:
                proc.communicate(timeout=1)
            except Exception:
                pass
            raise RuntimeError(
                f"cmd_runner timed out after {self._timeout} seconds"
            ) from e
        except Exception as e:
            proc.kill()
            raise RuntimeError("Error communicating with cmd_runner") from e

        if proc.returncode != 0:
            raise RuntimeError(
                f"cmd_runner exited with code {proc.returncode}. "
                f"Stderr: {stderr.strip()!r}"
            )

        out_lines = [ln.strip() for ln in stdout.splitlines() if ln.strip() != ""]

        if len(out_lines) != len(commands):
            raise ValueError(
                f"Output line count mismatch: expected {len(commands)}, got {len(out_lines)}. "
                f"Stdout: {stdout!r} Stderr: {stderr!r}"
            )

        results: List[float] = []
        for i, ln in enumerate(out_lines):
            try:
                results.append(float(ln))
            except ValueError as e:
                raise ValueError(
                    f"Could not parse output line {i} as float: {ln!r}. "
                    f"Full stdout: {stdout!r}"
                ) from e

        return results


@register("c_runner")
def factory_c_runner(configuration: dict) -> CRunner:
    return CRunner()
