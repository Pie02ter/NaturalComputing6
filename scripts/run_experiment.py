import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.config import DEFAULT_EVALUATION_SEEDS, DEFAULT_FITNESS_WEIGHTS, DEFAULT_SIMULATION_SETTINGS, EXPERIMENT_PRESETS, GA_DEFAULTS
from crowd_evac.experiments import run_generalization_suite, run_standard_comparison
from crowd_evac.io import best_summary_to_entries, load_best_runs, write_standard_summary
from crowd_evac.visualization.animations import make_standard_animations
from crowd_evac.visualization.plots import make_standard_plots


def _load_config(path=None, preset=None):
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    if preset:
        preset_payload = EXPERIMENT_PRESETS[preset]
        return {
            "suite": preset_payload["suite"],
            "settings": preset_payload["settings"],
            "evaluation_seeds": preset_payload["evaluation_seeds"],
            "fitness_weights": preset_payload["fitness_weights"],
            "ga_settings": preset_payload["ga_settings"],
            "random_candidates": preset_payload["random_candidates"],
        }
    return {
        "suite": "standard",
        "settings": DEFAULT_SIMULATION_SETTINGS,
        "evaluation_seeds": DEFAULT_EVALUATION_SEEDS,
        "fitness_weights": DEFAULT_FITNESS_WEIGHTS,
        "ga_settings": GA_DEFAULTS,
        "random_candidates": GA_DEFAULTS["population_size"] * GA_DEFAULTS["generations"],
    }


def _apply_quick(config):
    config = dict(config)
    config["evaluation_seeds"] = config.get("evaluation_seeds", DEFAULT_EVALUATION_SEEDS)[:1]
    ga_settings = dict(config.get("ga_settings", GA_DEFAULTS))
    ga_settings.update({"population_size": 6, "generations": 3})
    config["ga_settings"] = ga_settings
    config["random_candidates"] = 12
    return config


def run_from_config(config, results_dir, make_plots=False, make_animations=False, animation_seed=11):
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    settings = dict(DEFAULT_SIMULATION_SETTINGS)
    settings.update(config.get("settings", {}))
    seeds = [int(seed) for seed in config.get("evaluation_seeds", DEFAULT_EVALUATION_SEEDS)]
    fitness_weights = dict(DEFAULT_FITNESS_WEIGHTS)
    fitness_weights.update(config.get("fitness_weights", {}))
    ga_settings = dict(GA_DEFAULTS)
    ga_settings.update(config.get("ga_settings", {}))
    random_candidates = int(config.get("random_candidates", ga_settings["population_size"] * ga_settings["generations"]))

    standard_results = run_standard_comparison(
        seeds=seeds,
        sim_settings=settings,
        results_dir=results_dir,
        random_search_candidates=random_candidates,
        ga_generations=int(ga_settings["generations"]),
        ga_population_size=int(ga_settings["population_size"]),
        fitness_weights=fitness_weights,
        write_outputs=True,
        ga_settings=ga_settings,
    )

    if config.get("suite") == "generalization":
        run_generalization_suite(standard_results, seeds=seeds, results_dir=results_dir, fitness_weights=fitness_weights)

    _, standard = load_best_runs(results_dir)
    entries = best_summary_to_entries(standard)
    outputs = write_standard_summary(results_dir, standard, entries)
    if make_plots:
        outputs["plots"] = make_standard_plots(entries, standard.get("ga_history", []), results_dir)
    if make_animations:
        outputs["animations"] = make_standard_animations(entries, standard["settings"], results_dir, seed=animation_seed)
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Run standardized crowd evacuation experiments.")
    parser.add_argument("--config", help="Path to JSON experiment config.")
    parser.add_argument("--preset", choices=sorted(EXPERIMENT_PRESETS), help="Built-in preset from crowd_evac.config.")
    parser.add_argument("--out", default="results/standard_baseline", help="Output directory.")
    parser.add_argument("--quick", action="store_true", help="Use a tiny debug budget regardless of config.")
    parser.add_argument("--make-plots", action="store_true", help="Generate standardized plots after the run.")
    parser.add_argument("--make-animations", action="store_true", help="Generate standardized GIFs after the run.")
    parser.add_argument("--animation-seed", type=int, default=11, help="Replay seed for animations.")
    args = parser.parse_args()

    config = _load_config(args.config, args.preset)
    if args.quick:
        config = _apply_quick(config)
    outputs = run_from_config(config, args.out, args.make_plots, args.make_animations, args.animation_seed)
    print("Experiment complete.")
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
