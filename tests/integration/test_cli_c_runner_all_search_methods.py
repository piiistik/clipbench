import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="c_runner integration tests are Windows-only")
class TestCliCRunnerAllSearchMethods:
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _ensure_cmd_runner(self) -> None:
        runner_path = self._repo_root() / "build" / "cmd_runner.exe"
        if not runner_path.exists():
            pytest.skip("cmd_runner.exe not found in build/")

    def _write_experiment(self, case_dir: Path) -> None:
        # Use a built-in Windows command to keep integration tests lightweight.
        (case_dir / "experiment.xml").write_text(
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Parts>
    <Static>cmd /c echo</Static>
    <Dynamic>
        <Int min=\"0\" max=\"4\" step=\"1\"/>
    </Dynamic>
    <Dynamic>
        <Int min=\"0\" max=\"4\" step=\"1\"/>
    </Dynamic>
</Parts>
""",
            encoding="utf-8",
        )

    def _write_configuration(self, case_dir: Path, search_config: dict) -> None:
        config = {
            "command_runner_configuration": {
                "name": "c_runner",
                "timeout_seconds": 2.0,
            },
            "search_method_configuration": search_config,
            "budget": 20,
        }
        (case_dir / "configuration.json").write_text(
            json.dumps(config),
            encoding="utf-8",
        )

    def _run_cli(self, case_dir: Path) -> subprocess.CompletedProcess:
        repo_root = self._repo_root()
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        env["MPLBACKEND"] = "Agg"

        return subprocess.run(
            [sys.executable, "-m", "clipbench.ui.cli.cli", str(case_dir)],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def _assert_result_csv_content(self, case_dir: Path) -> None:
        result_csv = case_dir / "result.csv"
        assert result_csv.exists(), "Expected result.csv to be created"

        with result_csv.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))

        assert len(rows) >= 2, "result.csv should contain header and at least one data row"
        assert rows[0], "result.csv header should not be empty"
        for row in rows[1:]:
            assert row, "result.csv data rows should not be empty"

    def _assert_analysis_json_content(self, case_dir: Path) -> None:
        analysis_path = case_dir / "analysis.json"
        assert analysis_path.exists(), "Expected analysis.json to be created"

        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))

        assert "variables" in analysis
        assert "importances_mean" in analysis
        assert "importances_std" in analysis
        assert "statistics" in analysis
        assert isinstance(analysis["variables"], list)
        assert isinstance(analysis["importances_mean"], list)
        assert isinstance(analysis["importances_std"], list)
        assert isinstance(analysis["statistics"], dict)

    def _run_case(self, tmp_path: Path, folder_name: str, search_config: dict) -> None:
        self._ensure_cmd_runner()
        case_dir = tmp_path / folder_name
        case_dir.mkdir(parents=True, exist_ok=True)

        self._write_experiment(case_dir)
        self._write_configuration(case_dir, search_config)

        completed = self._run_cli(case_dir)
        assert completed.returncode == 0, (
            "clipbench CLI failed\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )

        self._assert_result_csv_content(case_dir)
        self._assert_analysis_json_content(case_dir)

    def test_cli_with_grid_sample(self, tmp_path: Path):
        self._run_case(
            tmp_path,
            "grid_sample_case",
            {"name": "grid_sample"},
        )

    def test_cli_with_random_sample(self, tmp_path: Path):
        self._run_case(
            tmp_path,
            "random_sample_case",
            {
                "name": "random_sample",
                "random_seed": 42,
            },
        )

    def test_cli_with_local_extrema_search(self, tmp_path: Path):
        self._run_case(
            tmp_path,
            "local_extrema_case",
            {
                "name": "local_extrema_search",
                "random_seed": 42,
                "number_of_iterations": 4,
                "budget_fraction_per_iteration": 0.2,
                "sampler_type": "random_sample",
                "sampler_config": {"random_seed": 42},
            },
        )

    def test_cli_with_trend_search(self, tmp_path: Path):
        self._run_case(
            tmp_path,
            "trend_search_case",
            {
                "name": "trend_search",
                "random_seed": 42,
                "number_of_iterations": 4,
                "budget_fraction_initial": 0.2,
                "sampler_type": "random_sample",
                "sampler_config": {"random_seed": 42},
            },
        )
