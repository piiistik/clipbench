import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Tuple, Dict, Optional

from src.clipex.core.search_method.random_sample import RandomSearchMethod
from src.clipex.core.search_method.island import IslandRandomCliffSearch

from interesting_functions import (
    complex_landscape_with_curved_cliff,
    square_with_maxima,
    square_with_minima,
    combine_maxima_with_ridge,
    combine_maxima_with_step,
    combine_minima_with_ridge,
    combine_minima_with_step,
    cliff_step,
    cliff_ridge,
    curved_cliff,
)


def _build_grid_from_fn(
    fn: Callable[[Tuple[int, int]], float],
    x_range: Tuple[int, int],
    y_range: Tuple[int, int],
    resolution: int,
) -> np.ndarray:
    x_lin = np.linspace(x_range[0], x_range[1], resolution).astype(int)
    y_lin = np.linspace(y_range[0], y_range[1], resolution).astype(int)
    X, Y = np.meshgrid(x_lin, y_lin)
    Z = np.zeros_like(X, dtype=float)
    for i in range(resolution):
        for j in range(resolution):
            Z[i, j] = fn((int(X[i, j]), int(Y[i, j])))
    return Z, (x_lin[0], x_lin[-1], y_lin[0], y_lin[-1])


def _build_grid_from_dict(
    values: Dict[Tuple[int, int], float],
    x_range: Tuple[int, int],
    y_range: Tuple[int, int],
    resolution: int,
) -> np.ndarray:
    x_lin = np.linspace(x_range[0], x_range[1], resolution).astype(int)
    y_lin = np.linspace(y_range[0], y_range[1], resolution).astype(int)
    X, Y = np.meshgrid(x_lin, y_lin)
    Z = np.full_like(X, fill_value=np.nan, dtype=float)
    for i in range(resolution):
        for j in range(resolution):
            key = (int(X[i, j]), int(Y[i, j]))
            if key in values:
                Z[i, j] = values[key]
    return Z, (x_lin[0], x_lin[-1], y_lin[0], y_lin[-1])


def plot_side_by_side(
    fn: Callable[[Tuple[int, int]], float],
    values: Dict[Tuple[int, int], float],
    x_range: Tuple[int, int] = (1, 1000),
    y_range: Tuple[int, int] = (1, 1000),
    resolution: int = 300,
    title_fn: str = "Function",
    title_vals: str = "Computed samples",
    show_difference: bool = False,
    cmap: str = "viridis",
    smooth: bool = True,  # <── NEW
):
    """
    Plot function evaluated on grid and precomputed values side-by-side.
    If show_difference=True, also plots (fn - values) as third subplot.

    New:
        smooth=True enables bilinear interpolation so plots look continuous.
    """

    # Build both grids
    Z_fn, extent = _build_grid_from_fn(fn, x_range, y_range, resolution)
    Z_vals, _ = _build_grid_from_dict(values, x_range, y_range, resolution)

    # Mask NaNs for transparent handling
    Z_vals_masked = np.ma.masked_invalid(Z_vals)

    # Determine color scale from valid entries
    valid_vals = np.concatenate(
        [
            Z_fn.flatten(),
            Z_vals_masked.compressed() if Z_vals_masked.count() > 0 else np.array([]),
        ]
    )
    if valid_vals.size == 0:
        vmin, vmax = np.nanmin(Z_fn), np.nanmax(Z_fn)
    else:
        vmin, vmax = np.nanmin(valid_vals), np.nanmax(valid_vals)

    # interpolation mode
    interp = "bilinear" if smooth else "nearest"

    ncols = 3 if show_difference else 2
    fig, axes = plt.subplots(1, ncols, figsize=(6 * ncols, 5), constrained_layout=True)

    if ncols == 2:
        ax_fn, ax_vals = axes
        ax_diff = None
    else:
        ax_fn, ax_vals, ax_diff = axes

    # Function heatmap
    im0 = ax_fn.imshow(
        Z_fn,
        extent=extent,
        origin="lower",
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation=interp,
    )  # <── SMOOTHING
    ax_fn.set_title(title_fn)
    ax_fn.set_xlabel("x")
    ax_fn.set_ylabel("y")

    # Precomputed samples heatmap
    im1 = ax_vals.imshow(
        Z_vals_masked,
        extent=extent,
        origin="lower",
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation=interp,
    )  # <── ALSO SMOOTHED
    ax_vals.set_title(title_vals)
    ax_vals.set_xlabel("x")
    ax_vals.set_ylabel("y")

    cbar = fig.colorbar(
        im1, ax=[ax_fn, ax_vals], orientation="vertical", fraction=0.045, pad=0.02
    )
    cbar.set_label("Value")

    # Difference plot
    if show_difference:
        Z_vals_filled = np.where(np.isnan(Z_vals), np.nan, Z_vals)
        with np.errstate(invalid="ignore"):
            Z_diff = Z_fn - Z_vals_filled

        Z_diff_masked = np.ma.masked_invalid(Z_diff)

        if Z_diff_masked.count() > 0:
            dmax = np.max(np.abs(Z_diff_masked))
            diff_vmin, diff_vmax = -dmax, dmax
        else:
            diff_vmin, diff_vmax = -1.0, 1.0

        im2 = ax_diff.imshow(
            Z_diff_masked,
            extent=extent,
            origin="lower",
            aspect="auto",
            cmap="coolwarm",
            vmin=diff_vmin,
            vmax=diff_vmax,
            interpolation=interp,  # <── SMOOTHED DIFFERENCE
        )
        ax_diff.set_title("Difference (fn - samples)")
        ax_diff.set_xlabel("x")
        ax_diff.set_ylabel("y")
        fig.colorbar(
            im2, ax=ax_diff, orientation="vertical", fraction=0.045, pad=0.02
        ).set_label("Difference")

    plt.suptitle("Side-by-side comparison", fontsize=16)
    plt.show()


if __name__ == "__main__":
    fn = square_with_maxima
    budget = 1000000

    method = RandomSearchMethod(
        search_space_definition=[(1, 1000), (1, 1000)],
        evaluation_function=fn,
        rng_seed=42,
    )
    # method = IslandRandomCliffSearch(
    #     search_space_definition=((1, 1000), (1, 1000)),
    #     evaluation_function=fn,
    #     division_factor=4,
    #     budget_per_step_coefficient=0.05,
    #     random_seed=42,
    # )
    searched = method.run(budget=budget)

    plot_side_by_side(fn, searched, resolution=300, show_difference=False, smooth=True)
