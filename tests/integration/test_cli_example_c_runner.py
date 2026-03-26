import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_runs_example_with_c_runner(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    work_example = tmp_path / "sleep_example"
    work_example.mkdir(parents=True, exist_ok=True)

    # Keep the shape of the real sleep example but use tiny ranges for fast integration testing.
    (work_example / "experiment.xml").write_text(
        """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Parts>
    <Static>
        .\\bin\\sleep.exe
    </Static>

    <Dynamic>
        <Int min=\"1\" max=\"3\" step=\"1\"/>
    </Dynamic>
</Parts>
""",
        encoding="utf-8",
    )

    (work_example / "configuration.json").write_text(
        json.dumps(
            {
                "command_runner_configuration": {
                    "name": "c_runner",
                    "timeout_seconds": 2.0,
                },
                "search_method_configuration": {"name": "grid_sample"},
                "budget": 3,
            }
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    env["MPLBACKEND"] = "Agg"

    completed = subprocess.run(
        [sys.executable, "-m", "clipbench.ui.cli.cli", str(work_example)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, (
        f"clipbench CLI failed.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
    )

    result_csv = work_example / "result.csv"
    assert result_csv.exists(), "Expected result.csv to be created by CLI run"

    with result_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert len(rows) > 1, "Expected at least one result row in result.csv"

    for row in rows[1:]:
        assert row, "Result row should not be empty"
        value = float(row[0])
        assert 0.0 <= value <= 1e9

    assert (work_example / "plot.jpg").exists(), "Expected plot.jpg to be generated"
