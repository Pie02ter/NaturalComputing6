import csv
import json
from pathlib import Path

import numpy as np

from config import DEFAULT_EVALUATION_SEEDS, DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, GA_DEFAULTS, LAYOUTS, PARAM_BOUNDS
from simulator import run_simulation


RESULT_COLUMNS = [
    "method",
    "generation",
    "individual_id",
    "fitness",
    "total_time",
    "near_collisions",
    "mean_congestion",
    "peak_congestion",
    "mean_high_time",
    "mean_low_time",
    "fairness_gap_time",
    "all_evacuated",
    "remaining_agents",
    "layout",
    "num_high",
    "num_low",
    "seed_list",
    "params",
    "per_seed_fitnesses",
    "per_seed_total_times",
]


def compute_fitness(result):
    fairness_gap_time = result["fairness_gap_time"]
    if fairness_gap_time is None:
        fairness_gap_time = result["total_time"]

    fitness = (
        result["total_time"]
        + 0.05 * result["near_collisions"]
        + 1.0 * result["mean_congestion"]
        + 2.0 * fairness_gap_time
    )
    if not result["all_evacuated"]:
        fitness += 1000 + 10 * result["remaining_agents"]
    return float(fitness)


def _scenario_settings(sim_settings=None):
    settings = DEFAULT_SIMULATION_SETTINGS.copy()
    if sim_settings:
        settings.update(sim_settings)
    return settings


def _cache_key(params, seeds, layout_name, settings):
    rounded_params = tuple(round(float(value), 6) for value in params)
    relevant_settings = (
        int(settings["num_high"]),
        int(settings["num_low"]),
        int(settings["max_ticks"]),
        round(float(settings["dt"]), 6),
    )
    return (rounded_params, tuple(int(seed) for seed in seeds), layout_name, relevant_settings)


def _aggregate_results(params, seeds, layout_name, settings, per_seed_results):
    metrics = {
        "total_time": float(np.mean([item["total_time"] for item in per_seed_results])),
        "near_collisions": float(np.mean([item["near_collisions"] for item in per_seed_results])),
        "mean_congestion": float(np.mean([item["mean_congestion"] for item in per_seed_results])),
        "peak_congestion": float(np.mean([item["peak_congestion"] for item in per_seed_results])),
        "remaining_agents": float(np.mean([item["remaining_agents"] for item in per_seed_results])),
        "all_evacuated": bool(all(item["all_evacuated"] for item in per_seed_results)),
    }

    optional_fields = ["mean_high_time", "mean_low_time", "fairness_gap_time"]
    for field in optional_fields:
        values = [item[field] for item in per_seed_results if item[field] is not None]
        metrics[field] = None if not values else float(np.mean(values))

    aggregate = {
        "method": None,
        "generation": None,
        "individual_id": None,
        "params": [float(value) for value in params],
        "layout": layout_name,
        "num_high": int(settings["num_high"]),
        "num_low": int(settings["num_low"]),
        "seed_list": [int(seed) for seed in seeds],
        "per_seed_results": per_seed_results,
    }
    aggregate.update(metrics)
    aggregate["fitness"] = compute_fitness(aggregate)
    return aggregate


def append_log_row(log_path, row):
    if log_path is None:
        return

    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row_to_write = {column: row.get(column) for column in RESULT_COLUMNS}
    write_header = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row_to_write)


def evaluation_to_log_row(evaluation):
    return {
        "method": evaluation["method"],
        "generation": evaluation["generation"],
        "individual_id": evaluation["individual_id"],
        "fitness": evaluation["fitness"],
        "total_time": evaluation["total_time"],
        "near_collisions": evaluation["near_collisions"],
        "mean_congestion": evaluation["mean_congestion"],
        "peak_congestion": evaluation["peak_congestion"],
        "mean_high_time": evaluation["mean_high_time"],
        "mean_low_time": evaluation["mean_low_time"],
        "fairness_gap_time": evaluation["fairness_gap_time"],
        "all_evacuated": evaluation["all_evacuated"],
        "remaining_agents": evaluation["remaining_agents"],
        "layout": evaluation["layout"],
        "num_high": evaluation["num_high"],
        "num_low": evaluation["num_low"],
        "seed_list": json.dumps(evaluation["seed_list"]),
        "params": json.dumps(evaluation["params"]),
        "per_seed_fitnesses": json.dumps([item["fitness"] for item in evaluation["per_seed_results"]]),
        "per_seed_total_times": json.dumps([item["total_time"] for item in evaluation["per_seed_results"]]),
    }


def evaluate_candidate(
    params,
    seeds=None,
    layout_name=None,
    sim_settings=None,
    method="ga",
    generation=None,
    individual_id=None,
    log_path=None,
    cache=None,
):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else list(seeds)
    layout_name = layout_name or DEFAULT_SIMULATION_SETTINGS["layout"]
    settings = _scenario_settings(sim_settings)

    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'")

    cache_key = _cache_key(params, seeds, layout_name, settings)
    if cache is not None and cache_key in cache:
        cached = dict(cache[cache_key])
        cached["method"] = method
        cached["generation"] = generation
        cached["individual_id"] = individual_id
        append_log_row(log_path, evaluation_to_log_row(cached))
        return cached

    layout = LAYOUTS[layout_name]
    per_seed_results = []
    for seed in seeds:
        result = run_simulation(
            params=params,
            num_high=settings["num_high"],
            num_low=settings["num_low"],
            room_size=layout["room_size"],
            exit_pos=layout["exit_pos"],
            max_ticks=settings["max_ticks"],
            dt=settings["dt"],
            seed=seed,
            frame_stride=settings.get("frame_stride", DEFAULT_SIMULATION_SETTINGS["frame_stride"]),
            capture_frames=False,
        )
        result["fitness"] = compute_fitness(result)
        per_seed_results.append(result)

    aggregate = _aggregate_results(params, seeds, layout_name, settings, per_seed_results)
    aggregate["method"] = method
    aggregate["generation"] = generation
    aggregate["individual_id"] = individual_id

    if cache is not None:
        cache[cache_key] = dict(aggregate)

    append_log_row(log_path, evaluation_to_log_row(aggregate))
    return aggregate


def initialize_population(population_size, bounds, rng, seed_vector=None):
    population = []
    if seed_vector is not None:
        population.append(np.array(seed_vector, dtype=float))

    while len(population) < population_size:
        genes = [rng.uniform(low, high) for low, high in bounds]
        population.append(np.array(genes, dtype=float))
    return population


def tournament_select(population, fitnesses, tournament_size, rng):
    indices = rng.choice(len(population), size=tournament_size, replace=False)
    best_index = min(indices, key=lambda idx: fitnesses[idx])
    return np.array(population[best_index], copy=True)


def arithmetic_crossover(parent_a, parent_b, rng):
    alpha = rng.random(len(parent_a))
    child_a = alpha * parent_a + (1.0 - alpha) * parent_b
    child_b = alpha * parent_b + (1.0 - alpha) * parent_a
    return child_a, child_b


def mutate(candidate, bounds, mutation_probability, mutation_sigma_scale, rng):
    mutated = np.array(candidate, copy=True)
    for index, (low, high) in enumerate(bounds):
        if rng.random() < mutation_probability:
            sigma = mutation_sigma_scale * (high - low)
            mutated[index] += rng.normal(0.0, sigma)
            mutated[index] = np.clip(mutated[index], low, high)
    return mutated


def run_ga(
    seeds=None,
    layout_name=None,
    sim_settings=None,
    population_size=None,
    generations=None,
    elite_count=None,
    tournament_size=None,
    crossover_probability=None,
    mutation_probability=None,
    mutation_sigma_scale=None,
    rng_seed=123,
    log_path=None,
):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else list(seeds)
    layout_name = layout_name or DEFAULT_SIMULATION_SETTINGS["layout"]
    population_size = population_size or GA_DEFAULTS["population_size"]
    generations = generations or GA_DEFAULTS["generations"]
    elite_count = elite_count or GA_DEFAULTS["elite_count"]
    tournament_size = tournament_size or GA_DEFAULTS["tournament_size"]
    crossover_probability = crossover_probability or GA_DEFAULTS["crossover_probability"]
    mutation_probability = mutation_probability or GA_DEFAULTS["mutation_probability"]
    mutation_sigma_scale = mutation_sigma_scale or GA_DEFAULTS["mutation_sigma_scale"]

    rng = np.random.default_rng(rng_seed)
    cache = {}
    population = initialize_population(population_size, PARAM_BOUNDS, rng, seed_vector=DEFAULT_PARAMS)

    best_evaluation = None
    history = []

    for generation in range(generations):
        evaluations = []
        fitnesses = []
        for individual_id, candidate in enumerate(population):
            evaluation = evaluate_candidate(
                params=candidate,
                seeds=seeds,
                layout_name=layout_name,
                sim_settings=sim_settings,
                method="ga",
                generation=generation,
                individual_id=individual_id,
                log_path=log_path,
                cache=cache,
            )
            evaluations.append(evaluation)
            fitnesses.append(evaluation["fitness"])

        ranked_indices = np.argsort(fitnesses)
        ranked_population = [population[index] for index in ranked_indices]
        ranked_evaluations = [evaluations[index] for index in ranked_indices]
        generation_best = ranked_evaluations[0]
        history.append(
            {
                "generation": generation,
                "best_fitness": generation_best["fitness"],
                "best_params": generation_best["params"],
            }
        )

        if best_evaluation is None or generation_best["fitness"] < best_evaluation["fitness"]:
            best_evaluation = generation_best

        next_population = [np.array(candidate, copy=True) for candidate in ranked_population[:elite_count]]
        while len(next_population) < population_size:
            parent_a = tournament_select(ranked_population, [entry["fitness"] for entry in ranked_evaluations], tournament_size, rng)
            parent_b = tournament_select(ranked_population, [entry["fitness"] for entry in ranked_evaluations], tournament_size, rng)

            if rng.random() < crossover_probability:
                child_a, child_b = arithmetic_crossover(parent_a, parent_b, rng)
            else:
                child_a, child_b = np.array(parent_a, copy=True), np.array(parent_b, copy=True)

            next_population.append(mutate(child_a, PARAM_BOUNDS, mutation_probability, mutation_sigma_scale, rng))
            if len(next_population) < population_size:
                next_population.append(mutate(child_b, PARAM_BOUNDS, mutation_probability, mutation_sigma_scale, rng))

        population = next_population

    return {
        "method": "ga",
        "best": best_evaluation,
        "history": history,
        "seeds": seeds,
        "layout": layout_name,
        "sim_settings": _scenario_settings(sim_settings),
        "ga_settings": {
            "population_size": population_size,
            "generations": generations,
            "elite_count": elite_count,
            "tournament_size": tournament_size,
            "crossover_probability": crossover_probability,
            "mutation_probability": mutation_probability,
            "mutation_sigma_scale": mutation_sigma_scale,
            "rng_seed": rng_seed,
        },
    }
