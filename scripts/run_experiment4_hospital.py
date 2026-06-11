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

from crowd_evac.config import LAYOUTS, sim_kwargs_from_layout
from crowd_evac.ga import merge_active_to_full
from crowd_evac.simulator import run_simulation


DEFAULT_EXP1_SUMMARY = ROOT / "results" / "experiment1_baseline_stability_hospital" / "summary_per_run.csv"

TOTAL_AGENTS = 40

POPULATION_SCENARIOS = {
    "balanced_50_50": {
        "label": "Default (50% high / 50% low)",
        "num_high": 20,
        "num_low": 20,
        "high_fraction": 0.5,
    },
    "high_dominant_80_20": {
        "label": "High-mobility dominant (80% / 20%)",
        "num_high": 32,
        "num_low": 8,
        "high_fraction": 0.8,
    },
    "low_dominant_20_80": {
        "label": "Low-mobility dominant / ICU-like (20% / 80%)",
        "num_high": 8,
        "num_low": 32,
        "high_fraction": 0.2,
    },
}

DEFAULT_SIMULATION_SEEDS = [
    11, 29, 47, 53, 61, 73, 89, 97, 101, 109,
    113, 127, 131, 137, 139, 149, 151, 157, 163, 167,
    173, 179, 181, 191, 193, 197, 199, 211, 223, 227,
]

HOSPITAL_BASE_SETTINGS = {
    "layout": "hospital_corridor",
    "max_ticks": 1000,
    "dt": 0.1,
    "frame_stride": 4,
}


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


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


def load_params_from_exp1(summary_path, ga_seed):
    summary_path = Path(summary_path)
    if not summary_path.exists():
        raise FileNotFoundError(
            f"Experiment 1 summary not found at {summary_path}. "
            "Run Experiment 1 first or pass --params-json with fixed parameters."
        )

    df = pd.read_csv(summary_path)
    required = {"ga_seed", "best_fitness", "accel_factor", "agent_rep_weight", "agent_radius"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Summary CSV missing columns: {sorted(missing)}")

    matches = df[df["ga_seed"].astype(int) == int(ga_seed)]
    if matches.empty:
        available = sorted(df["ga_seed"].astype(int).unique().tolist())
        raise ValueError(
            f"No Exp 1 run with ga_seed={ga_seed} in {summary_path}. Available seeds: {available}"
        )
    selected_row = matches.iloc[0]
    active = [
        float(selected_row["accel_factor"]),
        float(selected_row["agent_rep_weight"]),
        float(selected_row["agent_radius"]),
    ]
    full_params = merge_active_to_full(active).tolist()
    return {
        "source_summary": str(summary_path.resolve()),
        "selected_run": int(selected_row["run"]) if "run" in df.columns else None,
        "selected_ga_seed": int(selected_row["ga_seed"]),
        "exp1_best_fitness": float(selected_row["best_fitness"]),
        "active_params": active,
        "full_params": full_params,
    }


def load_params_from_json(params_json_path):
    payload = json.loads(Path(params_json_path).read_text(encoding="utf-8"))
    if "full_params" in payload:
        full_params = [float(x) for x in payload["full_params"]]
    elif "active_params" in payload:
        full_params = merge_active_to_full(payload["active_params"]).tolist()
    elif "params" in payload:
        full_params = [float(x) for x in payload["params"]]
    else:
        raise ValueError("params JSON must contain full_params, active_params, or params")
    if len(full_params) != 5:
        raise ValueError(f"Expected 5 full parameters, got {len(full_params)}")
    return {
        "source_summary": str(Path(params_json_path).resolve()),
        "selected_run": None,
        "selected_ga_seed": None,
        "exp1_best_fitness": None,
        "active_params": full_params[:3],
        "full_params": full_params,
    }


def run_scenario_evaluations(params_info, simulation_seeds):
    layout_name = HOSPITAL_BASE_SETTINGS["layout"]
    layout = LAYOUTS[layout_name]
    sim_kwargs = sim_kwargs_from_layout(layout)
    params = params_info["full_params"]
    rows = []

    for scenario_name, scenario in POPULATION_SCENARIOS.items():
        for seed in simulation_seeds:
            result = run_simulation(
                params=params,
                num_high=scenario["num_high"],
                num_low=scenario["num_low"],
                max_ticks=HOSPITAL_BASE_SETTINGS["max_ticks"],
                dt=HOSPITAL_BASE_SETTINGS["dt"],
                seed=int(seed),
                frame_stride=HOSPITAL_BASE_SETTINGS["frame_stride"],
                capture_frames=False,
                **sim_kwargs,
            )
            fairness_gap = result["fairness_gap_time"]
            if fairness_gap is None:
                fairness_gap = result["total_time"]

            rows.append(
                {
                    "scenario_name": scenario_name,
                    "scenario_label": scenario["label"],
                    "num_high": scenario["num_high"],
                    "num_low": scenario["num_low"],
                    "high_fraction": scenario["high_fraction"],
                    "simulation_seed": int(seed),
                    "total_time": float(result["total_time"]),
                    "fairness_gap_time": float(fairness_gap),
                    "near_collisions": float(result["near_collisions"]),
                    "mean_congestion": float(result["mean_congestion"]),
                    "all_evacuated": bool(result["all_evacuated"]),
                    "remaining_agents": int(result["remaining_agents"]),
                }
            )

    return rows


def build_aggregate_stats(df):
    stats = {
        "n_seeds_per_scenario": int(df.groupby("scenario_name").size().iloc[0]),
        "fixed_params": None,
        "scenarios": {},
        "kruskal_wallis_total_time": None,
        "kruskal_wallis_fairness_gap": None,
    }

    for scenario_name in POPULATION_SCENARIOS:
        subset = df[df["scenario_name"] == scenario_name]
        times = subset["total_time"].astype(float).to_numpy()
        gaps = subset["fairness_gap_time"].astype(float).to_numpy()
        q1_t, q3_t = np.percentile(times, [25, 75])
        q1_g, q3_g = np.percentile(gaps, [25, 75])
        stats["scenarios"][scenario_name] = {
            "label": POPULATION_SCENARIOS[scenario_name]["label"],
            "num_high": int(subset["num_high"].iloc[0]),
            "num_low": int(subset["num_low"].iloc[0]),
            "total_time": {
                "mean": float(np.mean(times)),
                "std": float(np.std(times, ddof=1)),
                "median": float(np.median(times)),
                "iqr": float(q3_t - q1_t),
                "min": float(np.min(times)),
                "max": float(np.max(times)),
            },
            "fairness_gap_time": {
                "mean": float(np.mean(gaps)),
                "std": float(np.std(gaps, ddof=1)),
                "median": float(np.median(gaps)),
                "iqr": float(q3_g - q1_g),
                "min": float(np.min(gaps)),
                "max": float(np.max(gaps)),
            },
            "all_evacuated_rate": float(subset["all_evacuated"].mean()),
        }

    time_groups = [
        df[df["scenario_name"] == name]["total_time"].astype(float).to_numpy()
        for name in POPULATION_SCENARIOS
    ]
    gap_groups = [
        df[df["scenario_name"] == name]["fairness_gap_time"].astype(float).to_numpy()
        for name in POPULATION_SCENARIOS
    ]
    stats["kruskal_wallis_total_time"] = kruskal_wallis(time_groups)
    stats["kruskal_wallis_fairness_gap"] = kruskal_wallis(gap_groups)
    return stats


def plot_metric_boxplots(out_root, df):
    time_png = out_root / "evacuation_time_by_scenario.png"
    gap_png = out_root / "fairness_gap_by_scenario.png"

    scenario_order = list(POPULATION_SCENARIOS.keys())
    labels = [POPULATION_SCENARIOS[name]["label"] for name in scenario_order]

    for metric, ylabel, png_path, title in [
        (
            "total_time",
            "Total Evacuation Time (s)",
            time_png,
            "Evacuation Time Across Population Mixtures (Fixed GA Parameters)",
        ),
        (
            "fairness_gap_time",
            "Fairness Gap (s)",
            gap_png,
            "Fairness Gap Across Population Mixtures (Fixed GA Parameters)",
        ),
    ]:
        data = [df[df["scenario_name"] == name][metric].astype(float).to_numpy() for name in scenario_order]
        fig, ax = plt.subplots(figsize=(9, 5))
        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("#93c5fd")
            patch.set_alpha(0.45)
        for idx, values in enumerate(data, start=1):
            x = np.random.normal(loc=idx, scale=0.04, size=len(values))
            ax.scatter(x, values, s=22, alpha=0.65, color="#1d4ed8", edgecolors="black", linewidths=0.3)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(png_path, dpi=200)
        plt.close(fig)

    return {
        "evacuation_time_png": str(time_png),
        "fairness_gap_png": str(gap_png),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Experiment 4: population heterogeneity stress test with fixed Exp 1 GA parameters."
    )
    parser.add_argument(
        "--out",
        default="results/experiment4_population_stress_hospital",
        help="Output directory for all generated artifacts.",
    )
    parser.add_argument(
        "--exp1-summary",
        default=str(DEFAULT_EXP1_SUMMARY),
        help="Path to Experiment 1 summary_per_run.csv for selecting parameters by GA seed.",
    )
    parser.add_argument(
        "--exp1-ga-seed",
        type=int,
        default=606,
        help="Experiment 1 GA seed whose optimized parameters are used (default: 606).",
    )
    parser.add_argument(
        "--params-json",
        help="Optional JSON with fixed params (overrides --exp1-summary).",
    )
    parser.add_argument(
        "--simulation-seeds",
        nargs="*",
        type=int,
        default=DEFAULT_SIMULATION_SEEDS,
        help="Simulation seeds per scenario (30 recommended).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Tiny run for pipeline testing; full paper settings remain the default.",
    )
    args = parser.parse_args()

    if args.quick:
        args.simulation_seeds = args.simulation_seeds[:2]

    if not args.simulation_seeds:
        raise SystemExit("Provide at least one simulation seed via --simulation-seeds.")

    for scenario in POPULATION_SCENARIOS.values():
        if scenario["num_high"] + scenario["num_low"] != TOTAL_AGENTS:
            raise ValueError("Each scenario must sum to TOTAL_AGENTS.")

    if args.params_json:
        params_info = load_params_from_json(args.params_json)
    else:
        params_info = load_params_from_exp1(args.exp1_summary, args.exp1_ga_seed)

    out_root = (ROOT / args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "fixed_params.json").write_text(json.dumps(params_info, indent=2), encoding="utf-8")

    rows = run_scenario_evaluations(params_info, args.simulation_seeds)
    results_csv = out_root / "per_seed_results.csv"
    with results_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    df = pd.DataFrame(rows)
    stats_payload = build_aggregate_stats(df)
    stats_payload["fixed_params"] = params_info
    stats_path = out_root / "aggregate_stats.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    plot_paths = plot_metric_boxplots(out_root, df)

    print("Done. Outputs in:")
    print(f"- {out_root}")
    print(f"- {results_csv}")
    print(f"- {stats_path}")
    print(f"- {plot_paths['evacuation_time_png']}")
    print(f"- {plot_paths['fairness_gap_png']}")


if __name__ == "__main__":
    main()
