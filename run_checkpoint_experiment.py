import argparse

from checkpoint_pipeline import (
    CHECKPOINT_GA_GENERATIONS,
    CHECKPOINT_GA_POPULATION_SIZE,
    CHECKPOINT_RANDOM_SEARCH_SAMPLES,
    CHECKPOINT_RESULTS_DIR,
    CHECKPOINT_SEEDS,
    run_checkpoint_experiment,
)


def main():
    parser = argparse.ArgumentParser(description="Run the formal checkpoint evacuation experiment.")
    parser.add_argument("--results-dir", default=str(CHECKPOINT_RESULTS_DIR), help="Output directory for checkpoint files.")
    parser.add_argument("--seeds", nargs="*", type=int, default=CHECKPOINT_SEEDS, help="Evaluation seeds.")
    parser.add_argument("--random-search-samples", type=int, default=CHECKPOINT_RANDOM_SEARCH_SAMPLES, help="Random search samples.")
    parser.add_argument("--ga-population-size", type=int, default=CHECKPOINT_GA_POPULATION_SIZE, help="GA population size.")
    parser.add_argument("--ga-generations", type=int, default=CHECKPOINT_GA_GENERATIONS, help="GA generations.")
    args = parser.parse_args()

    result = run_checkpoint_experiment(
        results_dir=args.results_dir,
        seeds=args.seeds,
        random_search_samples=args.random_search_samples,
        ga_population_size=args.ga_population_size,
        ga_generations=args.ga_generations,
    )

    print("Checkpoint experiment complete.")
    print(f"Summary CSV: {result['outputs']['summary_csv']}")
    print(f"Summary JSON: {result['outputs']['summary_json']}")
    print(f"Notes: {result['outputs']['notes_md']}")


if __name__ == "__main__":
    main()
