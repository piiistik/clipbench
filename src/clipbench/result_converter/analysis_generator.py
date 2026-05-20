import json
import logging
import math
from typing import Dict, List, Tuple
import numpy as np

"""Generate analysis summaries and statistics from benchmark results."""

from clipbench.core.search_space import SearchSpace, VariableVector
from clipbench.experiment.experiment import Experiment

logger = logging.getLogger(__name__)


def save_analysis(
    results: SearchSpace,
    json_file: str,
    experiment: Experiment,
) -> None:
    """Compute variable importance and statistics, then save them as JSON."""
    # Filter out None values from results
    valid_results = {
        vector: time_value
        for vector, time_value in results.items()
        if time_value is not None
    }

    if not valid_results:
        logger.warning("No valid results to analyze. Skipping analysis.")
        return

    # Check if we have enough samples and variance
    if len(valid_results) < 2:
        logger.warning(
            "Insufficient samples for analysis (need at least 2). Skipping analysis."
        )
        return

    analyzable_results = {
        vector: time_value
        for vector, time_value in valid_results.items()
        if np.isfinite(time_value) and time_value > -1.0
    }

    if len(analyzable_results) < len(valid_results):
        logger.warning(
            "Skipping %d non-finite or non-positive runtime values for importance analysis.",
            len(valid_results) - len(analyzable_results),
        )

    sample_vector = next(iter(valid_results.keys()))

    if len(analyzable_results) < 2:
        logger.warning(
            "Insufficient analyzable samples after filtering invalid runtimes. Setting all importances to zero."
        )
        num_vars = len(sample_vector)
        analysis = _create_analysis_output(
            experiment, sample_vector, np.zeros(num_vars), np.zeros(num_vars)
        )
    else:
        # Convert to numpy arrays for sklearn
        vectors = list(analyzable_results.keys())
        X = np.array(vectors, dtype=np.float64)
        y = np.array([analyzable_results[v] for v in vectors], dtype=np.float64)

        # Runtime data is typically skewed and multiplicative, so log scaling makes
        # the analysis more stable and the importance scores more meaningful.
        y = np.log1p(y)

        if np.std(y) == 0:
            logger.warning(
                "No variance in analyzable results. Setting all importances to zero."
            )
            num_vars = len(sample_vector)
            analysis = _create_analysis_output(
                experiment, sample_vector, np.zeros(num_vars), np.zeros(num_vars)
            )
        else:
            # Train RandomForest and compute permutation importance
            try:
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.inspection import permutation_importance
            except ImportError:
                logger.error(
                    "scikit-learn is required for analysis. Install with: pip install scikit-learn"
                )
                return

            model = RandomForestRegressor(
                n_estimators=100, random_state=42, n_jobs=-1, max_depth=10
            )
            model.fit(X, y)

            result = permutation_importance(
                model, X, y, n_repeats=10, random_state=42, n_jobs=-1
            )

            importance_mean = result.importances_mean
            importance_std = result.importances_std

            # Warn if too few samples
            if len(X) < 20:
                logger.warning(
                    f"Small sample size ({len(X)} samples). Importance estimates may be unreliable."
                )

            analysis = _create_analysis_output(
                experiment, sample_vector, importance_mean, importance_std
            )

    analysis["statistics"] = _compute_statistics(valid_results, experiment)

    # Write to JSON file
    with open(json_file, "w") as f:
        json.dump(analysis, f, indent=2)

    logger.info(f"Analysis saved to {json_file}")


def _create_analysis_output(
    experiment: Experiment,
    sample_vector: VariableVector,
    importance_mean: np.ndarray,
    importance_std: np.ndarray,
) -> Dict:
    """Build the JSON-ready importance payload for each variable."""
    num_vars = len(sample_vector)
    variable_names = [f"var_{i+1}" for i in range(num_vars)]

    # Normalize importances to sum to 1.0 (if there's any variance)
    total = np.sum(importance_mean)
    if total > 0:
        importance_mean_normalized = importance_mean / total
        importance_std_normalized = (
            importance_std / total if total > 0 else importance_std
        )
    else:
        importance_mean_normalized = importance_mean
        importance_std_normalized = importance_std

    return {
        "variables": variable_names,
        "importances_mean": importance_mean_normalized.tolist(),
        "importances_std": importance_std_normalized.tolist(),
    }


_MAX_OUTLIER_CONFIGS = 20


def _compute_statistics(
    valid_results: SearchSpace,
    experiment: Experiment,
) -> Dict:
    """Compute summary stats, outliers, and search-space coverage."""
    times = np.array(list(valid_results.values()), dtype=np.float64)
    vectors: List[VariableVector] = list(valid_results.keys())

    min_idx = int(np.argmin(times))
    max_idx = int(np.argmax(times))

    q1, median, q3 = np.percentile(times, [25, 50, 75])
    iqr = float(q3 - q1)
    low_threshold = float(q1 - 1.5 * iqr)
    high_threshold = float(q3 + 1.5 * iqr)

    def _config_entry(vector: VariableVector, time: float) -> Dict:
        return {
            "time": float(time),
            "config_ints": list(vector),
            "config_values": list(experiment.get_variable_values(vector)),
        }

    low_pairs = sorted(
        [(v, t) for v, t in valid_results.items() if t < low_threshold],
        key=lambda x: x[1],
    )
    high_pairs = sorted(
        [(v, t) for v, t in valid_results.items() if t > high_threshold],
        key=lambda x: x[1],
        reverse=True,
    )

    space_definition = experiment.get_search_space_definition()
    total_space_size = math.prod(max_int + 1 for _, max_int in space_definition)
    coverage = len(valid_results) / total_space_size if total_space_size > 0 else 0.0

    return {
        "sample_count": len(valid_results),
        "coverage": coverage,
        "min": _config_entry(vectors[min_idx], times[min_idx]),
        "max": _config_entry(vectors[max_idx], times[max_idx]),
        "mean": float(np.mean(times)),
        "median": float(median),
        "q1": float(q1),
        "q3": float(q3),
        "iqr": iqr,
        "low_outliers": {
            "count": len(low_pairs),
            "threshold": low_threshold,
            "configs": [
                _config_entry(v, t) for v, t in low_pairs[:_MAX_OUTLIER_CONFIGS]
            ],
        },
        "high_outliers": {
            "count": len(high_pairs),
            "threshold": high_threshold,
            "configs": [
                _config_entry(v, t) for v, t in high_pairs[:_MAX_OUTLIER_CONFIGS]
            ],
        },
    }
