import csv
import json
from pathlib import Path

from .visualization.styles import method_label


def best_summary_to_entries(standard):
    def entry(method, summary):
        return {
            "method": method,
            "label": method_label(method),
            "fitness": summary["fitness"],
            "params": summary["params"],
            "total_time": summary["total_time"],
            "near_collisions": summary["near_collisions"],
            "mean_congestion": summary["mean_congestion"],
            "fairness_gap_time": summary["fairness_gap_time"],
            "all_evacuated": summary["all_evacuated"],
            "remaining_agents": summary["remaining_agents"],
        }

    entries = [entry("default", standard["default"])]
    entries.extend(entry(method, summary) for method, summary in standard.get("heuristics", {}).items())
    entries.append(entry("random_search", standard["random"]))
    entries.append(entry("ga", standard["ga"]))
    return entries


def load_best_runs(results_dir):
    path = Path(results_dir) / "best_runs.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, payload["standard"]


def write_standard_summary(results_dir, standard, entries):
    results_dir = Path(results_dir)
    summary_csv = results_dir / "summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["method", "label", "fitness", "total_time", "fairness_gap_time", "mean_congestion", "near_collisions", "all_evacuated", "remaining_agents", "params"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            row = dict(entry)
            row["params"] = json.dumps(row["params"])
            writer.writerow(row)

    convergence_csv = results_dir / "ga_convergence.csv"
    with convergence_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["generation", "best_fitness", "best_params"])
        writer.writeheader()
        for row in standard.get("ga_history", []):
            writer.writerow({"generation": row["generation"], "best_fitness": row["best_fitness"], "best_params": json.dumps(row["best_params"])})

    summary_json = results_dir / "summary.json"
    summary_json.write_text(
        json.dumps(
            {
                "settings": standard["settings"],
                "seeds": standard["seeds"],
                "fitness_weights": standard["fitness_weights"],
                "ga_settings": standard["ga_settings"],
                "methods": entries,
                "ga_history": standard.get("ga_history", []),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"summary_csv": str(summary_csv), "summary_json": str(summary_json), "ga_convergence_csv": str(convergence_csv)}
