from typing import Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np


def plot_heatmap(
    results: Dict[Tuple[int, ...], float | None], output_path: str
) -> None:
    """
    Plot a simple heatmap of results and save to file.

    Args:
        results: Dictionary mapping tuples of variable values to time results
        output_path: Path where the heatmap image will be saved
    """
    if not results:
        return

    # Extract data
    keys = list(results.keys())
    values = [results[k] for k in keys if results[k] is not None]

    if not values:
        return

    # For 2D case, create proper heatmap
    if len(keys[0]) == 2:
        # Get unique values for each dimension
        x_vals = sorted(set(k[0] for k in keys))
        y_vals = sorted(set(k[1] for k in keys))

        # Create grid
        grid = np.full((len(y_vals), len(x_vals)), np.nan)

        for (x, y), val in results.items():
            if val is not None:
                i = y_vals.index(y)
                j = x_vals.index(x)
                grid[i, j] = val

        plt.figure(figsize=(10, 8))
        plt.imshow(grid, cmap="viridis", aspect="auto")
        plt.colorbar(label="Time")
        plt.xlabel("var_1")
        plt.ylabel("var_2")
        plt.xticks(range(len(x_vals)), x_vals)
        plt.yticks(range(len(y_vals)), y_vals)
        plt.title("Results Heatmap")
    else:
        # For 1D or >2D, just plot as bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(values)), values)
        plt.xlabel("Configuration")
        plt.ylabel("Time")
        plt.title("Results")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
