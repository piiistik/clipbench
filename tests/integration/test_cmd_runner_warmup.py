import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="cmd_runner is Windows-only")
def test_cmd_runner_executes_first_command_twice_but_reports_once(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    runner_path = repo_root / "bin" / "cmd_runner.exe"

    if not runner_path.exists():
        pytest.skip("cmd_runner.exe not found in bin/")

    marker_file = tmp_path / "warmup_marker.txt"

    first_command = f'echo first>>"{marker_file}"'
    second_command = f'echo second>>"{marker_file}"'
    stdin_payload = f"{first_command}\n{second_command}\n"

    completed = subprocess.run(
        [str(runner_path)],
        input=stdin_payload,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr

    out_lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    assert len(out_lines) == 2
    assert out_lines[0].startswith("OK ")
    assert out_lines[1].startswith("OK ")

    written_lines = [
        line.strip() for line in marker_file.read_text(encoding="utf-8").splitlines()
    ]
    assert written_lines == ["first", "first", "second"]
