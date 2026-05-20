# Input File Editor

The Input File Editor is a HTML-based tool for defining benchmarking experiments.

The editor generates input experiment configuration files that are used by the CLIPBench CLI application.

You can find the Input File Editor in the `build/` directory after building the project.

The tool is designed to simplify the process of creating experiment definitions, allowing you to quickly set up benchmarks without manually writing XML and JSON files. It has two parts:
- **Experiment Editor**: For defining the batch program commands and their parameters.
- **Configuration Editor**: For setting up the experiment configuration, including search method and execution settings.

The HTML is injected with setup information for each search method and command runner from main CLIPBench CLI application. Each parameter has its own description and reasonable default value. 

You can import existing input files into the editor or create new ones from scratch. Then you can copy the generated files from the editor or export them. The set-up for CLI application should be two files in the target experiment directory:
- `experiment.xml`
- `configuration.json`