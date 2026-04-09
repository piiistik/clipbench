import subprocess

import pytest

from clipbench.core.command_runner.c_runner import c_runner


class _FakeProc:
    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    def communicate(self, _stdin_payload: str, timeout=None):
        if isinstance(timeout, Exception):
            raise timeout
        return self._stdout, self._stderr

    def kill(self):
        return None


def test_c_runner_parses_ok_lines(monkeypatch):
    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: _FakeProc("OK 0.100000\nOK 2.500000\n"),
    )

    runner = c_runner.CRunner()
    results = runner.run(["echo one", "echo two"])

    assert results == [0.1, 2.5]


def test_c_runner_maps_timeout_and_error_to_sentinel(monkeypatch):
    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: _FakeProc("OK 0.050000\nTIMEOUT\nERROR exit_code=1\n"),
    )

    runner = c_runner.CRunner()
    results = runner.run(["ok", "slow", "bad"])

    assert results == [
        0.05,
        c_runner.NON_SUCCESS_SENTINEL,
        c_runner.NON_SUCCESS_SENTINEL,
    ]


def test_c_runner_passes_per_command_timeout_argument(monkeypatch):
    popen_calls = []

    def _fake_popen(*args, **kwargs):
        popen_calls.append(args[0])
        return _FakeProc("OK 0.100000\n")

    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(subprocess, "Popen", _fake_popen)

    runner = c_runner.CRunner(timeout_seconds=1.25)
    runner.run(["echo hi"])

    assert popen_calls == [["C:/fake/cmd_runner.exe", "1.25"]]


def test_c_runner_raises_on_unknown_status_line(monkeypatch):
    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: _FakeProc("NOT_A_STATUS\n"),
    )

    runner = c_runner.CRunner()
    with pytest.raises(ValueError, match="Unknown cmd_runner status line"):
        runner.run(["echo bad"])


def test_c_runner_subtracts_measured_overhead(monkeypatch):
    popen_inputs = []

    def _fake_popen(*args, **kwargs):
        class _Proc:
            returncode = 0

            def communicate(self, stdin_payload: str, timeout=None):
                popen_inputs.append(stdin_payload)
                if stdin_payload == "echo\necho\n":
                    return "OK 0.010000\nOK 0.030000\n", ""
                return "OK 0.120000\nOK 0.080000\n", ""

            def kill(self):
                return None

        return _Proc()

    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(subprocess, "Popen", _fake_popen)

    runner = c_runner.CRunner(overhead_measurement_runs=2)
    results = runner.run(["cmd_a", "cmd_b"])

    assert popen_inputs == ["echo\necho\n", "cmd_a\ncmd_b\n"]
    # Average overhead is (0.01 + 0.03) / 2 = 0.02
    assert results == pytest.approx([0.1, 0.06])


def test_c_runner_calibrates_only_once(monkeypatch):
    popen_inputs = []

    def _fake_popen(*args, **kwargs):
        class _Proc:
            returncode = 0

            def communicate(self, stdin_payload: str, timeout=None):
                popen_inputs.append(stdin_payload)
                if stdin_payload == "echo\n":
                    return "OK 0.020000\n", ""
                return "OK 0.100000\n", ""

            def kill(self):
                return None

        return _Proc()

    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(subprocess, "Popen", _fake_popen)

    runner = c_runner.CRunner(overhead_measurement_runs=1)
    first = runner.run(["a"])
    second = runner.run(["b"])

    assert first == [0.08]
    assert second == [0.08]
    assert popen_inputs == ["echo\n", "a\n", "b\n"]


def test_c_runner_clamps_adjusted_values_to_zero(monkeypatch):
    def _fake_popen(*args, **kwargs):
        class _Proc:
            returncode = 0

            def communicate(self, stdin_payload: str, timeout=None):
                if stdin_payload == "echo\n":
                    return "OK 0.050000\n", ""
                return "OK 0.010000\n", ""

            def kill(self):
                return None

        return _Proc()

    monkeypatch.setattr(
        c_runner, "_get_cmd_runner_path", lambda: "C:/fake/cmd_runner.exe"
    )
    monkeypatch.setattr(subprocess, "Popen", _fake_popen)

    runner = c_runner.CRunner(overhead_measurement_runs=1)
    results = runner.run(["tiny"])

    assert results == [0.0]


def test_c_runner_rejects_negative_overhead_measurement_runs():
    with pytest.raises(ValueError, match="overhead_measurement_runs must be >= 0"):
        c_runner.CRunner(overhead_measurement_runs=-1)
