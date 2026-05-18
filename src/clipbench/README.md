# CLIPBench CLI application

The CLIPBench CLI module handles the execution of benchmarking experiments. It provides:

- Experiment parsing and validation
- Program execution and timing measurement
- Data collection and result aggregation
- Integration with the command-line interface

This is the engine that drives the actual benchmarking process, taking experiment definitions and producing measured results.

## Search Methods

The core supports multiple strategies for exploring the parameter space:

- **Grid Sample** - Uniform grid sampling across all parameter combinations
- **Random Sample** - Random sampling of parameter combinations
- **Trend Search** - Identifies performance trends across parameter ranges
- **Local Extrema Search** - Finds local minima and maxima in the parameter space

## Command Runners

- **C Runner** - Executes and measures batch commands using a C-based implementation for high performance and accuracy.
