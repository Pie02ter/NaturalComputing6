import argparse
import json
from pathlib import Path

from .baselines import run_default_baseline, run_heuristic_baselines, run_random_search
from .config import DEFAULT_EVALUATION_SEEDS, DEFAULT_FITNESS_WEIGHTS, DEFAULT_SIMULATION_SETTINGS, EXPERIMENT_PRESETS, GA_DEFAULTS
from .ga import run_ga


def _results_dir(results_dir=None):
    path = Path("results" if results_dir is None else results_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _best_summary(evaluation):
    return {
        "fitness": evaluation["fitness"],
        "params": evaluation["params"],
        "total_time": evaluation["total_time"],
        "near_collisions": evaluation["near_collisions"],
        "mean_congestion": evaluation["mean_congestion"],
        "fairness_gap_time": evaluation["fairness_gap_time"],
        "all_evacuated": evaluation["all_evacuated"],
        "remaining_agents": evaluation["remaining_agents"],
    }


def run_standard_comparison(
    seeds=None,
    sim_settings=None,
    results_dir=None,
    random_search_candidates=None,
    ga_generations=None,
    ga_population_size=None,
    fitness_weights=None,
    write_outputs=True,
    ga_settings=None,
):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else list(seeds)
    settings = DEFAULT_SIMULATION_SETTINGS.copy()
    if sim_settings:
        settings.update(sim_settings)

    results_path = _results_dir(results_dir)
    log_path = results_path / "evaluations.csv"

    merged_ga_settings = dict(GA_DEFAULTS)
    if ga_settings:
        merged_ga_settings.update(ga_settings)
    ga_population_size = ga_population_size or merged_ga_settings["population_size"]
    ga_generations = ga_generations or merged_ga_settings["generations"]
    merged_ga_settings["population_size"] = ga_population_size
    merged_ga_settings["generations"] = ga_generations
    random_search_candidates = random_search_candidates or ga_population_size * ga_generations
    fitness_weights = DEFAULT_FITNESS_WEIGHTS if fitness_weights is None else fitness_weights

    cache = {}
    default_result = run_default_baseline(seeds=seeds, layout_name=settings["layout"], sim_settings=settings, log_path=log_path if write_outputs else None, cache=cache, fitness_weights=fitness_weights)
    heuristic_results = run_heuristic_baselines(seeds=seeds, layout_name=settings["layout"], sim_settings=settings, log_path=log_path if write_outputs else None, cache=cache, fitness_weights=fitness_weights)
    random_result = run_random_search(
        num_candidates=random_search_candidates,
        seeds=seeds,
        layout_name=settings["layout"],
        sim_settings=settings,
        log_path=log_path if write_outputs else None,
        cache=cache,
        fitness_weights=fitness_weights,
    )
    ga_result = run_ga(
        seeds=seeds,
        layout_name=settings["layout"],
        sim_settings=settings,
        population_size=merged_ga_settings["population_size"],
        generations=merged_ga_settings["generations"],
        elite_count=merged_ga_settings["elite_count"],
        tournament_size=merged_ga_settings["tournament_size"],
        crossover_probability=merged_ga_settings["crossover_probability"],
        mutation_probability=merged_ga_settings["mutation_probability"],
        mutation_sigma_scale=merged_ga_settings["mutation_sigma_scale"],
        rng_seed=merged_ga_settings.get("rng_seed", 123),
        log_path=log_path if write_outputs else None,
        fitness_weights=fitness_weights,
    )

    summary = {
        "standard": {
            "seeds": seeds,
            "settings": settings,
            "default": _best_summary(default_result),
            "heuristics": {result["method"]: _best_summary(result) for result in heuristic_results},
            "random": _best_summary(random_result["best"]),
            "ga": _best_summary(ga_result["best"]),
            "ga_history": ga_result["history"],
            "fitness_weights": fitness_weights,
            "ga_settings": merged_ga_settings,
        }
    }

    if write_outputs:
        (results_path / "best_runs.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "default": default_result,
        "heuristics": heuristic_results,
        "random": random_result,
        "ga": ga_result,
        "log_path": None if not write_outputs else str(log_path),
        "summary_path": None if not write_outputs else str(results_path / "best_runs.json"),
    }


def run_generalization_suite(standard_results, seeds=None, results_dir=None, fitness_weights=None, write_outputs=True):
    seeds = DEFAULT_EVALUATION_SEEDS if seeds is None else list(seeds)
    results_path = _results_dir(results_dir)
    log_path = results_path / "generalization_evaluations.csv"
    fitness_weights = DEFAULT_FITNESS_WEIGHTS if fitness_weights is None else fitness_weights

    candidate_map = {
        "default": standard_results["default"]["params"],
        "heuristic_1": next(result for result in standard_results["heuristics"] if result["method"] == "heuristic_1")["params"],
        "heuristic_2": next(result for result in standard_results["heuristics"] if result["method"] == "heuristic_2")["params"],
        "random_best": standard_results["random"]["best"]["params"],
        "ga_best": standard_results["ga"]["best"]["params"],
    }

    scenarios = [
        {"name": "corridor_balanced", "layout": "corridor", "num_high": 30, "num_low": 10},
        {"name": "asymmetric_balanced", "layout": "asymmetric", "num_high": 30, "num_low": 10},
        {"name": "hospital_corridor_balanced", "layout": "hospital_corridor", "num_high": 28, "num_low": 12, "max_ticks": 1000},
        {"name": "standard_lowmobility_heavy", "layout": "standard", "num_high": 20, "num_low": 20},
        {"name": "standard_high_density", "layout": "standard", "num_high": 40, "num_low": 20},
    ]

    from .ga import evaluate_candidate

    cache = {}
    suite = {}
    for scenario in scenarios:
        scenario_settings = DEFAULT_SIMULATION_SETTINGS.copy()
        scenario_settings.update(
            {
                "layout": scenario["layout"],
                "num_high": scenario["num_high"],
                "num_low": scenario["num_low"],
            }
        )
        scenario_results = {}
        for method_name, params in candidate_map.items():
            evaluation = evaluate_candidate(
                params=params,
                seeds=seeds,
                layout_name=scenario["layout"],
                sim_settings=scenario_settings,
                method=method_name,
                generation=0,
                individual_id=0,
                log_path=log_path if write_outputs else None,
                cache=cache,
                fitness_weights=fitness_weights,
            )
            scenario_results[method_name] = _best_summary(evaluation)
        suite[scenario["name"]] = scenario_results

    output = {"generalization": suite}
    if write_outputs:
        (results_path / "generalization_summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def build_preset_run(preset_name):
    if preset_name not in EXPERIMENT_PRESETS:
        raise ValueError(f"Unknown experiment preset '{preset_name}'")

    preset = EXPERIMENT_PRESETS[preset_name]
    standard_results = run_standard_comparison(
        seeds=preset["evaluation_seeds"],
        sim_settings=preset["settings"],
        random_search_candidates=preset["random_candidates"],
        ga_generations=preset["ga_settings"]["generations"],
        ga_population_size=preset["ga_settings"]["population_size"],
        fitness_weights=preset["fitness_weights"],
        write_outputs=False,
        ga_settings=preset["ga_settings"],
    )

    if preset["suite"] == "standard":
        return {"suite": "standard", "standard": standard_results}

    generalization = run_generalization_suite(
        standard_results,
        seeds=preset["evaluation_seeds"],
        fitness_weights=preset["fitness_weights"],
        write_outputs=False,
    )
    return {"suite": "generalization", "standard": standard_results, "generalization": generalization}


def main():
    parser = argparse.ArgumentParser(description="Run evacuation optimization experiments.")
    parser.add_argument("command", choices=["standard", "generalization"], help="Experiment suite to run")
    parser.add_argument("--results-dir", default="results", help="Output directory for CSV and JSON results")
    parser.add_argument("--seeds", nargs="*", type=int, default=None, help="Evaluation seeds to use")
    parser.add_argument("--population-size", type=int, default=None, help="GA population size override")
    parser.add_argument("--generations", type=int, default=None, help="GA generation count override")
    parser.add_argument("--random-candidates", type=int, default=None, help="Random search candidate count override")
    parser.add_argument("--preset", default=None, help="Experiment preset to run")
    args = parser.parse_args()

    if args.preset is not None:
        result = build_preset_run(args.preset)
        print(f"Ran preset {args.preset} with suite {result['suite']}")
        return

    if args.command == "standard":
        results = run_standard_comparison(
            seeds=args.seeds,
            results_dir=args.results_dir,
            random_search_candidates=args.random_candidates,
            ga_generations=args.generations,
            ga_population_size=args.population_size,
        )
        print(f"Wrote evaluation log to {results['log_path']}")
        print(f"Wrote summary to {results['summary_path']}")
        return

    standard_results = run_standard_comparison(
        seeds=args.seeds,
        results_dir=args.results_dir,
        random_search_candidates=args.random_candidates,
        ga_generations=args.generations,
        ga_population_size=args.population_size,
    )
    output = run_generalization_suite(standard_results, seeds=args.seeds, results_dir=args.results_dir)
    print(f"Wrote generalization summary for {len(output['generalization'])} scenarios to {Path(args.results_dir) / 'generalization_summary.json'}")


if __name__ == "__main__":
    main()
