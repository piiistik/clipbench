from typing import Dict, Tuple
import csv


def provide_result(csv_file: str) -> Dict[Tuple[int, ...], float | None]:
    """
    Load results from a CSV file with time as floats and variables as integers.

    Args:
        csv_file: Path to the input CSV file

    Returns:
        Dictionary mapping tuples of variable values to time results
    """
    results = {}

    with open(csv_file, "r", newline="") as f:
        reader = csv.reader(f)

        # Skip header row
        next(reader, None)

        # Read each result row
        for row in reader:
            if row:
                # First column is time (float), remaining columns are variables (ints)
                time_value = float(row[0])
                var_tuple = tuple(int(val) for val in row[1:])
                results[var_tuple] = time_value

    return results
