import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.io import best_summary_to_entries, load_best_runs, write_standard_summary
from crowd_evac.visualization.plots import make_standard_plots


def main():
    parser = argparse.ArgumentParser(description="Regenerate standardized plots from best_runs.json.")
    parser.add_argument("results_dir", help="Experiment results directory.")
    args = parser.parse_args()

    _, standard = load_best_runs(args.results_dir)
    entries = best_summary_to_entries(standard)
    write_standard_summary(args.results_dir, standard, entries)
    outputs = make_standard_plots(entries, standard.get("ga_history", []), args.results_dir)
    print("Plots complete.")
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
