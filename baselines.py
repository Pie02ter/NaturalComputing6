import numpy as np

from config import DEFAULT_EVALUATION_SEEDS, DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, GA_PARAM_BOUNDS, HEURISTIC_PARAM_SETS
from ga import evaluate_candidate, merge_active_to_full


def run_default_baseline(seeds=None, layout_name=None, sim_settings=None, log_path=None, cache=None, fitness_weights=None):
    return evaluate_candidate(
        params=DEFAULT_PARAMS,
        seeds=DEFAULT_EVALUATION_SEEDS if seeds is None else seeds,
        layout_name=layout_name or DEFAULT_SIMULATION_SETTINGS["layout"],
        sim_settings=sim_settings,
        method="default",
        generation=0,
        individual_id=0,
        log_path=log_path,
        cache=cache,
        fitness_weights=fitness_weights,
    )


def run_heuristic_baselines(seeds=None, layout_name=None, sim_settings=None, log_path=None, cache=None, fitness_weights=None, heuristic_param_sets=None):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else seeds
    layout_name = layout_name or DEFAULT_SIMULATION_SETTINGS["layout"]
    results = []
    heuristic_param_sets = HEURISTIC_PARAM_SETS if heuristic_param_sets is None else heuristic_param_sets
    for index, (name, params) in enumerate(heuristic_param_sets.items()):
        result = evaluate_candidate(
            params=params,
            seeds=seeds,
            layout_name=layout_name,
            sim_settings=sim_settings,
            method=name,
            generation=0,
            individual_id=index,
            log_path=log_path,
            cache=cache,
            fitness_weights=fitness_weights,
        )
        results.append(result)
    return results


def run_random_search(num_candidates, seeds=None, layout_name=None, sim_settings=None, rng_seed=321, log_path=None, cache=None, fitness_weights=None):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else seeds
    layout_name = layout_name or DEFAULT_SIMULATION_SETTINGS["layout"]
    rng = np.random.default_rng(rng_seed)

    best = None
    evaluations = []
    for candidate_id in range(num_candidates):
        active = [rng.uniform(low, high) for low, high in GA_PARAM_BOUNDS]
        params = merge_active_to_full(np.array(active)).tolist()
        evaluation = evaluate_candidate(
            params=params,
            seeds=seeds,
            layout_name=layout_name,
            sim_settings=sim_settings,
            method="random",
            generation=0,
            individual_id=candidate_id,
            log_path=log_path,
            cache=cache,
            fitness_weights=fitness_weights,
        )
        evaluations.append(evaluation)
        if best is None or evaluation["fitness"] < best["fitness"]:
            best = evaluation

    return {
        "method": "random",
        "best": best,
        "evaluations": evaluations,
        "num_candidates": num_candidates,
        "rng_seed": rng_seed,
        "seeds": list(seeds),
    }
