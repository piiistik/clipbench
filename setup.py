import subprocess
import sys
import shutil
import runpy
import distutils.cmd
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.build import build as _build
from setuptools.command.install import install as _install

class build_examples:
    """Build example C programs only."""
    
    @staticmethod
    def compile_examples():
        """Compile all example C programs into build/ directory."""
        bin_out_dir = Path("build")
        bin_out_dir.mkdir(parents=True, exist_ok=True)
        
        if shutil.which("gcc") is None:
            raise RuntimeError(
                "gcc compiler not found in PATH; cannot build examples"
            )
        
        example_programs_dir = Path("examples/example_batch_programs")
        if example_programs_dir.exists():
            for c_src in sorted(example_programs_dir.glob("*.c")):
                out_name = f"{c_src.stem}.exe" if sys.platform == "win32" else c_src.stem
                out_path = bin_out_dir / out_name
                print(f"[build_examples] compiling {c_src} -> {out_path}")
                subprocess.check_call(
                    [
                        "gcc",
                        "-O2",
                        "-std=c11",
                        "-o",
                        str(out_path),
                        str(c_src),
                        "-lm",
                    ]
                )
            
            # Make executables on unix
            if sys.platform != "win32":
                for program in bin_out_dir.glob("*"):
                    if program.is_file() and program.suffix == "":
                        program.chmod(0o755)
        else:
            print("[build_examples] No example programs directory found")


class BuildExamplesCommand(_build):
    """Custom build command that does NOT build examples."""
    
    def run(self):
        # Just run normal build, examples are built separately
        super().run()


class build_py(_build_py):
    def run(self):
        project_root = Path(__file__).parent
        src_root = project_root / "src"

        # Generate input_file_editor HTML into build/ using the creator script.
        old_sys_path = list(sys.path)
        try:
            if str(src_root) not in sys.path:
                sys.path.insert(0, str(src_root))
            runpy.run_path(
                str(src_root / "input_file_editor" / "editor_creator.py"),
                run_name="__main__",
            )
        finally:
            sys.path = old_sys_path

        # Copy static result viewer HTML into build/.
        result_viewer_src = src_root / "result_viewer" / "result_viewer.html"
        result_viewer_dst = project_root / "build" / "result_viewer.html"
        if not result_viewer_src.exists():
            raise FileNotFoundError(
                f"result_viewer source not found: {result_viewer_src}"
            )
        result_viewer_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result_viewer_src, result_viewer_dst)
        print(f"[build] copied {result_viewer_src} -> {result_viewer_dst}")

        src = Path("src/clipbench/core/command_runner/c_runner/cmd_runner.c")
        stale_package_binary = Path("src/clipbench/core/command_runner/c_runner") / (
            "cmd_runner.exe" if sys.platform == "win32" else "cmd_runner"
        )
        bin_out_dir = Path("build")
        binary_name = "cmd_runner.exe" if sys.platform == "win32" else "cmd_runner"

        bin_out = bin_out_dir / binary_name

        if not src.exists():
            raise FileNotFoundError(f"cmd_runner source not found: {src}")

        if shutil.which("gcc") is None:
            raise RuntimeError(
                "gcc compiler not found in PATH; cannot build cmd_runner"
            )

        # Ensure no stale binary remains under the Python package directory.
        if stale_package_binary.exists():
            stale_package_binary.unlink()

        # Remove stale binaries from previous build outputs so wheel contents stay clean.
        build_root = Path("build")
        if build_root.exists():
            for stale in build_root.glob(
                "**/clipbench/core/command_runner/c_runner/cmd_runner*"
            ):
                if stale.is_file():
                    stale.unlink()

        bin_out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[build] compiling {src} -> {bin_out}")
        subprocess.check_call(
            [
                "gcc",
                "-O2",
                "-std=c11",
                "-o",
                str(bin_out),
                str(src),
            ]
        )

        # make executable on unix
        if sys.platform != "win32":
            bin_out.chmod(0o755)

        super().run()


class InstallCommand(_install):
    """Custom install command that ensures build_py runs first."""
    
    def run(self):
        # Ensure build_py runs before install
        self.run_command("build_py")
        # Then proceed with normal install
        super().run()
        
        # After install, try to copy build/ files to the proper location
        # This is optional - if it fails due to permissions, that's okay
        # The code has fallback paths to find cmd_runner in the source checkout
        build_dir = Path("build")
        if build_dir.exists():
            try:
                # Copy to Scripts directory in Python environment
                scripts_dir = Path(sys.prefix) / ("Scripts" if sys.platform == "win32" else "bin")
                scripts_dir.mkdir(parents=True, exist_ok=True)
                
                for file in build_dir.glob("*"):
                    if file.is_file():
                        dst = scripts_dir / file.name
                        try:
                            print(f"[install] copying {file} -> {dst}")
                            shutil.copy2(file, dst)
                            # Make executable on Unix
                            if sys.platform != "win32" and file.suffix == "":
                                dst.chmod(0o755)
                        except (PermissionError, OSError) as e:
                            print(f"[install] warning: could not copy {file.name}: {e}")
                            print(f"[install] cmd_runner will be found in source checkout during development")
            except (PermissionError, OSError) as e:
                print(f"[install] warning: could not copy build files to Scripts: {e}")
                print(f"[install] cmd_runner will be found in source checkout during development")


class BuildExamplesCmd(distutils.cmd.Command):
    """Custom command to build only the example C programs."""
    
    description = "build example C programs"
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        build_examples.compile_examples()


setup(
    cmdclass={
        "build_py": build_py, 
        "build": BuildExamplesCommand, 
        "build_examples": BuildExamplesCmd,
        "install": InstallCommand,
    }
)
