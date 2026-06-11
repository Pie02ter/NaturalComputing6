#!/usr/bin/env python3
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.config import DEFAULT_FITNESS_WEIGHTS, GA_DEFAULTS
from crowd_evac.ga import evaluate_candidate, run_ga


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_sided_binomial_p_value(successes, trials, p0=0.5):
    observed_prob = math.comb(trials, successes) * (p0**successes) * ((1.0 - p0) ** (trials - successes))
    p_value = 0.0
    for k in range(trials + 1):
        prob = math.comb(trials, k) * (p0**k) * ((1.0 - p0) ** (trials - k))
        if prob <= observed_prob + 1e-15:
            p_value += prob
    return min(1.0, p_value)


def mann_kendall_test(series):
    values = np.asarray(series, dtype=float)
    n = values.size
    if n < 3:
        return {"n": int(n), "S": 0, "var_S": 0.0, "Z": 0.0, "p_value": 1.0}

    s_stat = 0
    for i in range(n - 1):
        s_stat += int(np.sum(np.sign(values[i + 1 :] - values[i])))

    _, counts = np.unique(values, return_counts=True)
    tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if var_s <= 0:
        return {"n": int(n), "S": int(s_stat), "var_S": float(var_s), "Z": 0.0, "p_value": 1.0}

    if s_stat > 0:
        z_stat = (s_stat - 1) / math.sqrt(var_s)
    elif s_stat < 0:
        z_stat = (s_stat + 1) / math.sqrt(var_s)
    else:
        z_stat = 0.0
    p_value = 2.0 * (1.0 - normal_cdf(abs(z_stat)))
    return {"n": int(n), "S": int(s_stat), "var_S": float(var_s), "Z": float(z_stat), "p_value": float(p_value)}


def run_experiment(out_root, ga_seeds, evaluation_seeds, ga_settings=None):
    out_root.mkdir(parents=True, exist_ok=True)
    runs_dir = out_root / "runs"
    runs_dir.mkdir(exist_ok=True)

    weights = {
        "time": 1.0,
        "collisions": 0.05,
        "congestion": 1.0,
        "fairness": 2.0,
        "incomplete_base": DEFAULT_FITNESS_WEIGHTS["incomplete_base"],
        "incomplete_agent": DEFAULT_FITNESS_WEIGHTS["incomplete_agent"],
    }
    sim_settings = {
        "layout": "hospital_corridor",
        "num_high": 28,
        "num_low": 12,
        "max_ticks": 1000,
        "dt": 0.1,
        "frame_stride": 4,
        "seed": 42,
    }
    ga_settings = dict(GA_DEFAULTS if ga_settings is None else ga_settings)

    run_rows = []
    convergence_rows = []

    for idx, ga_seed in enumerate(ga_seeds, start=1):
        run_name = f"run_{idx:02d}"
        run_dir = runs_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        result = run_ga(
            seeds=evaluation_seeds,
            layout_name=sim_settings["layout"],
            sim_settings=sim_settings,
            population_size=ga_settings["population_size"],
            generations=ga_settings["generations"],
            elite_count=ga_settings["elite_count"],
            tournament_size=ga_settings["tournament_size"],
            crossover_probability=ga_settings["crossover_probability"],
            mutation_probability=ga_settings["mutation_probability"],
            mutation_sigma_scale=ga_settings["mutation_sigma_scale"],
            rng_seed=ga_seed,
            log_path=run_dir / "evaluations_ga.csv",
            fitness_weights=weights,
        )

        best = result["best"]
        history = result["history"]
        params = best["params"]
        best_metrics = evaluate_candidate(
            params=params,
            seeds=evaluation_seeds,
            layout_name=sim_settings["layout"],
            sim_settings=sim_settings,
            method="ga_best_recheck",
            generation=None,
            individual_id=None,
            log_path=None,
            cache=None,
            fitness_weights=weights,
        )

        (run_dir / "best_ga.json").write_text(json.dumps(best, indent=2), encoding="utf-8")
        (run_dir / "ga_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        (run_dir / "meta.json").write_text(
            json.dumps(
                {
                    "ga_seed": ga_seed,
                    "evaluation_seeds": evaluation_seeds,
                    "weights": weights,
                    "ga_settings": result["ga_settings"],
                    "sim_settings": sim_settings,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        run_rows.append(
            {
                "run": idx,
                "run_name": run_name,
                "ga_seed": ga_seed,
                "best_fitness": float(best["fitness"]),
                "accel_factor": float(params[0]),
                "agent_rep_weight": float(params[1]),
                "agent_radius": float(params[2]),
                "mean_time": float(best_metrics["total_time"]),
                "mean_collisions": float(best_metrics["near_collisions"]),
                "mean_fairness_gap": float(best_metrics["fairness_gap_time"]),
            }
        )

        for h in history:
            convergence_rows.append(
                {
                    "run": idx,
                    "run_name": run_name,
                    "ga_seed": ga_seed,
                    "generation": int(h["generation"]),
                    "best_fitness": float(h["best_fitness"]),
                }
            )

    summary_csv = out_root / "summary_per_run.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(run_rows[0].keys()))
        writer.writeheader()
        writer.writerows(run_rows)

    convergence_csv = out_root / "ga_convergence_all_runs.csv"
    pd.DataFrame(convergence_rows).to_csv(convergence_csv, index=False)

    return {
        "run_rows": run_rows,
        "convergence_rows": convergence_rows,
        "summary_csv": summary_csv,
        "convergence_csv": convergence_csv,
        "weights": weights,
        "sim_settings": sim_settings,
    }


def build_statistics(run_rows, convergence_rows):
    df_runs = pd.DataFrame(run_rows)
    df_conv = pd.DataFrame(convergence_rows)

    stats_payload = {"n_runs": int(len(df_runs))}
    numeric_cols = [
        "best_fitness",
        "accel_factor",
        "agent_rep_weight",
        "agent_radius",
        "mean_time",
        "mean_collisions",
        "mean_fairness_gap",
    ]

    for col in numeric_cols:
        values = df_runs[col].astype(float).to_numpy()
        stats_payload[col] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    by_gen = (
        df_conv.groupby("generation", as_index=False)["best_fitness"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "mean_best_fitness", "std": "std_best_fitness"})
    )
    by_gen_records = by_gen.to_dict(orient="records")
    stats_payload["convergence_by_generation"] = by_gen_records

    mk = mann_kendall_test(by_gen["mean_best_fitness"].to_numpy())
    stats_payload["mann_kendall_mean_convergence"] = mk

    first_last = df_conv.sort_values(["run", "generation"]).groupby("run").agg(first=("best_fitness", "first"), last=("best_fitness", "last"))
    improvements = (first_last["first"] - first_last["last"]).to_numpy()
    success_count = int(np.sum(improvements > 0))
    sign_p = two_sided_binomial_p_value(success_count, len(improvements), p0=0.5)
    stats_payload["sign_test_improvement"] = {
        "runs_with_improvement": success_count,
        "total_runs": int(len(improvements)),
        "p_value_two_sided": float(sign_p),
        "mean_improvement": float(np.mean(improvements)),
        "median_improvement": float(np.median(improvements)),
    }

    return stats_payload, by_gen


def make_plots(out_root, df_runs, by_gen):
    boxplot_png = out_root / "parameter_variance_boxplot.png"
    conv_png = out_root / "ga_convergence_runs.png"

    params_cols = ["accel_factor", "agent_rep_weight", "agent_radius"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    for ax, col in zip(axes, params_cols):
        y = df_runs[col].to_numpy()
        ax.boxplot([y], tick_labels=[col], showfliers=False)
        x = np.random.normal(loc=1.0, scale=0.04, size=len(y))
        ax.scatter(x, y, s=22, alpha=0.75)
        ax.set_title(col)
        ax.set_ylabel("Value")
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Variance of GA-Optimized Parameters Across 10 Independent Runs", y=1.02)
    fig.tight_layout()
    fig.savefig(boxplot_png, dpi=200)
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(by_gen["generation"], by_gen["mean_best_fitness"], linewidth=2.8, label="Mean across runs")
    lower = by_gen["mean_best_fitness"] - by_gen["std_best_fitness"].fillna(0.0)
    upper = by_gen["mean_best_fitness"] + by_gen["std_best_fitness"].fillna(0.0)
    plt.fill_between(by_gen["generation"], lower, upper, alpha=0.2, label="Mean ± 1 SD")
    plt.title("GA Convergence on Hospital Corridor (10 Independent Runs)")
    plt.xlabel("Generation")
    plt.ylabel("Best Fitness (lower is better)")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(conv_png, dpi=200)
    plt.close()

    return {
        "parameter_boxplot_png": str(boxplot_png),
        "convergence_png": str(conv_png),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 1 baseline-stability runner for hospital_corridor with report-ready outputs."
    )
    parser.add_argument(
        "--out",
        default="results/experiment1_baseline_stability_hospital",
        help="Output directory for all generated artifacts.",
    )
    parser.add_argument(
        "--ga-seeds",
        nargs="*",
        type=int,
        default=[101, 202, 303, 404, 505, 606, 707, 808, 909, 1001],
        help="Independent GA random seeds (10 recommended).",
    )
    parser.add_argument(
        "--evaluation-seeds",
        nargs="*",
        type=int,
        default=[11, 29, 47, 53, 61, 73, 89, 97, 101, 109],
        help="Simulation seeds used inside each candidate fitness evaluation.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Tiny run for pipeline testing; full paper settings remain the default.",
    )
    args = parser.parse_args()

    ga_settings = dict(GA_DEFAULTS)
    if args.quick:
        args.ga_seeds = args.ga_seeds[:1]
        args.evaluation_seeds = args.evaluation_seeds[:1]
        ga_settings.update({"population_size": 6, "generations": 3, "elite_count": 1, "tournament_size": 2})

    out_root = (ROOT / args.out).resolve()
    eval_result = run_experiment(out_root, args.ga_seeds, args.evaluation_seeds, ga_settings=ga_settings)
    stats_payload, by_gen = build_statistics(eval_result["run_rows"], eval_result["convergence_rows"])

    stats_path = out_root / "aggregate_stats.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    df_runs = pd.DataFrame(eval_result["run_rows"])
    plot_paths = make_plots(out_root, df_runs, by_gen)

    print("Done. Outputs in:")
    print(f"- {out_root}")
    print(f"- {eval_result['summary_csv']}")
    print(f"- {eval_result['convergence_csv']}")
    print(f"- {stats_path}")
    print(f"- {plot_paths['parameter_boxplot_png']}")
    print(f"- {plot_paths['convergence_png']}")


if __name__ == "__main__":
    main()
