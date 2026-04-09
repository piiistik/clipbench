from clipbench.core.registry import (
    get_command_runner_configurations,
    get_search_method_configurations,
)
from clipbench.core import search_method
from clipbench.core import command_runner
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Get configurations from registry (no transformation needed)
runner_configs = get_command_runner_configurations()
method_configs = get_search_method_configurations()

# Prepare template variables
first_runner = next(iter(runner_configs.keys())) if runner_configs else "c_runner"
first_method = next(iter(method_configs.keys())) if method_configs else "grid_sample"

# Generate default runner fields for config
default_runner_config = runner_configs.get(first_runner, {})
default_runner_fields = ", ".join(
    f"{field_name}: {json.dumps(field_spec['default'])}"
    for field_name, field_spec in default_runner_config.items()
)

# Setup Jinja2
template_dir = Path(__file__).parent
env = Environment(loader=FileSystemLoader(str(template_dir)))
template = env.get_template("input_file_editor.html.j2")

# Render template
html_output = template.render(
    runner_schemas_json=json.dumps(runner_configs, indent=6),
    method_schemas_json=json.dumps(method_configs, indent=6),
    default_runner_name=first_runner,
    default_method_name=first_method,
    default_runner_fields=default_runner_fields,
)

# Write output
output_path = template_dir / ".." / ".." / "bin" / "input_file_editor.html"
output_path.write_text(html_output, encoding="utf-8")

print(f"Generated {output_path}")
print(f"Runner schemas: {list(runner_configs.keys())}")
print(f"Method schemas: {list(method_configs.keys())}")
