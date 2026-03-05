# clipbench
cli program benchmarker

expressions v experiment def

## Installation Workflows

### 1. Basic Setup (End Users)
Install only the runtime dependencies needed to use clipbench:
```bash
pip install .
```
Then run:
```bash
clipbench
```

### 2. Development Setup
Install with development tools (black, pytest) for coding and testing:
```bash
pip install -e .[dev]
```
Now you can:
- Run tests: `pytest`
- Format code: `black .`
- Use clipbench: `clipbench`

### 3. Packaging Setup
Install with packaging tools to build distributable wheels:
```bash
pip install -e .[dev,packaging]
```
Build the wheel:
```bash
python -m build
```
The wheel will be created in the `dist/` directory.
