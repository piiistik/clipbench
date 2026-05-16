import json
import logging
from typing import Dict, Tuple
import numpy as np

from clipbench.core.search_space import SearchSpace, VariableVector
from clipbench.experiment.experiment import Experiment

logger = logging.getLogger(__name__)


def save_analysis(
    results: SearchSpace,
    json_file: str,
    experiment: Experiment,
) -> None:
    """
    Analyze search results using permutation importance and save to JSON.

    Trains a RandomForest model on the search space and computes permutation importance
    for each variable. Results are saved to a JSON file with normalized importance scores.

    Args:
        results: Evaluated search space (Dict[VariableVector, Evaluation])
        json_file: Path to output analysis.json file
        experiment: Experiment instance for variable metadata
    """
    # Filter out None values from results
    valid_results = {
        vector: time_value
        for vector, time_value in results.items()
        if time_value is not None
    }

    if not valid_results:
        logger.warning("No valid results to analyze. Skipping analysis.")
        return

    # Convert to numpy arrays for sklearn
    vectors = list(valid_results.keys())
    X = np.array(vectors, dtype=np.float64)
    y = np.array([valid_results[v] for v in vectors], dtype=np.float64)

    # Runtime data is typically skewed and multiplicative, so log scaling makes
    # the analysis more stable and the importance scores more meaningful.
    y = np.log1p(y)

    # Check if we have enough samples and variance
    if len(X) < 2:
        logger.warning(
            "Insufficient samples for analysis (need at least 2). Skipping analysis."
        )
        return

    if np.std(y) == 0:
        logger.warning("No variance in results. Setting all importances to zero.")
        num_vars = len(vectors[0])
        analysis = _create_analysis_output(
            experiment, vectors[0], np.zeros(num_vars), np.zeros(num_vars)
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
            experiment, vectors[0], importance_mean, importance_std
        )

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
    """
    Create the analysis output dictionary with variable names and importance scores.

    Args:
        experiment: Experiment instance for variable metadata
        sample_vector: A sample variable vector to determine number of variables
        importance_mean: Array of mean importance values
        importance_std: Array of std importance values

    Returns:
        Dictionary with analysis results
    """
    num_vars = len(sample_vector)
    variable_names = [f"var_{i+1}" for i in range(num_vars)]

    # Normalize importances to sum to 1.0 (if there's any variance)
    total = np.sum(importance_mean)
    if total > 0:
        importance_mean_normalized = importance_mean / total
        importance_std_normalized = importance_std / total if total > 0 else importance_std
    else:
        importance_mean_normalized = importance_mean
        importance_std_normalized = importance_std

    return {
        "variables": variable_names,
        "importances_mean": importance_mean_normalized.tolist(),
        "importances_std": importance_std_normalized.tolist(),
    }
