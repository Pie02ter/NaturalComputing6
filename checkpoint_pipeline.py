import csv
import json
from pathlib import Path

import numpy as np

from config import (
    DEFAULT_PARAMS,
    FIXED_WALL_RADIUS,
    FIXED_WALL_REP_WEIGHT,
    GA_PARAM_BOUNDS,
    GA_PARAM_NAMES,
    DEFAULT_GA_SEED_VECTOR,
    LAYOUTS,
    PARAM_BOUNDS,
    PARAM_NAMES,
)
from ga import arithmetic_crossover, initialize_population, merge_active_to_full, mutate, tournament_select
from simulator import run_simulation


CHECKPOINT_SEEDS = [0, 1, 2]
CHECKPOINT_SETTINGS = {
    "layout": "standard",
    "num_high": 30,
    "num_low": 10,
    "max_ticks": 500,
    "dt": 0.1,
    "frame_stride": 4,
}
CHECKPOINT_RANDOM_SEARCH_SAMPLES = 50
CHECKPOINT_GA_POPULATION_SIZE = 15
CHECKPOINT_GA_GENERATIONS = 15
CHECKPOINT_RESULTS_DIR = Path("results") / "checkpoint"

CHECKPOINT_BASE_WEIGHTS = {
    "total_time": 1.0,
    "mean_congestion": 0.05,
    "near_collisions": 0.001,
    "remaining_agents": 10.0,
    "fairness_weight": 1.0,
    "missing_fairness_gap_time": 1_000_000.0,
}

SUMMARY_COLUMNS = [
    "method",
    "fitness",
    "search_fitness",
    "search_fairness_weight",
    "total_time",
    "mean_congestion",
    "peak_congestion",
    "near_collisions",
    "remaining_agents",
    "mean_high_time",
    "mean_low_time",
    "fairness_gap_time",
    "all_evacuated",
    "best_params",
]

CONVERGENCE_COLUMNS = [
    "generation",
    "best_fitness",
    "generation_best_fitness",
    "total_time",
    "fairness_gap_time",
    "remaining_agents",
    "best_params",
]


def checkpoint_fitness_weights(fairness_weight=1.0):
    weights = dict(CHECKPOINT_BASE_WEIGHTS)
    weights["fairness_weight"] = float(fairness_weight)
    return weights


def _merged_settings(settings=None):
    merged = dict(CHECKPOINT_SETTINGS)
    if settings:
        merged.update(settings)
    return merged


def _cache_key(params, seeds, layout_name, settings, weights):
    rounded_params = tuple(round(float(value), 8) for value in params)
    rounded_weights = tuple((key, round(float(value), 8)) for key, value in sorted(weights.items()))
    scenario = (
        layout_name,
        int(settings["num_high"]),
        int(settings["num_low"]),
        int(settings["max_ticks"]),
        round(float(settings["dt"]), 8),
    )
    return rounded_params, tuple(int(seed) for seed in seeds), scenario, rounded_weights


def _mean_or_none(values):
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return float(np.mean(valid_values))


def compute_checkpoint_fitness(metrics, weights):
    fairness_gap_time = metrics.get("fairness_gap_time")
    if fairness_gap_time is None:
        fairness_gap_time = weights["missing_fairness_gap_time"]

    return float(
        weights["total_time"] * metrics["total_time"]
        + weights["mean_congestion"] * metrics["mean_congestion"]
        + weights["near_collisions"] * metrics["near_collisions"]
        + weights["fairness_weight"] * fairness_gap_time
        + weights["remaining_agents"] * metrics["remaining_agents"]
    )


def _aggregate_metrics(per_seed_results):
    mean_high_time = _mean_or_none([result["mean_high_time"] for result in per_seed_results])
    mean_low_time = _mean_or_none([result["mean_low_time"] for result in per_seed_results])
    fairness_gap_time = None
    if mean_high_time is not None and mean_low_time is not None:
        fairness_gap_time = abs(mean_low_time - mean_high_time)

    return {
        "total_time": float(np.mean([result["total_time"] for result in per_seed_results])),
        "mean_congestion": float(np.mean([result["mean_congestion"] for result in per_seed_results])),
        "peak_congestion": float(np.mean([result["peak_congestion"] for result in per_seed_results])),
        "near_collisions": float(np.mean([result["near_collisions"] for result in per_seed_results])),
        "remaining_agents": float(np.mean([result["remaining_agents"] for result in per_seed_results])),
        "mean_high_time": mean_high_time,
        "mean_low_time": mean_low_time,
        "fairness_gap_time": fairness_gap_time,
        "all_evacuated": bool(all(result["all_evacuated"] for result in per_seed_results)),
    }


def evaluate_params(params, seeds, layout_name, settings, weights, cache=None):
    """Evaluate one parameter vector over fixed seeds and return fitness plus averaged metrics."""
    seeds = list(seeds)
    settings = _merged_settings(settings)
    layout_name = layout_name or settings["layout"]
    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'")

    params = [float(value) for value in params]
    weights = dict(CHECKPOINT_BASE_WEIGHTS if weights is None else weights)
    key = _cache_key(params, seeds, layout_name, settings, weights)
    if cache is not None and key in cache:
        cached = cache[key]
        return cached["fitness"], dict(cached["metrics"])

    layout = LAYOUTS[layout_name]
    per_seed_results = []
    for seed in seeds:
        per_seed_results.append(
            run_simulation(
                params=params,
                num_high=int(settings["num_high"]),
                num_low=int(settings["num_low"]),
                room_size=layout["room_size"],
                exit_pos=layout["exit_pos"],
                exit_width=layout["exit_width"],
                max_ticks=int(settings["max_ticks"]),
                dt=float(settings["dt"]),
                seed=int(seed),
                frame_stride=int(settings.get("frame_stride", CHECKPOINT_SETTINGS["frame_stride"])),
                capture_frames=False,
            )
        )

    metrics = _aggregate_metrics(per_seed_results)
    metrics["params"] = params
    metrics["seeds"] = [int(seed) for seed in seeds]
    metrics["layout"] = layout_name
    metrics["num_high"] = int(settings["num_high"])
    metrics["num_low"] = int(settings["num_low"])
    metrics["max_ticks"] = int(settings["max_ticks"])
    metrics["dt"] = float(settings["dt"])
    metrics["per_seed_results"] = per_seed_results
    fitness = compute_checkpoint_fitness(metrics, weights)

    if cache is not None:
        cache[key] = {"fitness": fitness, "metrics": dict(metrics)}
    return fitness, metrics


def run_random_search(num_samples, bounds, evaluator, rng_seed=321):
    if num_samples < 1:
        raise ValueError("num_samples must be at least 1")

    rng = np.random.default_rng(rng_seed)
    best = None
    evaluations = []
    for sample_id in range(num_samples):
        active = [float(rng.uniform(low, high)) for low, high in bounds]
        params = merge_active_to_full(np.array(active)).tolist()
        fitness, metrics = evaluator(params)
        record = {
            "sample_id": sample_id,
            "params": params,
            "fitness": fitness,
            "metrics": metrics,
        }
        evaluations.append(record)
        if best is None or fitness < best["fitness"]:
            best = record

    return {
        "method": "random_search",
        "best_params": best["params"],
        "best_fitness": best["fitness"],
        "best_metrics": best["metrics"],
        "evaluations": evaluations,
        "num_samples": int(num_samples),
        "rng_seed": int(rng_seed),
    }


def run_ga(
    fairness_weight,
    seeds=None,
    layout_name="standard",
    settings=None,
    population_size=CHECKPOINT_GA_POPULATION_SIZE,
    generations=CHECKPOINT_GA_GENERATIONS,
    elite_count=2,
    tournament_size=3,
    crossover_probability=0.9,
    mutation_probability=0.2,
    mutation_sigma_scale=0.1,
    rng_seed=123,
    bounds=None,
):
    seeds = CHECKPOINT_SEEDS if seeds is None else list(seeds)
    settings = _merged_settings(settings)
    bounds = GA_PARAM_BOUNDS if bounds is None else bounds
    weights = checkpoint_fitness_weights(fairness_weight)
    rng = np.random.default_rng(rng_seed)
    population = initialize_population(population_size, bounds, rng, seed_vector=DEFAULT_GA_SEED_VECTOR)
    cache = {}

    def evaluator(params):
        return evaluate_params(params, seeds, layout_name, settings, weights, cache=cache)

    best_so_far = None
    history = []
    tournament_size = min(int(tournament_size), int(population_size))

    for generation in range(generations):
        evaluations = []
        fitnesses = []
        for candidate in population:
            full_params = merge_active_to_full(np.array(candidate)).tolist()
            fitness, metrics = evaluator(full_params)
            evaluations.append({"params": metrics["params"], "fitness": fitness, "metrics": metrics})
            fitnesses.append(fitness)

        ranked_indices = np.argsort(fitnesses)
        ranked_population = [population[index] for index in ranked_indices]
        ranked_fitnesses = [fitnesses[index] for index in ranked_indices]
        generation_best = evaluations[int(ranked_indices[0])]

        if best_so_far is None or generation_best["fitness"] < best_so_far["fitness"]:
            best_so_far = generation_best

        history.append(
            {
                "generation": int(generation),
                "best_fitness": float(best_so_far["fitness"]),
                "generation_best_fitness": float(generation_best["fitness"]),
                "best_params": [float(value) for value in best_so_far["params"]],
                "generation_best_params": [float(value) for value in generation_best["params"]],
                "total_time": best_so_far["metrics"]["total_time"],
                "fairness_gap_time": best_so_far["metrics"]["fairness_gap_time"],
                "remaining_agents": best_so_far["metrics"]["remaining_agents"],
            }
        )

        next_population = [np.array(candidate, copy=True) for candidate in ranked_population[:elite_count]]
        while len(next_population) < population_size:
            parent_a = tournament_select(ranked_population, ranked_fitnesses, tournament_size, rng)
            parent_b = tournament_select(ranked_population, ranked_fitnesses, tournament_size, rng)
            if rng.random() < crossover_probability:
                child_a, child_b = arithmetic_crossover(parent_a, parent_b, rng)
            else:
                child_a, child_b = np.array(parent_a, copy=True), np.array(parent_b, copy=True)

            next_population.append(mutate(child_a, bounds, mutation_probability, mutation_sigma_scale, rng))
            if len(next_population) < population_size:
                next_population.append(mutate(child_b, bounds, mutation_probability, mutation_sigma_scale, rng))
        population = next_population

    return {
        "method": "ga",
        "fairness_weight": float(fairness_weight),
        "best_params": best_so_far["params"],
        "best_fitness": best_so_far["fitness"],
        "best_metrics": best_so_far["metrics"],
        "history": history,
        "settings": settings,
        "seeds": seeds,
        "ga_settings": {
            "population_size": int(population_size),
            "generations": int(generations),
            "elite_count": int(elite_count),
            "tournament_size": int(tournament_size),
            "crossover_probability": float(crossover_probability),
            "mutation_probability": float(mutation_probability),
            "mutation_sigma_scale": float(mutation_sigma_scale),
            "rng_seed": int(rng_seed),
        },
    }


def _summary_entry(method, common_fitness, common_metrics, search_fairness_weight, search_fitness=None, params=None):
    best_params = params if params is not None else common_metrics["params"]
    return {
        "method": method,
        "fitness": float(common_fitness),
        "search_fitness": None if search_fitness is None else float(search_fitness),
        "search_fairness_weight": float(search_fairness_weight),
        "total_time": common_metrics["total_time"],
        "mean_congestion": common_metrics["mean_congestion"],
        "peak_congestion": common_metrics["peak_congestion"],
        "near_collisions": common_metrics["near_collisions"],
        "remaining_agents": common_metrics["remaining_agents"],
        "mean_high_time": common_metrics["mean_high_time"],
        "mean_low_time": common_metrics["mean_low_time"],
        "fairness_gap_time": common_metrics["fairness_gap_time"],
        "all_evacuated": common_metrics["all_evacuated"],
        "best_params": [float(value) for value in best_params],
    }


def _csv_safe_row(entry):
    row = dict(entry)
    row["best_params"] = json.dumps(entry["best_params"])
    return row


def _write_summary_csv(path, entries):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(_csv_safe_row(entry))


def _write_convergence_csv(path, history):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONVERGENCE_COLUMNS)
        writer.writeheader()
        for entry in history:
            row = {column: entry.get(column) for column in CONVERGENCE_COLUMNS}
            row["best_params"] = json.dumps(entry["best_params"])
            writer.writerow(row)


def _format_markdown_value(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_checkpoint_notes(entries, settings, seeds, random_search_samples, ga_population_size, ga_generations):
    table_lines = [
        "| Method | Fitness | Total time | Fairness gap | Mean congestion | Near collisions | Remaining |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in entries:
        table_lines.append(
            "| {method} | {fitness} | {total_time} | {fairness_gap_time} | {mean_congestion} | {near_collisions} | {remaining_agents} |".format(
                method=entry["method"],
                fitness=_format_markdown_value(entry["fitness"]),
                total_time=_format_markdown_value(entry["total_time"]),
                fairness_gap_time=_format_markdown_value(entry["fairness_gap_time"]),
                mean_congestion=_format_markdown_value(entry["mean_congestion"]),
                near_collisions=_format_markdown_value(entry["near_collisions"]),
                remaining_agents=_format_markdown_value(entry["remaining_agents"]),
            )
        )

    best_fitness = min(entries, key=lambda entry: entry["fitness"])
    best_fairness = min(
        (entry for entry in entries if entry["fairness_gap_time"] is not None),
        key=lambda entry: entry["fairness_gap_time"],
        default=None,
    )
    fastest = min(entries, key=lambda entry: entry["total_time"])
    fairness_sentence = "No method produced a defined fairness gap."
    if best_fairness is not None:
        fairness_sentence = f"The smallest mean evacuation-time gap was produced by `{best_fairness['method']}` ({best_fairness['fairness_gap_time']:.3f}s)."

    return "\n".join(
        [
            "# Checkpoint Experiment Notes",
            "",
            "## Experimental Settings",
            f"- layout: `{settings['layout']}`",
            f"- exit_width: `{LAYOUTS[settings['layout']]['exit_width']}`",
            f"- num_high: `{settings['num_high']}`",
            f"- num_low: `{settings['num_low']}`",
            f"- max_ticks: `{settings['max_ticks']}`",
            f"- dt: `{settings['dt']}`",
            f"- evaluation seeds: `{seeds}`",
            f"- random_search_samples: `{random_search_samples}`",
            f"- ga_population_size: `{ga_population_size}`",
            f"- ga_generations: `{ga_generations}`",
            f"- GA search space: `accel_factor`, `agent_rep_weight`, `agent_radius`; fixed `wall_rep_weight = {FIXED_WALL_REP_WEIGHT}`, `wall_radius = {FIXED_WALL_RADIUS}`.",
            "",
            "## Fitness Function",
            "`fitness = 1.0 * total_time + 0.05 * mean_congestion + 0.001 * near_collisions + fairness_weight * fairness_gap_time + 10.0 * remaining_agents`",
            "",
            "For the common comparison summary, `fitness` is recomputed with `fairness_weight = 1.0` for every method. `GA without fairness` is optimized with `fairness_weight = 0.0`; its convergence file therefore reports the no-fairness optimization objective.",
            "",
            "## Fairness Definition",
            "`G = abs(mean_low_time - mean_high_time)`",
            "",
            "## Result Summary",
            *table_lines,
            "",
            f"Best common checkpoint fitness: `{best_fitness['method']}` ({best_fitness['fitness']:.3f}).",
            f"Fastest mean evacuation time: `{fastest['method']}` ({fastest['total_time']:.3f}s).",
            fairness_sentence,
            "",
            "## Planned Next Experiments",
            "- More evaluation seeds.",
            "- Fairness-weight sweep with `w_G in {0, 0.25, 0.5, 1.0, 2.0}`.",
            "- Generalization to corridor and asymmetric layouts.",
            "- Different high/low mobility ratios.",
            "",
        ]
    )


def run_checkpoint_experiment(
    results_dir=CHECKPOINT_RESULTS_DIR,
    seeds=None,
    settings=None,
    random_search_samples=CHECKPOINT_RANDOM_SEARCH_SAMPLES,
    ga_population_size=CHECKPOINT_GA_POPULATION_SIZE,
    ga_generations=CHECKPOINT_GA_GENERATIONS,
    random_rng_seed=321,
    ga_rng_seed=123,
):
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    seeds = CHECKPOINT_SEEDS if seeds is None else list(seeds)
    settings = _merged_settings(settings)
    layout_name = settings["layout"]
    common_weights = checkpoint_fitness_weights(1.0)
    no_fairness_weights = checkpoint_fitness_weights(0.0)
    cache = {}

    def common_evaluator(params):
        return evaluate_params(params, seeds, layout_name, settings, common_weights, cache=cache)

    default_fitness, default_metrics = common_evaluator(DEFAULT_PARAMS)
    default_entry = _summary_entry("fixed_default", default_fitness, default_metrics, 1.0, default_fitness, DEFAULT_PARAMS)

    random_result = run_random_search(random_search_samples, GA_PARAM_BOUNDS, common_evaluator, rng_seed=random_rng_seed)
    random_entry = _summary_entry(
        "random_search",
        random_result["best_fitness"],
        random_result["best_metrics"],
        1.0,
        random_result["best_fitness"],
        random_result["best_params"],
    )

    ga_no_fairness = run_ga(
        0.0,
        seeds=seeds,
        layout_name=layout_name,
        settings=settings,
        population_size=ga_population_size,
        generations=ga_generations,
        rng_seed=ga_rng_seed,
    )
    no_common_fitness, no_common_metrics = common_evaluator(ga_no_fairness["best_params"])
    ga_no_entry = _summary_entry(
        "ga_no_fairness",
        no_common_fitness,
        no_common_metrics,
        0.0,
        ga_no_fairness["best_fitness"],
        ga_no_fairness["best_params"],
    )

    ga_fairness = run_ga(
        1.0,
        seeds=seeds,
        layout_name=layout_name,
        settings=settings,
        population_size=ga_population_size,
        generations=ga_generations,
        rng_seed=ga_rng_seed,
    )
    fair_common_fitness, fair_common_metrics = common_evaluator(ga_fairness["best_params"])
    ga_fair_entry = _summary_entry(
        "ga_fairness",
        fair_common_fitness,
        fair_common_metrics,
        1.0,
        ga_fairness["best_fitness"],
        ga_fairness["best_params"],
    )

    entries = [default_entry, random_entry, ga_no_entry, ga_fair_entry]

    summary_csv = results_path / "checkpoint_summary.csv"
    summary_json = results_path / "checkpoint_summary.json"
    no_fairness_convergence = results_path / "ga_no_fairness_convergence.csv"
    fairness_convergence = results_path / "ga_fairness_convergence.csv"
    notes_path = results_path / "checkpoint_notes.md"

    _write_summary_csv(summary_csv, entries)
    _write_convergence_csv(no_fairness_convergence, ga_no_fairness["history"])
    _write_convergence_csv(fairness_convergence, ga_fairness["history"])

    notes = build_checkpoint_notes(entries, settings, seeds, random_search_samples, ga_population_size, ga_generations)
    notes_path.write_text(notes, encoding="utf-8")

    payload = {
        "settings": settings,
        "layout_definition": LAYOUTS[layout_name],
        "seeds": seeds,
        "param_names": PARAM_NAMES,
        "param_bounds": PARAM_BOUNDS,
        "ga_param_names": GA_PARAM_NAMES,
        "ga_param_bounds": GA_PARAM_BOUNDS,
        "fixed_wall_rep_weight": FIXED_WALL_REP_WEIGHT,
        "fixed_wall_radius": FIXED_WALL_RADIUS,
        "fitness_function": "fitness = 1.0 * total_time + 0.05 * mean_congestion + 0.001 * near_collisions + fairness_weight * fairness_gap_time + 10.0 * remaining_agents",
        "common_summary_fairness_weight": 1.0,
        "methods": entries,
        "random_search": {
            "num_samples": random_search_samples,
            "rng_seed": random_rng_seed,
        },
        "ga_settings": {
            "population_size": ga_population_size,
            "generations": ga_generations,
            "rng_seed": ga_rng_seed,
        },
        "convergence": {
            "ga_no_fairness": ga_no_fairness["history"],
            "ga_fairness": ga_fairness["history"],
        },
        "outputs": {
            "summary_csv": str(summary_csv),
            "summary_json": str(summary_json),
            "ga_no_fairness_convergence_csv": str(no_fairness_convergence),
            "ga_fairness_convergence_csv": str(fairness_convergence),
            "notes_md": str(notes_path),
        },
        "notes": notes,
    }
    summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
