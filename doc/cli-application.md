# CLIPBench CLI Application

The CLIPBench CLI module handles the execution of benchmarking experiments. It provides:

- Experiment parsing and validation
- Program execution and timing measurement
- Data collection and result aggregation
- Integration with the command-line interface

This is the engine that drives the actual benchmarking process, taking experiment definitions and producing measured results. 

---

## Usage

The main CLIPBench application runs in a terminal and expects a path to an experiment directory:

```bash
clipbench <path>
```

Example:

```bash
clipbench .\examples\new_gradient_descend\trend\
```

The target directory should contain at least:

- `experiment.xml`
- `configuration.json`

These files define the benchmark experiment and its configuration. Use Input File Editor to quickly produce them. See [Input File Editor docs](input-file-editor.md) for details on how to create these files.

CLIPBench CLI app will execute the benchmark and write results back to that directory as:

- `result.csv`
- `analysis.json`

You can use the Result Viewer to analyze these results in an interactive, visual format. See [Result Viewer docs](result-viewer.md) for details on how to use the viewer.

For examples documentation (including building and running examples), see [examples.md](examples.md). Here you can find ready-to-run benchmark scenarios that demonstrate how to use CLIPBench on different kinds of batch programs and search goals.

---

## Search Methods

The core supports multiple strategies for exploring the parameter space:

- **Grid Sample**

  A deterministic baseline sampler that distributes evaluations across the search space on a coarse Cartesian grid.
  Prefer this method when you need broad, even coverage of the domain and a reproducible baseline for comparison. `budget` determines approximate grid resolution and number of evaluated points.

- **Random Sample**

  A uniform stochastic sampler that draws integer-valued parameter vectors independently from the search space.
  Prefer this method when you want unbiased exploratory coverage without structural assumptions about the objective.
  Inputs:
  - `budget`: Runtime evaluation budget; upper bound on the number of sampled vectors.
  - `random_seed`: Seed for pseudorandom sampling; controls reproducibility.

- **Trend Search**

  An adaptive refinement method that detects steep local transitions by comparing nearby evaluated points, scoring pairs by value difference relative to distance, and sampling between or around the steepest pairs.
  Prefer this method when the primary goal is to locate boundaries, ridges, or rapid response changes rather than directly optimize extrema.
  Inputs:
  - `budget`: Runtime evaluation budget; total number of points to evaluate.
  - `random_seed`: Seed for randomized components and deterministic replay.
  - `number_of_iterations`: Number of adaptive refinement rounds after initialization.
  - `budget_fraction_initial`: Fraction of budget spent on the initial broad sample.
  - `k_neighbors`: Number of strong neighbor relationships retained per evaluated point.
  - `max_neighbor_distance`: Maximum normalized distance for considering two points as candidate neighbors.
  - `max_pairs_per_iteration`: Maximum number of steep pairs used for refinement each iteration.
  - `steepness_percentile_threshold`: Percentile gate that keeps only sufficiently steep pairs.
  - `min_effective_distance`: Lower bound on distance in steepness scoring to avoid unstable ratios.
  - `fallback_strategy`: Strategy when bisection yields too few new points (`refine` or `random`).
  - `refine_zone_radius`: Relative radius of local zones sampled in guided fallback refinement.
  - `refine_zone_sample_count`: Number of guided samples generated per selected steep zone.
  - `sampler_type`: Initial spread sampler (`random_sample` or `grid_sample`).
  - `sampler_config`: Configuration dictionary passed to the initial sampler.

- **Local Extrema Search**

  An iterative local optimization heuristic that starts with an initial sample, ranks evaluated points by objective value, and concentrates subsequent evaluations around the most promising candidates.
  Prefer this method when the objective is to approximate local minima or maxima efficiently under a fixed evaluation budget.
  Inputs:
  - `budget`: Runtime evaluation budget; total number of points to evaluate.
  - `random_seed`: Seed for stochastic sampling and reproducibility.
  - `search_target`: Optimization direction (`min` for minima, `max` for maxima).
  - `number_of_iterations`: Number of local refinement rounds.
  - `budget_fraction_per_iteration`: Fraction of budget used in the initial sampling stage.
  - `spread_of_search`: Relative amount of additional exploratory candidate generation per iteration.
  - `localization_radius`: Relative per-dimension neighborhood radius used for local sampling.
  - `candidate_pool_ratio`: Fraction of per-iteration budget used to size the elite candidate pool.
  - `sampler_type`: Initial sampler (`random_sample` or `grid_sample`).
  - `sampler_config`: Configuration dictionary passed to the initial sampler.

---

## Command Runners

- **C Runner** - Executes and measures batch commands using a C-based implementation for high performance and accuracy.
