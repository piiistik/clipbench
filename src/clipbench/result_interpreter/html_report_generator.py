from scipy.interpolate import griddata

# ...existing code...
from bokeh.plotting import figure, output_file, save
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource, Select, CustomJS, LinearColorMapper, ColorBar
from bokeh.layouts import column, row
from bokeh.palettes import Viridis256

import csv

TIMEOUT_SENTINEL = -1e9
ERROR_SENTINEL = -2e9


def load_csv_to_dict(csv_path):
    """Load CSV file into a list of dictionaries."""
    data = []
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(dict(row))
    return data


def interpolate_nd_data(data, num_points=1000):
    """
    Interpolate n-dimensional data using scipy's griddata.
    Adds new points to fill the space.
    """
    import numpy as np

    if not data:
        return data
    keys = [k for k in data[0].keys() if k != "time"]
    points = np.array([[float(row[k]) for k in keys] for row in data])
    values = np.array([float(row["time"]) for row in data])
    # Create a grid covering the space
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    grid = np.random.uniform(mins, maxs, size=(num_points, len(keys)))
    interp_values = griddata(points, values, grid, method="linear")
    # Add interpolated points to data
    for i, val in enumerate(interp_values):
        if np.isnan(val):
            continue
        new_row = {k: str(grid[i, j]) for j, k in enumerate(keys)}
        new_row["time"] = str(val)
        data.append(new_row)
    return data


def create_scatter_and_heatmap_html(data, output_html):
    # Build variable schema from *_int columns when present, else fallback to legacy var_*.
    keys = list(data[0].keys())
    int_vars = [k for k in keys if k.endswith("_int")]
    if int_vars:
        all_vars = int_vars
        value_map_by_var = {}
        for var in all_vars:
            value_key = var.replace("_int", "_value")
            if value_key in keys:
                mapping = {}
                for row in data:
                    mapping[row[var]] = row[value_key]
                value_map_by_var[var] = mapping
            else:
                value_map_by_var[var] = {}
    else:
        all_vars = [k for k in keys if k != "time"]
        value_map_by_var = {var: {} for var in all_vars}

    unique_vals = {var: sorted(set(row[var] for row in data)) for var in all_vars}
    x_var = all_vars[0]
    fixed_vars = {v: unique_vals[v][0] for v in all_vars if v != x_var}

    def _axis_label(var_name: str) -> str:
        return var_name.replace("_int", "") if var_name.endswith("_int") else var_name

    def _axis_label_overrides(var_name: str) -> dict:
        mapping = value_map_by_var.get(var_name, {})
        return {float(k): str(v) for k, v in mapping.items()}

    def filter_data(x_var, fixed_vars):
        return [
            row
            for row in data
            if all(str(row.get(k)) == str(v) for k, v in fixed_vars.items())
        ]

    filtered = filter_data(x_var, fixed_vars)
    x_ok, time_ok, x_timeout, x_error = [], [], [], []
    for _row in filtered:
        _t = float(_row["time"])
        if _t == TIMEOUT_SENTINEL:
            x_timeout.append(float(_row[x_var]))
        elif _t == ERROR_SENTINEL:
            x_error.append(float(_row[x_var]))
        else:
            x_ok.append(float(_row[x_var]))
            time_ok.append(_t)

    # Scatter plot
    scatter_source = ColumnDataSource(data={"x": x_ok, "time": time_ok})
    scatter_timeout_source = ColumnDataSource(data={"x": x_timeout, "time": [0.0] * len(x_timeout)})
    scatter_error_source = ColumnDataSource(data={"x": x_error, "time": [0.0] * len(x_error)})
    scatter_p = figure(
        title=f"Scatter: {x_var} vs time",
        x_axis_label=_axis_label(x_var),
        y_axis_label="time",
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    scatter_p.xaxis.major_label_overrides = _axis_label_overrides(x_var)
    scatter_p.scatter(
        "x", "time", source=scatter_source, size=8, color="navy", alpha=0.5
    )
    scatter_p.triangle(
        "x", "time", source=scatter_timeout_source, size=10, color="orange",
        alpha=0.9, legend_label="timeout",
    )
    scatter_p.x(
        "x", "time", source=scatter_error_source, size=10, color="red",
        line_width=2, alpha=0.9, legend_label="error",
    )

    # Scatter menu
    x_select = Select(title="X Variable", value=x_var, options=all_vars)
    var_selects = [
        Select(
            title=f"Fix {v}",
            value=fixed_vars.get(v, unique_vals[v][0]),
            options=unique_vals[v],
        )
        for v in all_vars
    ]

    # Heatmap plot
    y_var = all_vars[1] if len(all_vars) > 1 else all_vars[0]
    heatmap_fixed_vars = {
        v: unique_vals[v][0] for v in all_vars if v != x_var and v != y_var
    }

    def filter_heatmap_data(x_var, y_var, fixed_vars):
        return [
            row
            for row in data
            if all(str(row.get(k)) == str(v) for k, v in fixed_vars.items())
        ]

    heatmap_filtered = filter_heatmap_data(x_var, y_var, heatmap_fixed_vars)
    x_hm_ok, y_hm_ok, time_hm_ok = [], [], []
    x_hm_timeout, y_hm_timeout = [], []
    x_hm_error, y_hm_error = [], []
    for _row in heatmap_filtered:
        _t = float(_row["time"])
        if _t == TIMEOUT_SENTINEL:
            x_hm_timeout.append(float(_row[x_var]))
            y_hm_timeout.append(float(_row[y_var]))
        elif _t == ERROR_SENTINEL:
            x_hm_error.append(float(_row[x_var]))
            y_hm_error.append(float(_row[y_var]))
        else:
            x_hm_ok.append(float(_row[x_var]))
            y_hm_ok.append(float(_row[y_var]))
            time_hm_ok.append(_t)

    heatmap_source = ColumnDataSource(
        data={"x": x_hm_ok, "y": y_hm_ok, "time": time_hm_ok}
    )
    heatmap_timeout_source = ColumnDataSource(
        data={"x": x_hm_timeout, "y": y_hm_timeout}
    )
    heatmap_error_source = ColumnDataSource(
        data={"x": x_hm_error, "y": y_hm_error}
    )
    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=min(time_hm_ok) if time_hm_ok else 0,
        high=max(time_hm_ok) if time_hm_ok else 1,
    )
    heatmap_p = figure(
        title=f"Heatmap: {x_var} vs {y_var}",
        x_axis_label=_axis_label(x_var),
        y_axis_label=_axis_label(y_var),
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    heatmap_p.xaxis.major_label_overrides = _axis_label_overrides(x_var)
    heatmap_p.yaxis.major_label_overrides = _axis_label_overrides(y_var)
    heatmap_p.rect(
        "x",
        "y",
        width=1.1,
        height=1.1,
        source=heatmap_source,
        fill_color={"field": "time", "transform": color_mapper},
        line_color=None,
    )
    heatmap_p.rect(
        "x",
        "y",
        width=1.1,
        height=1.1,
        source=heatmap_timeout_source,
        fill_color="orange",
        line_color=None,
        legend_label="timeout",
    )
    heatmap_p.rect(
        "x",
        "y",
        width=1.1,
        height=1.1,
        source=heatmap_error_source,
        fill_color="red",
        line_color=None,
        legend_label="error",
    )
    color_bar = ColorBar(
        color_mapper=color_mapper, label_standoff=12, location=(0, 0), title="time"
    )
    heatmap_p.add_layout(color_bar, "right")

    # Heatmap menu
    x_select_hm = Select(title="X Variable (heatmap)", value=x_var, options=all_vars)
    y_select_hm = Select(title="Y Variable (heatmap)", value=y_var, options=all_vars)
    heatmap_var_selects = [
        Select(
            title=f"Fix {v}",
            value=heatmap_fixed_vars.get(v, unique_vals[v][0]),
            options=unique_vals[v],
        )
        for v in all_vars
    ]

    # JS callbacks (scatter and heatmap)
    scatter_callback_code = """
	var TIMEOUT_SENTINEL = -1e9;
	var ERROR_SENTINEL = -2e9;
	var x_var = x_select.value;
    function axisLabel(var_name) {
        return var_name.endsWith('_int') ? var_name.slice(0, -4) : var_name;
    }
    function axisLabelOverrides(var_name) {
        var overrides = {};
        for (var i = 0; i < all_data.length; i++) {
            var row = all_data[i];
            var value_key = var_name.endsWith('_int') ? var_name.replace('_int', '_value') : null;
            if (value_key && row[value_key] !== undefined) {
                overrides[parseFloat(row[var_name])] = String(row[value_key]);
            }
        }
        return overrides;
    }
	for (var i = 0; i < var_selects.length; i++) {
		var_selects[i].disabled = (var_selects[i].title.replace('Fix ', '') === x_var);
	}
	var fixed = {};
	for (var i = 0; i < var_selects.length; i++) {
		var var_name = var_selects[i].title.replace('Fix ', '');
		if (var_name !== x_var) {
			fixed[var_name] = var_selects[i].value;
		}
	}
	var x_ok = [], time_ok = [], x_timeout = [], x_error = [];
	for (var i = 0; i < all_data.length; i++) {
		var row = all_data[i];
		var match = true;
		for (var k in fixed) {
			if (row[k] != fixed[k]) match = false;
		}
		if (match) {
			var t = parseFloat(row['time']);
			if (t === TIMEOUT_SENTINEL) {
				x_timeout.push(parseFloat(row[x_var]));
			} else if (t === ERROR_SENTINEL) {
				x_error.push(parseFloat(row[x_var]));
			} else {
				x_ok.push(parseFloat(row[x_var]));
				time_ok.push(t);
			}
		}
	}
	scatter_source.data = {x: x_ok, time: time_ok};
	scatter_source.change.emit();
	scatter_timeout_source.data = {x: x_timeout, time: new Array(x_timeout.length).fill(0.0)};
	scatter_timeout_source.change.emit();
	scatter_error_source.data = {x: x_error, time: new Array(x_error.length).fill(0.0)};
	scatter_error_source.change.emit();
    scatter_p.xaxis[0].axis_label = axisLabel(x_var);
    scatter_p.xaxis[0].major_label_overrides = axisLabelOverrides(x_var);
	scatter_p.title.text = "Scatter: " + x_var + " vs time";
	"""

    heatmap_callback_code = """
	var TIMEOUT_SENTINEL = -1e9;
	var ERROR_SENTINEL = -2e9;
	var x_var = x_select_hm.value;
	var y_var = y_select_hm.value;
    function axisLabel(var_name) {
        return var_name.endsWith('_int') ? var_name.slice(0, -4) : var_name;
    }
    function axisLabelOverrides(var_name) {
        var overrides = {};
        for (var i = 0; i < all_data.length; i++) {
            var row = all_data[i];
            var value_key = var_name.endsWith('_int') ? var_name.replace('_int', '_value') : null;
            if (value_key && row[value_key] !== undefined) {
                overrides[parseFloat(row[var_name])] = String(row[value_key]);
            }
        }
        return overrides;
    }
	// Disable x and y variable dropdowns for fixed values
	for (var i = 0; i < heatmap_var_selects.length; i++) {
		var vname = heatmap_var_selects[i].title.replace('Fix ', '');
		heatmap_var_selects[i].disabled = (vname === x_var || vname === y_var);
	}
	// Prevent selecting same variable for x and y
	if (x_var === y_var) {
		heatmap_source.data = {x: [], y: [], time: []};
		heatmap_source.change.emit();
		heatmap_timeout_source.data = {x: [], y: []};
		heatmap_timeout_source.change.emit();
		heatmap_error_source.data = {x: [], y: []};
		heatmap_error_source.change.emit();
        heatmap_p.xaxis[0].axis_label = axisLabel(x_var);
        heatmap_p.yaxis[0].axis_label = axisLabel(y_var);
        heatmap_p.xaxis[0].major_label_overrides = axisLabelOverrides(x_var);
        heatmap_p.yaxis[0].major_label_overrides = axisLabelOverrides(y_var);
		heatmap_p.title.text = "Heatmap: " + x_var + " vs " + y_var;
		return;
	}
	var fixed = {};
	for (var i = 0; i < heatmap_var_selects.length; i++) {
		var var_name = heatmap_var_selects[i].title.replace('Fix ', '');
		if (var_name !== x_var && var_name !== y_var) {
			fixed[var_name] = heatmap_var_selects[i].value;
		}
	}
	var x_ok = [], y_ok = [], time_ok = [];
	var x_timeout = [], y_timeout = [];
	var x_error = [], y_error = [];
	for (var i = 0; i < all_data.length; i++) {
		var row = all_data[i];
		var match = true;
		for (var k in fixed) {
			if (row[k] != fixed[k]) match = false;
		}
		if (match) {
			var t = parseFloat(row['time']);
			if (t === TIMEOUT_SENTINEL) {
				x_timeout.push(parseFloat(row[x_var]));
				y_timeout.push(parseFloat(row[y_var]));
			} else if (t === ERROR_SENTINEL) {
				x_error.push(parseFloat(row[x_var]));
				y_error.push(parseFloat(row[y_var]));
			} else {
				x_ok.push(parseFloat(row[x_var]));
				y_ok.push(parseFloat(row[y_var]));
				time_ok.push(t);
			}
		}
	}
	heatmap_source.data = {x: x_ok, y: y_ok, time: time_ok};
	heatmap_source.change.emit();
	heatmap_timeout_source.data = {x: x_timeout, y: y_timeout};
	heatmap_timeout_source.change.emit();
	heatmap_error_source.data = {x: x_error, y: y_error};
	heatmap_error_source.change.emit();
	if (time_ok.length > 0) {
		var min_t = Math.min.apply(null, time_ok);
		var max_t = Math.max.apply(null, time_ok);
		color_mapper.low = min_t;
		color_mapper.high = max_t === min_t ? min_t + 1 : max_t;
	}
    heatmap_p.xaxis[0].axis_label = axisLabel(x_var);
    heatmap_p.yaxis[0].axis_label = axisLabel(y_var);
    heatmap_p.xaxis[0].major_label_overrides = axisLabelOverrides(x_var);
    heatmap_p.yaxis[0].major_label_overrides = axisLabelOverrides(y_var);
	heatmap_p.title.text = "Heatmap: " + x_var + " vs " + y_var;
	"""

    scatter_args = {
        "all_vars": all_vars,
        "x_select": x_select,
        "var_selects": var_selects,
        "all_data": data,
        "scatter_p": scatter_p,
        "scatter_source": scatter_source,
        "scatter_timeout_source": scatter_timeout_source,
        "scatter_error_source": scatter_error_source,
    }
    x_select.js_on_change(
        "value", CustomJS(args=scatter_args, code=scatter_callback_code)
    )
    for vs in var_selects:
        vs.js_on_change(
            "value", CustomJS(args=scatter_args, code=scatter_callback_code)
        )

    heatmap_args = {
        "all_vars": all_vars,
        "x_select_hm": x_select_hm,
        "y_select_hm": y_select_hm,
        "heatmap_var_selects": heatmap_var_selects,
        "all_data": data,
        "heatmap_p": heatmap_p,
        "heatmap_source": heatmap_source,
        "heatmap_timeout_source": heatmap_timeout_source,
        "heatmap_error_source": heatmap_error_source,
        "color_mapper": color_mapper,
    }
    x_select_hm.js_on_change(
        "value", CustomJS(args=heatmap_args, code=heatmap_callback_code)
    )
    y_select_hm.js_on_change(
        "value", CustomJS(args=heatmap_args, code=heatmap_callback_code)
    )
    for vs in heatmap_var_selects:
        vs.js_on_change(
            "value", CustomJS(args=heatmap_args, code=heatmap_callback_code)
        )

    # Initially disable the dropdown for the initial x_var and y_var
    for vs in var_selects:
        if vs.title.replace("Fix ", "") == x_var:
            vs.disabled = True
    for vs in heatmap_var_selects:
        if (
            vs.title.replace("Fix ", "") == x_var
            or vs.title.replace("Fix ", "") == y_var
        ):
            vs.disabled = True

    layout = row(
        column(row(x_select, *var_selects), scatter_p),
        column(row(x_select_hm, y_select_hm, *heatmap_var_selects), heatmap_p),
    )
    output_file(output_html, title="Bokeh Interactive Scatter & Heatmap", mode="cdn")
    save(layout, resources=CDN)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python html_report_generator.py <csv_path> <output_html>")
        sys.exit(1)
    csv_path = sys.argv[1]
    output_html = sys.argv[2]
    data = load_csv_to_dict(csv_path)
    # data = interpolate_nd_data(data, num_points=1000)
    print("Loaded rows:", len(data))
    print("First row:", data[0] if data else "No data")
    create_scatter_and_heatmap_html(data, output_html)
    print(f"Interactive scatter & heatmap saved to {output_html}")
