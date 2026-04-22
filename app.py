from flask import Flask, jsonify, request, send_from_directory

from config import DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, LAYOUTS, PARAM_BOUNDS, PARAM_NAMES
from simulator import run_simulation


app = Flask(__name__, static_folder="static", static_url_path="/static")


def _layout_payload():
    return {
        name: {
            "room_size": list(layout["room_size"]),
            "exit_pos": list(layout["exit_pos"]),
            "exit_width": layout["exit_width"],
        }
        for name, layout in LAYOUTS.items()
    }


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/config")
def get_config():
    return jsonify(
        {
            "layouts": _layout_payload(),
            "param_names": PARAM_NAMES,
            "param_bounds": PARAM_BOUNDS,
            "default_params": DEFAULT_PARAMS,
            "defaults": DEFAULT_SIMULATION_SETTINGS,
        }
    )


@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}

    layout_name = payload.get("layout", DEFAULT_SIMULATION_SETTINGS["layout"])
    if layout_name not in LAYOUTS:
        return jsonify({"error": f"Unknown layout '{layout_name}'"}), 400

    params = payload.get("params", DEFAULT_PARAMS)
    if len(params) != len(DEFAULT_PARAMS):
        return jsonify({"error": "Expected 6 movement parameters."}), 400

    layout = LAYOUTS[layout_name]
    result = run_simulation(
        params=[float(value) for value in params],
        num_high=int(payload.get("num_high", DEFAULT_SIMULATION_SETTINGS["num_high"])),
        num_low=int(payload.get("num_low", DEFAULT_SIMULATION_SETTINGS["num_low"])),
        room_size=layout["room_size"],
        exit_pos=layout["exit_pos"],
        max_ticks=int(payload.get("max_ticks", DEFAULT_SIMULATION_SETTINGS["max_ticks"])),
        dt=float(payload.get("dt", DEFAULT_SIMULATION_SETTINGS["dt"])),
        seed=int(payload.get("seed", DEFAULT_SIMULATION_SETTINGS["seed"])),
        frame_stride=max(1, int(payload.get("frame_stride", DEFAULT_SIMULATION_SETTINGS["frame_stride"]))),
    )
    result["layout"] = layout_name
    result["exit_width"] = layout["exit_width"]
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
