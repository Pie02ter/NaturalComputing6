from flask import Flask, jsonify, request, send_from_directory

from baselines import run_default_baseline, run_heuristic_baselines, run_random_search
from checkpoint_pipeline import CHECKPOINT_GA_GENERATIONS, CHECKPOINT_GA_POPULATION_SIZE, CHECKPOINT_RANDOM_SEARCH_SAMPLES, CHECKPOINT_RESULTS_DIR, CHECKPOINT_SEEDS, run_checkpoint_experiment
from config import (
    DEFAULT_EVALUATION_SEEDS,
    DEFAULT_FITNESS_WEIGHTS,
    DEFAULT_GA_SEED_VECTOR,
    DEFAULT_PARAMS,
    DEFAULT_SIMULATION_SETTINGS,
    EXPERIMENT_PRESETS,
    FIXED_WALL_RADIUS,
    FIXED_WALL_REP_WEIGHT,
    GA_ACTIVE_INDICES,
    GA_DEFAULTS,
    GA_PARAM_BOUNDS,
    GA_PARAM_NAMES,
    LAYOUTS,
    PARAM_BOUNDS,
    PARAM_NAMES,
)
from experiments import run_generalization_suite, run_standard_comparison
from ga import run_ga
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


def _preset_payload():
    return EXPERIMENT_PRESETS


def _optional_ga_seed_vector(payload):
    raw = payload.get("ga_seed_vector")
    if raw is None:
        return None
    vec = [float(value) for value in raw]
    if len(vec) != len(GA_PARAM_BOUNDS):
        raise ValueError(f"ga_seed_vector must have length {len(GA_PARAM_BOUNDS)}.")
    return vec


def _fitness_weights_payload(payload):
    weights = dict(DEFAULT_FITNESS_WEIGHTS)
    raw_weights = payload.get("fitness_weights", {})
    for key, default_value in DEFAULT_FITNESS_WEIGHTS.items():
        if key in raw_weights:
            weights[key] = float(raw_weights[key])
        else:
            weights[key] = float(default_value)
    return weights


def _sim_settings_from_simulation(simulation):
    return {
        "layout": simulation["layout_name"],
        "num_high": simulation["num_high"],
        "num_low": simulation["num_low"],
        "max_ticks": simulation["max_ticks"],
        "dt": simulation["dt"],
        "frame_stride": simulation["frame_stride"],
        "seed": simulation["seed"],
    }


def _simulation_payload(payload):
    layout_name = payload.get("layout", DEFAULT_SIMULATION_SETTINGS["layout"])
    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'")

    params = payload.get("params", DEFAULT_PARAMS)
    if len(params) != len(DEFAULT_PARAMS):
        raise ValueError(f"Expected {len(DEFAULT_PARAMS)} movement parameters.")

    return {
        "layout_name": layout_name,
        "params": [float(value) for value in params],
        "num_high": int(payload.get("num_high", DEFAULT_SIMULATION_SETTINGS["num_high"])),
        "num_low": int(payload.get("num_low", DEFAULT_SIMULATION_SETTINGS["num_low"])),
        "max_ticks": int(payload.get("max_ticks", DEFAULT_SIMULATION_SETTINGS["max_ticks"])),
        "dt": float(payload.get("dt", DEFAULT_SIMULATION_SETTINGS["dt"])),
        "seed": int(payload.get("seed", DEFAULT_SIMULATION_SETTINGS["seed"])),
        "frame_stride": max(1, int(payload.get("frame_stride", DEFAULT_SIMULATION_SETTINGS["frame_stride"]))),
    }


def _run_simulation_for_payload(payload):
    simulation = _simulation_payload(payload)
    layout = LAYOUTS[simulation["layout_name"]]
    result = run_simulation(
        params=simulation["params"],
        num_high=simulation["num_high"],
        num_low=simulation["num_low"],
        room_size=layout["room_size"],
        exit_pos=layout["exit_pos"],
        exit_width=layout["exit_width"],
        max_ticks=simulation["max_ticks"],
        dt=simulation["dt"],
        seed=simulation["seed"],
        frame_stride=simulation["frame_stride"],
    )
    result["layout"] = simulation["layout_name"]
    result["exit_width"] = layout["exit_width"]
    return result


def _summary_payload(evaluation):
    return {
        "method": evaluation["method"],
        "fitness": evaluation["fitness"],
        "params": evaluation["params"],
        "total_time": evaluation["total_time"],
        "near_collisions": evaluation["near_collisions"],
        "mean_congestion": evaluation["mean_congestion"],
        "fairness_gap_time": evaluation["fairness_gap_time"],
        "all_evacuated": evaluation["all_evacuated"],
        "remaining_agents": evaluation["remaining_agents"],
    }


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/manual")
def manual_page():
    return send_from_directory(app.static_folder, "manual.html")


@app.get("/ga")
def ga_page():
    return send_from_directory(app.static_folder, "ga.html")


@app.get("/comparison")
def comparison_page():
    return send_from_directory(app.static_folder, "comparison.html")


@app.get("/experiments")
def experiments_page():
    return send_from_directory(app.static_folder, "experiments.html")


@app.get("/checkpoint")
def checkpoint_page():
    return send_from_directory(app.static_folder, "checkpoint.html")


@app.get("/results/<path:filename>")
def result_file(filename):
    return send_from_directory("results", filename)


@app.get("/api/config")
def get_config():
    return jsonify(
        {
            "layouts": _layout_payload(),
            "param_names": PARAM_NAMES,
            "param_bounds": PARAM_BOUNDS,
            "default_params": DEFAULT_PARAMS,
            "ga_active_indices": list(GA_ACTIVE_INDICES),
            "ga_param_names": GA_PARAM_NAMES,
            "ga_param_bounds": GA_PARAM_BOUNDS,
            "default_ga_seed_vector": DEFAULT_GA_SEED_VECTOR,
            "fixed_wall_params": {
                "wall_rep_weight": FIXED_WALL_REP_WEIGHT,
                "wall_radius": FIXED_WALL_RADIUS,
            },
            "defaults": DEFAULT_SIMULATION_SETTINGS,
            "default_evaluation_seeds": DEFAULT_EVALUATION_SEEDS,
            "default_fitness_weights": DEFAULT_FITNESS_WEIGHTS,
            "ga_defaults": GA_DEFAULTS,
            "experiment_presets": _preset_payload(),
        }
    )


@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(_run_simulation_for_payload(payload))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/optimize/ga")
def optimize_ga():
    payload = request.get_json(silent=True) or {}

    try:
        simulation = _simulation_payload(payload)
        active_seed_vector = _optional_ga_seed_vector(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    seeds = payload.get("evaluation_seeds", DEFAULT_EVALUATION_SEEDS)
    seeds = [int(seed) for seed in seeds]
    fitness_weights = _fitness_weights_payload(payload)
    ga_result = run_ga(
        seeds=seeds,
        layout_name=simulation["layout_name"],
        sim_settings=_sim_settings_from_simulation(simulation),
        population_size=int(payload.get("population_size", GA_DEFAULTS["population_size"])),
        generations=int(payload.get("generations", GA_DEFAULTS["generations"])),
        elite_count=int(payload.get("elite_count", GA_DEFAULTS["elite_count"])),
        tournament_size=int(payload.get("tournament_size", GA_DEFAULTS["tournament_size"])),
        crossover_probability=float(payload.get("crossover_probability", GA_DEFAULTS["crossover_probability"])),
        mutation_probability=float(payload.get("mutation_probability", GA_DEFAULTS["mutation_probability"])),
        mutation_sigma_scale=float(payload.get("mutation_sigma_scale", GA_DEFAULTS["mutation_sigma_scale"])),
        rng_seed=int(payload.get("rng_seed", 123)),
        fitness_weights=fitness_weights,
        active_seed_vector=active_seed_vector,
    )

    visualization_seed = int(payload.get("visualization_seed", simulation["seed"]))
    replay_payload = dict(payload)
    replay_payload["params"] = ga_result["best"]["params"]
    replay_payload["seed"] = visualization_seed
    best_simulation = _run_simulation_for_payload(replay_payload)

    return jsonify(
        {
            "history": ga_result["history"],
            "best": ga_result["best"],
            "ga_settings": ga_result["ga_settings"],
            "fitness_weights": fitness_weights,
            "evaluation_seeds": seeds,
            "visualization_seed": visualization_seed,
            "best_simulation": best_simulation,
        }
    )


@app.post("/api/compare")
def compare_methods():
    payload = request.get_json(silent=True) or {}

    try:
        simulation = _simulation_payload(payload)
        active_seed_vector = _optional_ga_seed_vector(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    seeds = [int(seed) for seed in payload.get("evaluation_seeds", DEFAULT_EVALUATION_SEEDS)]
    fitness_weights = _fitness_weights_payload(payload)
    ga_population_size = int(payload.get("population_size", GA_DEFAULTS["population_size"]))
    ga_generations = int(payload.get("generations", GA_DEFAULTS["generations"]))
    random_candidates = int(payload.get("random_candidates", ga_population_size * ga_generations))
    sim_settings = _sim_settings_from_simulation(simulation)

    cache = {}
    default_result = run_default_baseline(
        seeds=seeds,
        layout_name=simulation["layout_name"],
        sim_settings=sim_settings,
        cache=cache,
        fitness_weights=fitness_weights,
    )
    heuristic_results = run_heuristic_baselines(
        seeds=seeds,
        layout_name=simulation["layout_name"],
        sim_settings=sim_settings,
        cache=cache,
        fitness_weights=fitness_weights,
    )
    random_result = run_random_search(
        num_candidates=random_candidates,
        seeds=seeds,
        layout_name=simulation["layout_name"],
        sim_settings=sim_settings,
        rng_seed=int(payload.get("random_rng_seed", 321)),
        cache=cache,
        fitness_weights=fitness_weights,
    )
    ga_result = run_ga(
        seeds=seeds,
        layout_name=simulation["layout_name"],
        sim_settings=sim_settings,
        population_size=ga_population_size,
        generations=ga_generations,
        elite_count=int(payload.get("elite_count", GA_DEFAULTS["elite_count"])),
        tournament_size=int(payload.get("tournament_size", GA_DEFAULTS["tournament_size"])),
        crossover_probability=float(payload.get("crossover_probability", GA_DEFAULTS["crossover_probability"])),
        mutation_probability=float(payload.get("mutation_probability", GA_DEFAULTS["mutation_probability"])),
        mutation_sigma_scale=float(payload.get("mutation_sigma_scale", GA_DEFAULTS["mutation_sigma_scale"])),
        rng_seed=int(payload.get("rng_seed", 123)),
        fitness_weights=fitness_weights,
        active_seed_vector=active_seed_vector,
    )

    visualization_seed = int(payload.get("visualization_seed", simulation["seed"]))
    default_replay_payload = dict(payload)
    default_replay_payload["params"] = default_result["params"]
    default_replay_payload["seed"] = visualization_seed
    default_simulation = _run_simulation_for_payload(default_replay_payload)

    ga_replay_payload = dict(payload)
    ga_replay_payload["params"] = ga_result["best"]["params"]
    ga_replay_payload["seed"] = visualization_seed
    ga_best_simulation = _run_simulation_for_payload(ga_replay_payload)

    chart_methods = [_summary_payload(default_result)]
    chart_methods.extend(_summary_payload(result) for result in heuristic_results)
    chart_methods.append(_summary_payload(random_result["best"]))
    chart_methods.append(_summary_payload(ga_result["best"]))

    return jsonify(
        {
            "methods": chart_methods,
            "default_simulation": default_simulation,
            "ga_best_simulation": ga_best_simulation,
            "ga_history": ga_result["history"],
            "fitness_weights": fitness_weights,
            "evaluation_seeds": seeds,
            "visualization_seed": visualization_seed,
        }
    )


@app.post("/api/experiments/run")
def run_experiment_api():
    payload = request.get_json(silent=True) or {}
    preset_name = payload.get("preset")
    suite = payload.get("suite", "standard")

    if preset_name:
        if preset_name not in EXPERIMENT_PRESETS:
            return jsonify({"error": f"Unknown experiment preset '{preset_name}'"}), 400
        preset = EXPERIMENT_PRESETS[preset_name]
        suite = payload.get("suite", preset["suite"])
        settings = dict(preset["settings"])
        settings.update(payload.get("settings", {}))
        seeds = [int(seed) for seed in payload.get("evaluation_seeds", preset["evaluation_seeds"])]
        fitness_weights = _fitness_weights_payload({"fitness_weights": payload.get("fitness_weights", preset["fitness_weights"])})
        ga_settings = dict(preset["ga_settings"])
        ga_settings.update(payload.get("ga_settings", {}))
        random_candidates = int(payload.get("random_candidates", preset["random_candidates"]))
    else:
        settings = DEFAULT_SIMULATION_SETTINGS.copy()
        settings.update(payload.get("settings", {}))
        seeds = [int(seed) for seed in payload.get("evaluation_seeds", DEFAULT_EVALUATION_SEEDS)]
        fitness_weights = _fitness_weights_payload(payload)
        ga_settings = dict(GA_DEFAULTS)
        ga_settings.update(payload.get("ga_settings", {}))
        random_candidates = int(payload.get("random_candidates", ga_settings["population_size"] * ga_settings["generations"]))

    standard_results = run_standard_comparison(
        seeds=seeds,
        sim_settings=settings,
        random_search_candidates=random_candidates,
        ga_generations=int(ga_settings["generations"]),
        ga_population_size=int(ga_settings["population_size"]),
        fitness_weights=fitness_weights,
        write_outputs=False,
        ga_settings=ga_settings,
    )

    response = {
        "suite": suite,
        "preset": preset_name,
        "settings": settings,
        "evaluation_seeds": seeds,
        "fitness_weights": fitness_weights,
        "standard": {
            "default": _summary_payload(standard_results["default"]),
            "heuristics": [_summary_payload(result) for result in standard_results["heuristics"]],
            "random": _summary_payload(standard_results["random"]["best"]),
            "ga": _summary_payload(standard_results["ga"]["best"]),
            "ga_history": standard_results["ga"]["history"],
        },
    }

    if suite == "generalization":
        generalization = run_generalization_suite(
            standard_results,
            seeds=seeds,
            fitness_weights=fitness_weights,
            write_outputs=False,
        )
        response["generalization"] = generalization["generalization"]

    return jsonify(response)


@app.post("/api/checkpoint/run")
def run_checkpoint_api():
    payload = request.get_json(silent=True) or {}
    results_dir = payload.get("results_dir", str(CHECKPOINT_RESULTS_DIR))
    seeds = [int(seed) for seed in payload.get("seeds", CHECKPOINT_SEEDS)]
    random_search_samples = int(payload.get("random_search_samples", CHECKPOINT_RANDOM_SEARCH_SAMPLES))
    ga_population_size = int(payload.get("ga_population_size", CHECKPOINT_GA_POPULATION_SIZE))
    ga_generations = int(payload.get("ga_generations", CHECKPOINT_GA_GENERATIONS))

    result = run_checkpoint_experiment(
        results_dir=results_dir,
        seeds=seeds,
        random_search_samples=random_search_samples,
        ga_population_size=ga_population_size,
        ga_generations=ga_generations,
    )

    from plot_checkpoint_results import plot_checkpoint_results

    plot_outputs = plot_checkpoint_results(results_dir)
    result["outputs"].update(plot_outputs)
    result["plot_urls"] = {
        name: "/" + path.replace("\\", "/")
        for name, path in plot_outputs.items()
    }
    return jsonify(result)


@app.post("/api/checkpoint/animate")
def animate_checkpoint_api():
    payload = request.get_json(silent=True) or {}
    results_dir = payload.get("results_dir", str(CHECKPOINT_RESULTS_DIR))
    seed = int(payload.get("seed", 0))
    fps = int(payload.get("fps", 12))
    output_format = payload.get("format", "gif")

    from animate_checkpoint_runs import generate_checkpoint_animations

    outputs = generate_checkpoint_animations(
        results_dir=results_dir,
        seed=seed,
        output_format=output_format,
        fps=fps,
    )
    outputs["animation_urls"] = {
        "individual": {
            method: "/" + path.replace("\\", "/")
            for method, path in outputs["individual"].items()
        },
        "side_by_side": None if outputs["side_by_side"] is None else "/" + outputs["side_by_side"].replace("\\", "/"),
    }
    return jsonify(outputs)


if __name__ == "__main__":
    app.run(debug=True)
