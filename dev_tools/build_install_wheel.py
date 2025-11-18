import subprocess
import glob
import os
from packaging.version import Version, InvalidVersion

def build_and_install():
    # Step 1: Run build
    print("Building package...")
    print(os.path.curdir)
    subprocess.run(["python", "-m", "build"], check=True)

    # Step 2: Find all .whl files in dist/
    wheel_files = glob.glob("dist/*.whl")
    if not wheel_files:
        raise FileNotFoundError("No .whl files found in 'dist/'")

    # Step 3: Extract versions and pick the highest
    def parse_version_from_filename(filename):
        # Example filename: clipex-0.0.1-py3-none-any.whl
        base = os.path.basename(filename)
        parts = base.split('-')
        try:
            return Version(parts[1])
        except (IndexError, InvalidVersion):
            return Version("0.0.0")

    latest_wheel = max(wheel_files, key=parse_version_from_filename)
    print(f"Latest wheel detected: {latest_wheel}")

    # Step 4: Install the latest wheel
    subprocess.run([
        "pip", "install", latest_wheel, "--force-reinstall", "--no-deps"
    ], check=True)

    print("Installation complete.")

if __name__ == "__main__":
    build_and_install()
