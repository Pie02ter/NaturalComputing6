import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.io import best_summary_to_entries, load_best_runs
from crowd_evac.visualization.animations import make_standard_animations


def main():
    parser = argparse.ArgumentParser(description="Regenerate standardized animations from best_runs.json.")
    parser.add_argument("results_dir", help="Experiment results directory.")
    parser.add_argument("--seed", type=int, default=11, help="Replay seed.")
    parser.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Animation format.")
    parser.add_argument("--fps", type=int, default=12, help="Frames per second.")
    args = parser.parse_args()

    _, standard = load_best_runs(args.results_dir)
    entries = best_summary_to_entries(standard)
    outputs = make_standard_animations(entries, standard["settings"], args.results_dir, seed=args.seed, output_format=args.format, fps=args.fps)
    print("Animations complete.")
    print(outputs)


if __name__ == "__main__":
    main()
