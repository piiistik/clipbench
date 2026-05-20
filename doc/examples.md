# CLIPBench Examples

The `examples/` directory contains ready-to-run benchmark scenarios that demonstrate how to use CLIPBench on different kinds of batch programs and search goals.

These examples are useful for:
- Learning expected input structure (`experiment.xml`, `configuration.json`)
- Testing your local setup
- Comparing behavior of different search methods (for example: minima, maxima, trend, optimized, broken)

## Build Example Binaries

Example C batch programs are not built by default. Build them explicitly with:

```bash
python setup.py build_examples
```

This compiles example executables into the `build/` directory.

## Run Examples

### Run One Example With CLI

Run CLIPBench on a specific example directory:

```bash
clipbench .\examples\new_gradient_descend\trend\
```

Each runnable example directory should contain:
- `experiment.xml`
- `configuration.json`

CLIPBench writes outputs into that same example directory, typically:
- `result.csv`
- `analysis.json`

The example directories also contain pregenerated results, so you can inspect the expected output without running the benchmarks yourself.

### Run Multiple Or All Examples

You can also use the helper script:

```bash
python .\examples\run_all_examples.py --all
```

Run selected examples:

```bash
python .\examples\run_all_examples.py euclids_gcd new_gradient_descend/maxima
```

## Runtime Disclaimer

These examples can take a considerable amount of time (all together - hours) to run because they evaluate with relatively high search budgets and artificial delays. If you want to run them as they are, I advise to run them using --all flag in the `run_all_examples.py` script and let them run in the background while you work on other things. 

If you need faster runs, reduce the budgets in the example configurations. This will speed up execution, but the resulting analysis will generally be less reliable and less valuable. 

You can inspect pregenerated results, which are included in the example directories, to see what kind of output to expect without running the full benchmarks yourself. Most of these results are part of Evaluation chapter of my thesis, so you can find interpretation of these results there. 

TODO: Overview of existing examples