import subprocess
import sys
import shutil
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        src = Path("src/clipbench/core/command_runner/c_runner/cmd_runner.c")
        package_out_dir = Path("src/clipbench/core/command_runner/c_runner")
        bin_out_dir = Path("bin")
        binary_name = "cmd_runner.exe" if sys.platform == "win32" else "cmd_runner"

        package_out = package_out_dir / binary_name
        bin_out = bin_out_dir / binary_name

        if not src.exists():
            raise FileNotFoundError(f"cmd_runner source not found: {src}")

        if shutil.which("gcc") is None:
            raise RuntimeError("gcc compiler not found in PATH; cannot build cmd_runner")

        package_out_dir.mkdir(parents=True, exist_ok=True)
        bin_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[build] compiling {src} -> {package_out}")
        subprocess.check_call([
            "gcc",
            "-O2",
            "-std=c11",
            "-o",
            str(package_out),
            str(src),
        ])

        shutil.copy2(package_out, bin_out)
        print(f"[build] copied {package_out} -> {bin_out}")

        # make executable on unix
        if sys.platform != "win32":
            package_out.chmod(0o755)
            bin_out.chmod(0o755)

        super().run()


setup(cmdclass={"build_py": build_py})
