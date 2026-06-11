#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.config import DEFAULT_FITNESS_WEIGHTS, GA_DEFAULTS
from crowd_evac.ga import evaluate_candidate, run_ga


WEIGHT_PAIRS = [
    (1.0, 0.0),
    (1.0, 0.5),
    (1.0, 1.0),
    (1.0, 2.0),
    (0.0, 1.0),
]

DEFAULT_GA_SEEDS = [101, 202, 303, 404, 505]

HOSPITAL_SIM_SETTINGS = {
    "layout": "hospital_corridor",
    "num_high": 28,
    "num_low": 12,
    "max_ticks": 1000,
    "dt": 0.1,
    "frame_stride": 4,
    "seed": 42,
}


def build_fitness_weights(w_time, w_fair):
    return {
        "time": float(w_time),
        "collisions": DEFAULT_FITNESS_WEIGHTS["collisions"],
        "congestion": DEFAULT_FITNESS_WEIGHTS["congestion"],
        "fairness": float(w_fair),
        "incomplete_base": DEFAULT_FITNESS_WEIGHTS["incomplete_base"],
        "incomplete_agent": DEFAULT_FITNESS_WEIGHTS["incomplete_agent"],
    }


def weight_dir_name(w_time, w_fair):
    def fmt(x):
        return str(int(x)) if float(x).is_integer() else str(x).replace(".", "p")

    return f"weights_wT{fmt(w_time)}_wF{fmt(w_fair)}"


def run_ga_for_seed(pair_dir, ga_seed, weights, evaluation_seeds):
    seed_dir = pair_dir / f"seed_{ga_seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    result = run_ga(
        seeds=evaluation_seeds,
        layout_name=HOSPITAL_SIM_SETTINGS["layout"],
        sim_settings=HOSPITAL_SIM_SETTINGS,
        population_size=GA_DEFAULTS["population_size"],
        generations=GA_DEFAULTS["generations"],
        elite_count=GA_DEFAULTS["elite_count"],
        tournament_size=GA_DEFAULTS["tournament_size"],
        crossover_probability=GA_DEFAULTS["crossover_probability"],
        mutation_probability=GA_DEFAULTS["mutation_probability"],
        mutation_sigma_scale=GA_DEFAULTS["mutation_sigma_scale"],
        rng_seed=ga_seed,
        log_path=seed_dir / "evaluations_ga.csv",
        fitness_weights=weights,
    )

    best = result["best"]
    params = best["params"]
    best_metrics = evaluate_candidate(
        params=params,
        seeds=evaluation_seeds,
        layout_name=HOSPITAL_SIM_SETTINGS["layout"],
        sim_settings=HOSPITAL_SIM_SETTINGS,
        method="ga_best_recheck",
        generation=None,
        individual_id=None,
        log_path=None,
        cache=None,
        fitness_weights=weights,
    )

    (seed_dir / "best_ga.json").write_text(json.dumps(best, indent=2), encoding="utf-8")
    (seed_dir / "ga_history.json").write_text(json.dumps(result["history"], indent=2), encoding="utf-8")

    fairness_gap = best_metrics["fairness_gap_time"]
    if fairness_gap is None:
        fairness_gap = best_metrics["total_time"]

    return {
        "ga_seed": ga_seed,
        "best_fitness": float(best["fitness"]),
        "mean_time": float(best_metrics["total_time"]),
        "mean_fairness_gap": float(fairness_gap),
        "mean_collisions": float(best_metrics["near_collisions"]),
        "mean_congestion": float(best_metrics["mean_congestion"]),
        "accel_factor": float(params[0]),
        "agent_rep_weight": float(params[1]),
        "agent_radius": float(params[2]),
        "all_evacuated": bool(best_metrics["all_evacuated"]),
        "best_ga": best,
        "ga_history": result["history"],
        "ga_settings": result["ga_settings"],
    }


def run_weight_sweep(out_root, evaluation_seeds, ga_seeds):
    out_root.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    attempt_rows = []

    for idx, (w_time, w_fair) in enumerate(WEIGHT_PAIRS, start=1):
        weights = build_fitness_weights(w_time, w_fair)
        pair_dir = out_root / weight_dir_name(w_time, w_fair)
        pair_dir.mkdir(parents=True, exist_ok=True)

        candidates = []
        for ga_seed in ga_seeds:
            attempt = run_ga_for_seed(pair_dir, ga_seed, weights, evaluation_seeds)
            attempt_rows.append(
                {
                    "pair_index": idx,
                    "w_time": w_time,
                    "w_fair": w_fair,
                    "weight_label": f"({w_time:g}, {w_fair:g})",
                    **{k: attempt[k] for k in attempt if k not in ("best_ga", "ga_history", "ga_settings")},
                }
            )
            candidates.append(attempt)

        winner = min(candidates, key=lambda c: c["best_fitness"])
        (pair_dir / "best_ga.json").write_text(json.dumps(winner["best_ga"], indent=2), encoding="utf-8")
        (pair_dir / "ga_history.json").write_text(json.dumps(winner["ga_history"], indent=2), encoding="utf-8")
        (pair_dir / "best_selected.json").write_text(
            json.dumps(
                {
                    "selected_ga_seed": winner["ga_seed"],
                    "selected_best_fitness": winner["best_fitness"],
                    "all_attempts": [
                        {"ga_seed": c["ga_seed"], "best_fitness": c["best_fitness"], "mean_collisions": c["mean_collisions"]}
                        for c in candidates
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (pair_dir / "meta.json").write_text(
            json.dumps(
                {
                    "pair_index": idx,
                    "w_time": w_time,
                    "w_fair": w_fair,
                    "ga_seeds": ga_seeds,
                    "selected_ga_seed": winner["ga_seed"],
                    "evaluation_seeds": evaluation_seeds,
                    "fitness_weights": weights,
                    "ga_settings": winner["ga_settings"],
                    "sim_settings": HOSPITAL_SIM_SETTINGS,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        summary_rows.append(
            {
                "pair_index": idx,
                "w_time": w_time,
                "w_fair": w_fair,
                "weight_label": f"({w_time:g}, {w_fair:g})",
                "ga_seed_selected": winner["ga_seed"],
                "n_ga_seeds": len(ga_seeds),
                "best_fitness": winner["best_fitness"],
                "mean_time": winner["mean_time"],
                "mean_fairness_gap": winner["mean_fairness_gap"],
                "mean_collisions": winner["mean_collisions"],
                "mean_congestion": winner["mean_congestion"],
                "accel_factor": winner["accel_factor"],
                "agent_rep_weight": winner["agent_rep_weight"],
                "agent_radius": winner["agent_radius"],
                "all_evacuated": winner["all_evacuated"],
            }
        )

    summary_csv = out_root / "summary_by_weights.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    attempts_csv = out_root / "all_ga_seed_attempts.csv"
    with attempts_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(attempt_rows[0].keys()))
        writer.writeheader()
        writer.writerows(attempt_rows)

    return summary_rows, attempt_rows, summary_csv, attempts_csv


def build_aggregate_stats(df, attempt_df, ga_seeds):
    stats = {
        "n_weight_pairs": int(len(df)),
        "ga_seeds_per_pair": ga_seeds,
        "n_ga_seeds_per_pair": len(ga_seeds),
        "selection_rule": "lowest_best_fitness_across_seeds",
        "weight_pairs": [{"w_time": float(r["w_time"]), "w_fair": float(r["w_fair"])} for _, r in df.iterrows()],
    }

    if len(df) >= 3:
        stats["spearman_w_fair_vs_mean_fairness_gap"] = float(
            df["w_fair"].corr(df["mean_fairness_gap"], method="spearman")
        )
        stats["spearman_w_fair_vs_mean_time"] = float(df["w_fair"].corr(df["mean_time"], method="spearman"))
        stats["spearman_w_fair_vs_mean_collisions"] = float(
            df["w_fair"].corr(df["mean_collisions"], method="spearman")
        )

    stats["per_pair"] = df.to_dict(orient="records")
    stats["all_attempts"] = attempt_df.to_dict(orient="records")
    return stats


def plot_pareto_front(out_root, df):
    pareto_png = out_root / "pareto_time_vs_fairness.png"

    x = df["mean_time"].to_numpy()
    y = df["mean_fairness_gap"].to_numpy()
    colors = df["mean_collisions"].to_numpy()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, linestyle="--", color="gray", alpha=0.5, zorder=1)
    scatter = ax.scatter(
        x,
        y,
        c=colors,
        s=110,
        cmap="YlOrRd",
        edgecolors="black",
        linewidths=0.6,
        zorder=2,
    )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Mean Near-Collisions (Safety)")

    for _, row in df.iterrows():
        ax.annotate(
            row["weight_label"],
            (row["mean_time"], row["mean_fairness_gap"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
        )

    ax.set_title("Weight Sensitivity: Time vs Fairness (color = collisions)")
    ax.set_xlabel("Mean Evacuation Time (s)")
    ax.set_ylabel("Mean Fairness Gap (s)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(pareto_png, dpi=200)
    plt.close(fig)

    return {"pareto_png": str(pareto_png)}


def postprocess_results(out_root, ga_seeds):
    summary_csv = out_root / "summary_by_weights.csv"
    attempts_csv = out_root / "all_ga_seed_attempts.csv"
    if not summary_csv.exists():
        raise FileNotFoundError(f"Missing {summary_csv}; run the experiment first or check --out.")
    if not attempts_csv.exists():
        raise FileNotFoundError(f"Missing {attempts_csv}; run the experiment first or check --out.")

    df = pd.read_csv(summary_csv)
    attempt_df = pd.read_csv(attempts_csv)
    stats_payload = build_aggregate_stats(df, attempt_df, ga_seeds)
    stats_path = out_root / "aggregate_stats.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    plot_paths = plot_pareto_front(out_root, df)
    return summary_csv, attempts_csv, stats_path, plot_paths


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 2: weight sensitivity and Pareto trade-off on hospital_corridor."
    )
    parser.add_argument(
        "--out",
        default="results/experiment2_weight_sensitivity_hospital",
        help="Output directory for all generated artifacts.",
    )
    parser.add_argument(
        "--ga-seeds",
        nargs="*",
        type=int,
        default=None,
        help=(
            "GA seeds per weight pair; best fitness across seeds is selected "
            f"(default: {DEFAULT_GA_SEEDS} for a full run; inferred from CSV in --recover mode)."
        ),
    )
    parser.add_argument(
        "--evaluation-seeds",
        nargs="*",
        type=int,
        default=[11, 29, 47, 53, 61, 73, 89, 97, 101, 109],
        help="Simulation seeds used inside each candidate fitness evaluation.",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Rebuild stats and plots from existing CSVs without re-running the GA sweep.",
    )
    args = parser.parse_args()

    out_root = (ROOT / args.out).resolve()

    if args.recover:
        attempts_csv = out_root / "all_ga_seed_attempts.csv"
        if not attempts_csv.exists():
            raise SystemExit(f"Cannot recover: missing {attempts_csv}")
        if args.ga_seeds:
            ga_seeds = args.ga_seeds
        else:
            attempt_df = pd.read_csv(attempts_csv)
            ga_seeds = sorted(attempt_df["ga_seed"].unique().tolist())
        if not ga_seeds:
            raise SystemExit("Cannot recover: no GA seeds found in all_ga_seed_attempts.csv.")
        summary_csv, attempts_csv, stats_path, plot_paths = postprocess_results(out_root, ga_seeds)
    else:
        ga_seeds = args.ga_seeds if args.ga_seeds is not None else DEFAULT_GA_SEEDS
        if not ga_seeds:
            raise SystemExit("Provide at least one GA seed via --ga-seeds.")
        _, _, summary_csv, attempts_csv = run_weight_sweep(
            out_root, args.evaluation_seeds, ga_seeds
        )
        _, _, stats_path, plot_paths = postprocess_results(out_root, ga_seeds)

    print("Done. Outputs in:")
    print(f"- {out_root}")
    print(f"- {summary_csv}")
    print(f"- {attempts_csv}")
    print(f"- {stats_path}")
    print(f"- {plot_paths['pareto_png']}")


if __name__ == "__main__":
    main()
