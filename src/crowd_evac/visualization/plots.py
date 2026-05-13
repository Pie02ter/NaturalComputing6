from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .styles import method_color, method_label


def _save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _summary_dataframe(entries):
    rows = []
    for entry in entries:
        row = dict(entry)
        row["label"] = entry.get("label", method_label(entry["method"]))
        row["color"] = method_color(entry["method"])
        rows.append(row)
    return pd.DataFrame(rows)


def plot_fitness_comparison(entries, output_dir):
    output_dir = Path(output_dir)
    summary = _summary_dataframe(entries)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(summary["label"], summary["fitness"], color=summary["color"])
    ax.set_ylabel("Fitness")
    ax.set_title("Scalar Fitness Comparison")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", alpha=0.25)
    path = output_dir / "fitness_comparison.png"
    _save(fig, path)
    return str(path)


def plot_metric_breakdown(entries, output_dir):
    output_dir = Path(output_dir)
    summary = _summary_dataframe(entries)
    metrics = [
        ("total_time", "Total time"),
        ("fairness_gap_time", "Fairness gap"),
        ("mean_congestion", "Mean congestion"),
        ("near_collisions", "Near-collisions"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (metric, title) in zip(axes.flatten(), metrics):
        ax.bar(summary["label"], summary[metric], color=summary["color"])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Method Metric Breakdown", y=1.02)
    path = output_dir / "metric_breakdown.png"
    _save(fig, path)
    return str(path)


def plot_ga_convergence(history, output_dir):
    output_dir = Path(output_dir)
    history = pd.DataFrame(history)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(history["generation"], history["best_fitness"], marker="o", color="#2563eb")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best fitness")
    ax.set_title("GA Convergence")
    ax.grid(True, alpha=0.3)
    path = output_dir / "ga_convergence.png"
    _save(fig, path)
    return str(path)


def plot_efficiency_fairness_tradeoff(entries, output_dir):
    output_dir = Path(output_dir)
    summary = _summary_dataframe(entries)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(summary["total_time"], summary["fairness_gap_time"], s=90, color=summary["color"])
    for _, row in summary.iterrows():
        ax.annotate(row["label"], (row["total_time"], row["fairness_gap_time"]), xytext=(6, 5), textcoords="offset points")
    ax.set_xlabel("Total time")
    ax.set_ylabel("Fairness gap time")
    ax.set_title("Efficiency-Fairness Tradeoff")
    ax.grid(True, alpha=0.3)
    path = output_dir / "efficiency_fairness_tradeoff.png"
    _save(fig, path)
    return str(path)


def plot_parameter_comparison(entries, output_dir):
    output_dir = Path(output_dir)
    summary = _summary_dataframe(entries)
    params = pd.DataFrame(summary["params"].tolist(), columns=["accel_factor", "agent_rep_weight", "agent_radius", "wall_rep_weight", "wall_radius"])
    params.insert(0, "label", summary["label"].tolist())
    params.insert(1, "color", summary["color"].tolist())
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, param in zip(axes, ["accel_factor", "agent_rep_weight", "agent_radius"]):
        ax.bar(params["label"], params[param], color=params["color"])
        ax.set_title(param)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Active Parameter Comparison", y=1.03)
    path = output_dir / "parameter_comparison.png"
    _save(fig, path)
    return str(path)


def make_standard_plots(entries, history, results_dir):
    plot_dir = Path(results_dir) / "plots"
    outputs = {
        "fitness_comparison": plot_fitness_comparison(entries, plot_dir),
        "metric_breakdown": plot_metric_breakdown(entries, plot_dir),
        "efficiency_fairness_tradeoff": plot_efficiency_fairness_tradeoff(entries, plot_dir),
        "parameter_comparison": plot_parameter_comparison(entries, plot_dir),
    }
    if history:
        outputs["ga_convergence"] = plot_ga_convergence(history, plot_dir)
    return outputs
