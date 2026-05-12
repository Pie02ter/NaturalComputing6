import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from checkpoint_pipeline import CHECKPOINT_RESULTS_DIR


METHOD_LABELS = {
    "fixed_default": "Fixed default",
    "random_search": "Random search",
    "ga_no_fairness": "GA no fairness",
    "ga_fairness": "GA fairness",
}


def _labels(methods):
    return [METHOD_LABELS.get(method, method) for method in methods]


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_convergence(results_path):
    no_fairness = pd.read_csv(results_path / "ga_no_fairness_convergence.csv")
    fairness = pd.read_csv(results_path / "ga_fairness_convergence.csv")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(no_fairness["generation"], no_fairness["best_fitness"], marker="o", label="GA no fairness (w_G=0)")
    ax.plot(fairness["generation"], fairness["best_fitness"], marker="o", label="GA fairness (w_G=1)")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best search fitness")
    ax.set_title("GA Convergence")
    ax.grid(True, alpha=0.3)
    ax.legend()
    _save(fig, results_path / "convergence.png")


def plot_method_comparison(summary, results_path):
    metrics = [
        ("total_time", "Total time"),
        ("fairness_gap_time", "Fairness gap"),
        ("mean_congestion", "Mean congestion"),
        ("near_collisions", "Near collisions"),
    ]
    methods = summary["method"].tolist()
    labels = _labels(methods)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (metric, title) in zip(axes.flatten(), metrics):
        ax.bar(labels, summary[metric], color="#2563eb")
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Checkpoint Method Comparison", y=1.02)
    _save(fig, results_path / "method_comparison.png")


def plot_group_times(summary, results_path):
    methods = summary["method"].tolist()
    labels = _labels(methods)
    x_positions = range(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 4.8))
    high_positions = [x - width / 2 for x in x_positions]
    low_positions = [x + width / 2 for x in x_positions]
    ax.bar(high_positions, summary["mean_high_time"], width=width, label="High mobility", color="#2563eb")
    ax.bar(low_positions, summary["mean_low_time"], width=width, label="Low mobility", color="#dc2626")
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Mean evacuation time")
    ax.set_title("Group Evacuation Times")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    _save(fig, results_path / "group_times.png")


def plot_efficiency_fairness_tradeoff(summary, results_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(summary["total_time"], summary["fairness_gap_time"], s=80, color="#7c3aed")
    for _, row in summary.iterrows():
        ax.annotate(METHOD_LABELS.get(row["method"], row["method"]), (row["total_time"], row["fairness_gap_time"]), xytext=(6, 5), textcoords="offset points")
    ax.set_xlabel("Total time")
    ax.set_ylabel("Fairness gap time")
    ax.set_title("Efficiency-Fairness Tradeoff")
    ax.grid(True, alpha=0.3)
    _save(fig, results_path / "efficiency_fairness_tradeoff.png")


def plot_checkpoint_results(results_dir=CHECKPOINT_RESULTS_DIR):
    results_path = Path(results_dir)
    summary = pd.read_csv(results_path / "checkpoint_summary.csv")
    plot_convergence(results_path)
    plot_method_comparison(summary, results_path)
    plot_group_times(summary, results_path)
    plot_efficiency_fairness_tradeoff(summary, results_path)
    return {
        "convergence_png": str(results_path / "convergence.png"),
        "method_comparison_png": str(results_path / "method_comparison.png"),
        "group_times_png": str(results_path / "group_times.png"),
        "efficiency_fairness_tradeoff_png": str(results_path / "efficiency_fairness_tradeoff.png"),
    }


def main():
    parser = argparse.ArgumentParser(description="Plot checkpoint experiment results.")
    parser.add_argument("--results-dir", default=str(CHECKPOINT_RESULTS_DIR), help="Directory containing checkpoint CSV files.")
    args = parser.parse_args()
    outputs = plot_checkpoint_results(args.results_dir)
    print("Checkpoint plots complete.")
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
