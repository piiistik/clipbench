# CLIPBench (Command-Line Interface Program Benchmarking toolkit)

CLIPBench is a toolkit for benchmarking batch programs and analyzing computational experiments. It provides an integrated framework for defining, executing, and visualizing the results of program benchmarks.

> **⚠️ Disclaimer:** The current implementation is limited to **Windows** only. Cross-platform support for Linux and macOS is planned as future work.

## Installation

### Prerequisites

Before installing CLIPBench, ensure you have:

- **Python 3.11 or higher**
- **pip 23.0 or higher** (usually included with standard Python installations)
- **GCC (GNU Compiler Collection)**
- **Git**

If you don't yet have this repository locally on your machine, clone the CLIPBench repository:

```bash
git clone <repository-url>
cd clipbench
```

### Installation

Install CLIPBench and its dependencies:

```bash
pip install .
```

This command will:
- Download and install all required runtime dependencies
- Install CLIPBench as a package in your Python environment
- Create a `build/` directory with compiled binaries for the CLI application and UI tools

Runtime Python dependencies installed with `pip install .`:

- `bokeh>=3.0.0`
- `jinja2>=3.1.0`
- `numpy>=1.20.0`
- `scipy>=1.8.0`
- `scikit-learn>=1.0.0`

Verify the installation by running:

```bash
clipbench --help
```

If the command is recognized, you should see the help message for the CLIPBench CLI application. If you encounter a "command not found" error, see the [Windows Troubleshooting docs](doc/windows-troubleshooting.md) for solutions.

#### Development Setup

For development work, install with development tools:

```bash
pip install -e .[dev]
```

This includes black (code formatter) and pytest (testing framework).

Development extra dependencies:

- `black>=22.0.0`
- `pytest>=7.0.0`

Run tests with:

```bash
pytest
pytest tests/integration
pytest tests/unit
```

Run code formatter with:

```bash
black .
```

#### Full Installation

For packaging and distribution, install with all extras:

```bash
pip install -e .[dev,packaging]
```

Packaging extra dependencies:

- `build>=0.7.0`
- `packaging>=21.0`

Build-system dependencies used during package build:

- `setuptools>=61`
- `wheel`

## Documentation

For the complete documentation index, see [doc/documentation.md](doc/documentation.md). This includes usage instructions on how to create and run experiments and how to view results.
