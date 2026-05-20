"""Command runner backed by the compiled cmd_runner helper executable."""

from clipbench.core.registry import (
    register_command_runner as register_instance,
    register_command_runner_configuration as register_configuration,
)

from clipbench.core.command_runner.command_runner import CommandRunner

import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import List, Optional

TIMEOUT_SENTINEL = -1e9
ERROR_SENTINEL = -2e9
OVERHEAD_CALIBRATION_COMMAND = "echo"


def _get_cmd_runner_path():
    """Resolve the cmd_runner executable path from supported install layouts."""
    name = "cmd_runner.exe" if sys.platform == "win32" else "cmd_runner"

    candidates = [
        # Source checkout layout.
        Path(__file__).resolve().parents[5] / "build" / name,
        # User-site install layout on Windows (e.g. AppData/Roaming/Python/bin).
        Path(__file__).resolve().parents[6] / "build" / name,
        # Virtualenv/global install fallback.
        Path(sys.prefix) / "bin" / name,
        # Scripts path fallback (primarily for Windows venv installs).
        Path(sysconfig.get_path("scripts")) / name,
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    locations = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"cmd_runner binary not found. Checked: {locations}")


def write_commands_to_file(commands: List[str], filepath: str):
    """Write one command per line to a UTF-8 text file."""
    with open(filepath, "w", encoding="utf-8") as f:
        for cmd in commands:
            f.write(cmd + "\n")


class CRunner(CommandRunner):
    """Execute command batches through cmd_runner and return timing-like scores."""

    def __init__(
        self,
        timeout: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
        overhead_measurement_runs: int = 0,
    ):
        """Configure batch timeout, per-command timeout, and overhead calibration."""
        super().__init__()
        # Outer timeout for the whole batch communication.
        self._timeout = timeout
        # Per-command timeout enforced by cmd_runner itself.
        self._timeout_seconds = timeout_seconds
        if overhead_measurement_runs < 0:
            raise ValueError("overhead_measurement_runs must be >= 0")
        self._overhead_measurement_runs = overhead_measurement_runs
        self._command_overhead: Optional[float] = None

    def _execute_batch(self, commands: list[str]) -> list[float]:
        """Run commands via cmd_runner and parse status lines into float results."""
        if not commands:
            return []

        # Resolve installed cmd_runner executable
        runner_path = _get_cmd_runner_path()

        runner_command = [runner_path]
        if self._timeout_seconds is not None:
            runner_command.append(str(self._timeout_seconds))

        # Prepare stdin payload (one command per line)
        stdin_payload = "\n".join(commands)
        if not stdin_payload.endswith("\n"):
            stdin_payload += "\n"

        try:
            proc = subprocess.Popen(
                runner_command,
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
            if ln == "TIMEOUT":
                results.append(TIMEOUT_SENTINEL)
                continue

            if ln.startswith("ERROR"):
                results.append(ERROR_SENTINEL)
                continue

            if ln.startswith("OK "):
                value_text = ln[3:].strip()
                try:
                    results.append(float(value_text))
                except ValueError as e:
                    raise ValueError(
                        f"Could not parse OK value on output line {i}: {ln!r}. "
                        f"Full stdout: {stdout!r}"
                    ) from e
                continue

            raise ValueError(
                f"Unknown cmd_runner status line {i}: {ln!r}. "
                f"Expected 'OK <float>', 'TIMEOUT', or 'ERROR <reason>'. "
                f"Stdout: {stdout!r} Stderr: {stderr!r}"
            )

        return results

    def _ensure_command_overhead(self) -> None:
        """Measure and cache average per-command runner overhead if enabled."""
        if self._command_overhead is not None:
            return

        if self._overhead_measurement_runs == 0:
            self._command_overhead = 0.0
            return

        calibration_commands = [
            OVERHEAD_CALIBRATION_COMMAND
        ] * self._overhead_measurement_runs
        calibration_results = self._execute_batch(calibration_commands)
        valid_results = [
            value
            for value in calibration_results
            if value != TIMEOUT_SENTINEL and value != ERROR_SENTINEL
        ]

        if not valid_results:
            raise RuntimeError(
                "Failed to measure c_runner overhead: all calibration commands failed"
            )

        self._command_overhead = sum(valid_results) / len(valid_results)

    def run(self, commands: list[str]) -> list[float]:
        """Execute commands and return results with calibrated overhead subtracted."""
        if not commands:
            return []

        self._ensure_command_overhead()
        command_results = self._execute_batch(commands)
        command_overhead = (
            self._command_overhead if self._command_overhead is not None else 0.0
        )

        adjusted_results: List[float] = []
        for value in command_results:
            if value == TIMEOUT_SENTINEL or value == ERROR_SENTINEL:
                adjusted_results.append(value)
            else:
                adjusted_results.append(max(0.0, value - command_overhead))

        return adjusted_results


@register_configuration("c_runner")
def configuration_c_runner() -> dict:
    """Return UI-facing configuration metadata for the c_runner backend."""

    return {
        "timeout": {
            "type": "float",
            "description": "Optional timeout in seconds for whole cmd_runner batch communication.",
            "default": None,
        },
        "timeout_seconds": {
            "type": "float",
            "description": "Optional timeout in seconds for each command executed by cmd_runner.",
            "default": None,
        },
        "overhead_measurement_runs": {
            "type": "int",
            "description": "Number of lightweight echo commands used to estimate and subtract c_runner command overhead.",
            "default": 0,
        },
    }


@register_instance("c_runner")
def factory_c_runner(configuration: dict) -> CRunner:
    """Build a CRunner instance from user configuration with defaults applied."""

    defaults = configuration_c_runner()
    default_timeout = defaults["timeout"]["default"]
    default_timeout_seconds = defaults["timeout_seconds"]["default"]
    default_overhead_measurement_runs = defaults["overhead_measurement_runs"]["default"]
    return CRunner(
        timeout=configuration.get("timeout", default_timeout),
        timeout_seconds=configuration.get("timeout_seconds", default_timeout_seconds),
        overhead_measurement_runs=configuration.get(
            "overhead_measurement_runs", default_overhead_measurement_runs
        ),
    )
