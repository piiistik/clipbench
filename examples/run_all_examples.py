#!/usr/bin/env python3
"""
Run clipbench on examples with comprehensive error handling.

This script can be run from any directory and allows:
  - Running all examples: python run_all_examples.py --all
  - Running a single example: python run_all_examples.py euclids_gcd
    - Running selected examples: python run_all_examples.py new_gradient_descend/maxima euclids_gcd/maxima

Examples are discovered by finding directories with experiment.xml and configuration.json.
"""

import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import traceback
import argparse


@dataclass
class ExampleResult:
    """Result of running clipbench on a single example."""

    path: Path
    success: bool
    error: Optional[str] = None
    traceback_str: Optional[str] = None


def find_examples(base_dir: Path, filter_name: Optional[str] = None) -> List[Path]:
    """
    Find all example directories containing experiment.xml and configuration.json.

    Args:
        base_dir: Base directory to search in
        filter_name: Optional filter to match only directories containing this name.
                     For example, "euclids_gcd" will match "euclids_gcd/broken" and "euclids_gcd/optimized"

    Returns:
        List of paths to valid example directories, sorted.
    """
    examples = []

    for directory in sorted(base_dir.rglob("*")):
        if not directory.is_dir():
            continue

        # Check if this directory has the required files for clipbench
        has_experiment = (directory / "experiment.xml").exists()
        has_config = (directory / "configuration.json").exists()

        if has_experiment and has_config:
            # Apply filter if specified
            if filter_name:
                if filter_name in str(directory):
                    examples.append(directory)
            else:
                examples.append(directory)

    return sorted(examples)


def run_clipbench(example_path: Path) -> ExampleResult:
    """
    Run clipbench on a single example directory.

    Args:
        example_path: Path to the example directory

    Returns:
        ExampleResult with success status and any error information.
    """
    try:
        # Check prerequisites
        if not (example_path / "experiment.xml").exists():
            return ExampleResult(
                path=example_path, success=False, error="Missing experiment.xml"
            )

        if not (example_path / "configuration.json").exists():
            return ExampleResult(
                path=example_path, success=False, error="Missing configuration.json"
            )

        # Run clipbench
        result = subprocess.run(
            [sys.executable, "-m", "clipbench.ui.cli.cli", str(example_path)],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per example
        )

        if result.returncode != 0:
            error_msg = f"clipbench exited with code {result.returncode}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr[:500]}"  # Truncate long errors
            return ExampleResult(path=example_path, success=False, error=error_msg)

        # Check that output files were created
        result_csv = example_path / "result.csv"
        analysis_json = example_path / "analysis.json"

        if not result_csv.exists():
            return ExampleResult(
                path=example_path,
                success=False,
                error="Output result.csv was not created",
            )

        if not analysis_json.exists():
            return ExampleResult(
                path=example_path,
                success=False,
                error="Output analysis.json was not created",
            )

        return ExampleResult(path=example_path, success=True)

    except subprocess.TimeoutExpired:
        return ExampleResult(
            path=example_path, success=False, error="Execution timed out (> 1 hour)"
        )
    except FileNotFoundError as e:
        return ExampleResult(
            path=example_path, success=False, error=f"File not found: {e}"
        )
    except Exception as e:
        return ExampleResult(
            path=example_path,
            success=False,
            error=f"{type(e).__name__}: {str(e)}",
            traceback_str=traceback.format_exc(),
        )


def is_valid_example_dir(path: Path) -> bool:
    """Return True if path contains a valid clipbench example setup."""
    return (
        path.is_dir()
        and (path / "experiment.xml").exists()
        and (path / "configuration.json").exists()
    )


def print_summary(results: List[ExampleResult]) -> None:
    """Print a nice summary of all results."""
    print("\n" + "=" * 80)
    print("CLIPBENCH EXECUTION SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print(f"\nTotal examples: {len(results)}")
    print(f"✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")

    if successful:
        print("\n--- SUCCESSFUL RUNS ---")
        for result in successful:
            rel_path = result.path.relative_to(Path.cwd())
            print(f"  ✓ {rel_path}")

    if failed:
        print("\n--- FAILED RUNS ---")
        for result in failed:
            rel_path = result.path.relative_to(Path.cwd())
            print(f"  ✗ {rel_path}")
            print(f"      Error: {result.error}")
            if result.traceback_str:
                print(f"      Traceback:\n{result.traceback_str}")

    print("\n" + "=" * 80)

    # Exit with error code if any failed
    if failed:
        print(f"\n⚠️  {len(failed)} example(s) failed. See details above.")
        sys.exit(1)
    else:
        print("\n✓ All examples completed successfully!")
        sys.exit(0)


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Run clipbench on examples with comprehensive error handling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_examples.py --all        # Run all examples
  python run_all_examples.py euclids_gcd  # Run euclids_gcd/broken and euclids_gcd/optimized
    python run_all_examples.py new_gradient_descend/maxima euclids_gcd/maxima
        """.strip(),
    )
    parser.add_argument(
        "examples",
        nargs="*",
        default=[],
        help="Specific examples to run (e.g., 'euclids_gcd', 'root_finding/minima')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all examples (default if no example specified)",
    )

    args = parser.parse_args()

    # Find the examples directory relative to this script
    script_dir = Path(__file__).parent
    examples_dir = script_dir

    # Validate that we're in/near the examples directory
    if not examples_dir.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        sys.exit(1)

    print(f"Using examples directory: {examples_dir}\n")

    # Determine selected examples
    if args.examples and not args.all:
        selected = []
        seen = set()

        for token in args.examples:
            # Prefer exact relative directory matches first.
            candidate = (examples_dir / token).resolve()
            if is_valid_example_dir(candidate):
                if candidate not in seen:
                    selected.append(candidate)
                    seen.add(candidate)
                continue

            # Fallback: substring match to support family names like "euclids_gcd".
            for match in find_examples(examples_dir, token):
                if match not in seen:
                    selected.append(match)
                    seen.add(match)

        examples = sorted(selected)
    else:
        examples = find_examples(examples_dir, None)

    if not examples:
        if args.examples and not args.all:
            joined = ", ".join(args.examples)
            print(f"❌ No examples found matching: {joined}")
            print(
                "   (looking for directories with experiment.xml and configuration.json)"
            )
            sys.exit(1)
        print("❌ No examples found (missing experiment.xml or configuration.json)")
        sys.exit(1)

    print(f"Found {len(examples)} example(s) to run:\n")
    for i, example_path in enumerate(examples, 1):
        rel_path = example_path.relative_to(examples_dir)
        print(f"  {i}. {rel_path}")

    print("\n" + "-" * 80)
    print("Starting clipbench execution...\n")

    # Run clipbench on each example
    results = []
    for i, example_path in enumerate(examples, 1):
        rel_path = example_path.relative_to(examples_dir)
        print(f"[{i}/{len(examples)}] Running: {rel_path}...", end=" ", flush=True)

        result = run_clipbench(example_path)
        results.append(result)

        if result.success:
            print("✓")
        else:
            print(f"✗ ({result.error})")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
