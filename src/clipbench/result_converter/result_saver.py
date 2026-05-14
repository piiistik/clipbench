from typing import Callable, Dict, Tuple
import csv


def save_result(
    results: Dict[Tuple[int, ...], float | None],
    csv_file: str,
    vector_to_values: Callable[[Tuple[int, ...]], Tuple[str, ...]] | None = None,
) -> None:
    """
    Save results to a CSV file with time as floats and variables as integers.

    Args:
        results: Dictionary mapping tuples of variable values to time results
        csv_file: Path to the output CSV file
        vector_to_values: Optional converter from variable index vector to display values
    """
    if not results:
        return

    # Determine the number of variables from the first key
    num_vars = len(next(iter(results.keys())))

    if vector_to_values is None:
        header = ["time"] + [f"var_{i+1}" for i in range(num_vars)]
    else:
        int_header = [f"var_{i+1}_int" for i in range(num_vars)]
        value_header = [f"var_{i+1}_value" for i in range(num_vars)]
        header = ["time"] + int_header + value_header

    # Write to CSV file
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # Write each result row
        for var_tuple, time_value in results.items():
            if time_value is not None:
                row = [time_value] + list(var_tuple)
                if vector_to_values is not None:
                    row += list(vector_to_values(var_tuple))
                writer.writerow(row)
