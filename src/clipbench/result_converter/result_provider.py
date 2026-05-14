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
        header = next(reader, None)
        if header is None:
            return results

        int_indices = [
            i for i, name in enumerate(header) if i != 0 and name.endswith("_int")
        ]
        has_new_schema = len(int_indices) > 0

        # Read each result row
        for row in reader:
            if row:
                time_value = float(row[0])
                if has_new_schema:
                    var_tuple = tuple(int(row[i]) for i in int_indices)
                else:
                    var_tuple = tuple(int(val) for val in row[1:])
                results[var_tuple] = time_value

    return results
