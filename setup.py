import subprocess
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        src = Path("src/clipbench/core/command_runner/c_runner/cmd_runner.c")
        out_dir = Path("src/clipbench/core/command_runner/c_runner")
        out = out_dir / ("cmd_runner.exe" if sys.platform == "win32" else "cmd_runner")

        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[build] compiling {src} -> {out}")
        subprocess.check_call([
            "gcc",
            "-O2",
            "-std=c11",
            "-o",
            str(out),
            str(src),
        ])

        # make executable on unix
        if sys.platform != "win32":
            out.chmod(0o755)

        super().run()


setup(cmdclass={"build_py": build_py})
