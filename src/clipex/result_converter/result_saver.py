from typing import Dict, Tuple
import csv


def save_result(results: Dict[Tuple[int, ...], float | None], csv_file: str) -> None:
    """
    Save results to a CSV file with time as floats and variables as integers.

    Args:
        results: Dictionary mapping tuples of variable values to time results
        csv_file: Path to the output CSV file
    """
    if not results:
        return

    # Determine the number of variables from the first key
    num_vars = len(next(iter(results.keys())))

    # Create header: 'time' followed by 'var_1', 'var_2', ..., 'var_n'
    header = ["time"] + [f"var_{i+1}" for i in range(num_vars)]

    # Write to CSV file
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # Write each result row
        for var_tuple, time_value in results.items():
            if time_value is not None:
                # First column is time (float), remaining columns are variables (ints)
                row = [time_value] + list(var_tuple)
                writer.writerow(row)
