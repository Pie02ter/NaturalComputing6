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


EVAL_BUDGET = 600

GA_CONFIGS = {
    "A_default": {
        "label": "A (Default)",
        "population_size": 24,
        "generations": 25,
        "mutation_probability": 0.2,
    },
    "B_exploration": {
        "label": "B (Exploration)",
        "population_size": 60,
        "generations": 10,
        "mutation_probability": 0.3,
    },
    "C_exploitation": {
        "label": "C (Exploitation)",
        "population_size": 10,
        "generations": 60,
        "mutation_probability": 0.1,
    },
}

CONFIG_COLORS = {
    "A_default": "#2563eb",
    "B_exploration": "#059669",
    "C_exploitation": "#dc2626",
}

DEFAULT_GA_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001]

HOSPITAL_SIM_SETTINGS = {
    "layout": "hospital_corridor",
    "num_high": 28,
    "num_low": 12,
    "max_ticks": 1000,
    "dt": 0.1,
    "frame_stride": 4,
    "seed": 42,
}

STANDARD_FITNESS_WEIGHTS = dict(DEFAULT_FITNESS_WEIGHTS)


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def assert_eval_budgets(configs=None, expected_budget=EVAL_BUDGET):
    configs = GA_CONFIGS if configs is None else configs
    for name, cfg in configs.items():
        budget = cfg["population_size"] * cfg["generations"]
        if budget != expected_budget:
            raise ValueError(f"Config {name} budget is {budget}, expected {expected_budget}")


def kruskal_wallis(groups):
    arrays = [np.asarray(g, dtype=float) for g in groups]
    k = len(arrays)
    n_total = sum(len(g) for g in arrays)
    if k < 2 or n_total == 0:
        return {"H": 0.0, "df": 0, "p_value": 1.0}

    combined = np.concatenate(arrays)
    ranks = pd.Series(combined).rank(method="average").to_numpy()

    h_stat = 0.0
    offset = 0
    for group in arrays:
        n = len(group)
        group_ranks = ranks[offset : offset + n]
        h_stat += float(group_ranks.sum()) ** 2 / n
        offset += n

    h_stat = (12.0 / (n_total * (n_total + 1))) * h_stat - 3.0 * (n_total + 1)
    df = k - 1
    p_value = math.exp(-h_stat / 2.0) if df == 2 else None
    if p_value is None:
        z = math.sqrt(2.0 * h_stat) - math.sqrt(2.0 * df - 1.0)
        p_value = 2.0 * (1.0 - normal_cdf(abs(z)))

    return {"H": float(h_stat), "df": int(df), "p_value": float(p_value)}


def mann_whitney_u(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return {"U": 0.0, "z": 0.0, "p_value_two_sided": 1.0}

    combined = np.concatenate([x, y])
    ranks = pd.Series(combined).rank(method="average").to_numpy()
    r1 = float(ranks[:n1].sum())
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u2 = n1 * n2 - u1
    u_stat = min(u1, u2)

    mu = n1 * n2 / 2.0
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    if sigma == 0:
        return {"U": float(u_stat), "z": 0.0, "p_value_two_sided": 1.0}

    z = (u_stat - mu) / sigma
    p_value = 2.0 * (1.0 - normal_cdf(abs(z)))
    return {"U": float(u_stat), "z": float(z), "p_value_two_sided": float(p_value)}


def run_single_ga(config_name, config, ga_seed, evaluation_seeds, run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "evaluations_ga.csv"

    result = run_ga(
        seeds=evaluation_seeds,
        layout_name=HOSPITAL_SIM_SETTINGS["layout"],
        sim_settings=HOSPITAL_SIM_SETTINGS,
        population_size=config["population_size"],
        generations=config["generations"],
        elite_count=GA_DEFAULTS["elite_count"],
        tournament_size=GA_DEFAULTS["tournament_size"],
        crossover_probability=GA_DEFAULTS["crossover_probability"],
        mutation_probability=config["mutation_probability"],
        mutation_sigma_scale=GA_DEFAULTS["mutation_sigma_scale"],
        rng_seed=ga_seed,
        log_path=log_path,
        fitness_weights=STANDARD_FITNESS_WEIGHTS,
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
        fitness_weights=STANDARD_FITNESS_WEIGHTS,
    )

    (run_dir / "best_ga.json").write_text(json.dumps(best, indent=2), encoding="utf-8")
    (run_dir / "ga_history.json").write_text(json.dumps(result["history"], indent=2), encoding="utf-8")
    (run_dir / "meta.json").write_text(
        json.dumps(
            {
                "config_name": config_name,
                "config_label": config["label"],
                "ga_seed": ga_seed,
                "evaluation_seeds": evaluation_seeds,
                "fitness_weights": STANDARD_FITNESS_WEIGHTS,
                "ga_settings": result["ga_settings"],
                "sim_settings": HOSPITAL_SIM_SETTINGS,
                "eval_budget": EVAL_BUDGET,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    fairness_gap = best_metrics["fairness_gap_time"]
    if fairness_gap is None:
        fairness_gap = best_metrics["total_time"]

    convergence_rows = extract_convergence_stats(
        log_path=log_path,
        config_name=config_name,
        config_label=config["label"],
        ga_seed=ga_seed,
        population_size=config["population_size"],
    )

    summary_row = {
        "config_name": config_name,
        "config_label": config["label"],
        "ga_seed": ga_seed,
        "population_size": config["population_size"],
        "generations": config["generations"],
        "mutation_probability": config["mutation_probability"],
        "best_fitness": float(best["fitness"]),
        "mean_time": float(best_metrics["total_time"]),
        "mean_fairness_gap": float(fairness_gap),
        "mean_collisions": float(best_metrics["near_collisions"]),
        "mean_congestion": float(best_metrics["mean_congestion"]),
        "accel_factor": float(params[0]),
        "agent_rep_weight": float(params[1]),
        "agent_radius": float(params[2]),
        "all_evacuated": bool(best_metrics["all_evacuated"]),
    }
    return summary_row, convergence_rows


def extract_convergence_stats(log_path, config_name, config_label, ga_seed, population_size):
    df = pd.read_csv(log_path)
    df = df[df["method"] == "ga"].copy()
    if df.empty:
        return []

    grouped = (
        df.groupby("generation", as_index=False)["fitness"]
        .agg(min_fitness="min", max_fitness="max", mean_fitness="mean")
        .sort_values("generation")
    )
    grouped["best_so_far"] = grouped["min_fitness"].cummin()
    grouped["cumulative_evaluations"] = (grouped["generation"] + 1) * population_size
    grouped["config_name"] = config_name
    grouped["config_label"] = config_label
    grouped["ga_seed"] = ga_seed
    grouped["population_size"] = population_size
    return grouped.to_dict(orient="records")


def run_ablation(out_root, evaluation_seeds, ga_seeds, configs=None):
    out_root.mkdir(parents=True, exist_ok=True)
    configs = GA_CONFIGS if configs is None else configs
    summary_rows = []
    convergence_rows = []

    for config_name, config in configs.items():
        config_dir = out_root / "configs" / config_name
        for ga_seed in ga_seeds:
            run_dir = config_dir / f"seed_{ga_seed}"
            summary_row, conv_rows = run_single_ga(
                config_name, config, ga_seed, evaluation_seeds, run_dir
            )
            summary_rows.append(summary_row)
            convergence_rows.extend(conv_rows)

    summary_csv = out_root / "summary_per_run.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    convergence_csv = out_root / "convergence_by_eval.csv"
    pd.DataFrame(convergence_rows).to_csv(convergence_csv, index=False)

    return summary_rows, convergence_rows, summary_csv, convergence_csv


def build_aggregate_stats(summary_df, configs=None, eval_budget=EVAL_BUDGET):
    configs = GA_CONFIGS if configs is None else configs
    stats = {
        "eval_budget": eval_budget,
        "configs": {},
        "kruskal_wallis_final_fitness": None,
        "mann_whitney_posthoc_bonferroni": [],
    }

    groups = []
    group_names = []
    for config_name in configs:
        subset = summary_df[summary_df["config_name"] == config_name]["best_fitness"].astype(float)
        values = subset.to_numpy()
        groups.append(values)
        group_names.append(config_name)
        q1, q3 = np.percentile(values, [25, 75])
        stats["configs"][config_name] = {
            "label": GA_CONFIGS[config_name]["label"],
            "n": int(len(values)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "median": float(np.median(values)),
            "iqr": float(q3 - q1),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }

    if all(len(g) > 0 for g in groups) and len(groups) >= 2:
        stats["kruskal_wallis_final_fitness"] = kruskal_wallis(groups)

        pairs = [
            ("A_default", "B_exploration"),
            ("A_default", "C_exploitation"),
            ("B_exploration", "C_exploitation"),
        ]
        raw_tests = []
        for left, right in pairs:
            result = mann_whitney_u(
                summary_df[summary_df["config_name"] == left]["best_fitness"].to_numpy(),
                summary_df[summary_df["config_name"] == right]["best_fitness"].to_numpy(),
            )
            raw_tests.append(
                {
                    "comparison": f"{left}_vs_{right}",
                    "left": left,
                    "right": right,
                    **result,
                }
            )

        bonferroni_factor = len(raw_tests)
        for test in raw_tests:
            test["p_value_bonferroni"] = min(1.0, test["p_value_two_sided"] * bonferroni_factor)
            stats["mann_whitney_posthoc_bonferroni"].append(test)

    return stats


def plot_convergence_vs_evaluations(out_root, convergence_df, configs=None, eval_budget=EVAL_BUDGET):
    configs = GA_CONFIGS if configs is None else configs
    png_path = out_root / "convergence_vs_evaluations.png"

    fig, ax = plt.subplots(figsize=(10, 6))

    for config_name, config in configs.items():
        subset = convergence_df[convergence_df["config_name"] == config_name]
        color = CONFIG_COLORS[config_name]

        for ga_seed, seed_df in subset.groupby("ga_seed"):
            seed_df = seed_df.sort_values("cumulative_evaluations")
            ax.plot(
                seed_df["cumulative_evaluations"],
                seed_df["mean_fitness"],
                color=color,
                alpha=0.15,
                linewidth=1.0,
            )

        agg = (
            subset.groupby("cumulative_evaluations", as_index=False)
            .agg(
                mean_fitness=("mean_fitness", "mean"),
                min_fitness=("min_fitness", "min"),
                max_fitness=("max_fitness", "max"),
                best_so_far=("best_so_far", "mean"),
            )
            .sort_values("cumulative_evaluations")
        )
        ax.fill_between(
            agg["cumulative_evaluations"],
            agg["min_fitness"],
            agg["max_fitness"],
            color=color,
            alpha=0.12,
        )
        ax.plot(
            agg["cumulative_evaluations"],
            agg["mean_fitness"],
            color=color,
            linewidth=2.5,
            linestyle="-",
        )
        ax.plot(
            agg["cumulative_evaluations"],
            agg["best_so_far"],
            color=color,
            linewidth=1.5,
            linestyle="--",
            label=config["label"],
        )

    ax.set_title("GA Ablation: Population Mean Fitness vs Evaluation Budget")
    ax.set_xlabel("Cumulative Evaluations")
    ax.set_ylabel("Population Mean Fitness (lower is better)")
    ax.set_xlim(0, eval_budget)
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    plt.close(fig)

    return {"convergence_png": str(png_path)}


def plot_best_fitness_boxplot(out_root, summary_df, configs=None):
    configs = GA_CONFIGS if configs is None else configs
    png_path = out_root / "best_fitness_boxplot_by_config.png"
    plot_rng = np.random.default_rng(0)

    labels = [configs[name]["label"] for name in configs]
    data = [
        summary_df[summary_df["config_name"] == name]["best_fitness"].astype(float).to_numpy()
        for name in configs
    ]
    colors = [CONFIG_COLORS[name] for name in configs]

    fig, ax = plt.subplots(figsize=(8, 5))
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)

    for idx, (name, values) in enumerate(zip(configs, data), start=1):
        x = plot_rng.normal(loc=idx, scale=0.04, size=len(values))
        ax.scatter(x, values, s=28, alpha=0.75, color=CONFIG_COLORS[name], edgecolors="black", linewidths=0.4)

    ax.set_title("Final Best Fitness by GA Configuration (10 Seeds)")
    ax.set_ylabel("Best Fitness (lower is better)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(png_path, dpi=200)
    plt.close(fig)

    return {"boxplot_png": str(png_path)}


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 3: GA hyperparameter ablation on hospital_corridor."
    )
    parser.add_argument(
        "--out",
        default="results/experiment3_ga_ablation_hospital",
        help="Output directory for all generated artifacts.",
    )
    parser.add_argument(
        "--ga-seeds",
        nargs="*",
        type=int,
        default=DEFAULT_GA_SEEDS,
        help="GA seeds per configuration (10 recommended for statistical power).",
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

    configs = GA_CONFIGS
    eval_budget = EVAL_BUDGET
    if args.quick:
        args.ga_seeds = args.ga_seeds[:1]
        args.evaluation_seeds = args.evaluation_seeds[:1]
        configs = {
            "A_default": {**GA_CONFIGS["A_default"], "population_size": 6, "generations": 3},
            "B_exploration": {**GA_CONFIGS["B_exploration"], "population_size": 9, "generations": 2},
            "C_exploitation": {**GA_CONFIGS["C_exploitation"], "population_size": 3, "generations": 6},
        }
        eval_budget = 18

    assert_eval_budgets(configs=configs, expected_budget=eval_budget)

    if not args.ga_seeds:
        raise SystemExit("Provide at least one GA seed via --ga-seeds.")

    out_root = (ROOT / args.out).resolve()
    summary_rows, _, summary_csv, convergence_csv = run_ablation(
        out_root, args.evaluation_seeds, args.ga_seeds, configs=configs
    )

    summary_df = pd.DataFrame(summary_rows)
    convergence_df = pd.read_csv(convergence_csv)

    stats_payload = build_aggregate_stats(summary_df, configs=configs, eval_budget=eval_budget)
    stats_path = out_root / "aggregate_stats.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    plot_paths = {}
    plot_paths.update(plot_convergence_vs_evaluations(out_root, convergence_df, configs=configs, eval_budget=eval_budget))
    plot_paths.update(plot_best_fitness_boxplot(out_root, summary_df, configs=configs))

    print("Done. Outputs in:")
    print(f"- {out_root}")
    print(f"- {summary_csv}")
    print(f"- {convergence_csv}")
    print(f"- {stats_path}")
    print(f"- {plot_paths['convergence_png']}")
    print(f"- {plot_paths['boxplot_png']}")


if __name__ == "__main__":
    main()
