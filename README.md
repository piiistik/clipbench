# CLIPBench (Command-Line Interface Program Benchmarking toolkit)

CLIPBench is a toolkit for benchmarking batch programs and analyzing computational experiments. It provides an integrated framework for defining, executing, and visualizing the results of program benchmarks.

> **⚠️ Disclaimer:** The current implementation is limited to **Windows** only. Cross-platform support for Linux and macOS is planned as future work.

## Core Components

CLIPBench consists of three main tools:

1. **Experiment Definition** - Define your benchmarking experiments and parameters. See [input_file_editor](src/input_file_editor) for detailed documentation.

2. **Experiment Execution** - Run your defined experiments and collect performance metrics. See [clipbench](src/clipbench) for detailed documentation.

3. **Result Visualization** - Analyze and visualize your benchmark results. See [result_viewer](src/result_viewer) for detailed documentation.

## Setup

### Prerequisites

Before installing CLIPBench, ensure you have:

- **Python 3.11 or higher**
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
- Download and install all required dependencies (matplotlib, numpy, pexpect, scikit-learn)
- Install CLIPBench as a package in your Python environment
- Creates a `build/` directory with compiled binaries for the CLI application and UI tools

#### Development Setup

For development work, install with development tools:

```bash
pip install -e .[dev]
```

This includes black (code formatter) and pytest (testing framework).

#### Full Installation

For packaging and distribution, install with all extras:

```bash
pip install -e .[dev,packaging]
```

### Using CLIPBench

After installation, CLIPBench generates these files in the `build/` directory:

- `build/input_file_editor.html`
- `build/result_viewer.html`

To use these UI tools, open the files in a web browser (recommended: Google Chrome). You can either:

- Open the files directly from your file explorer
- Drag and drop the files into a browser window

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

For complete examples documentation (including building and running examples), see [examples/README.md](examples/README.md).

If the `clipbench` command is not found on Windows, use one of these options:

1. **Add Python Scripts to PATH** (recommended):
   - Find your Python installation directory (example: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311`)
   - Add the `Scripts` subdirectory to your system PATH:
     - Open System Properties → Environment Variables
     - Edit the `PATH` variable and add: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\Scripts`
     - Restart your terminal

2. **Call CLIPBench by full path:**
   ```bash
   C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\Scripts\clipbench.exe
   ```
