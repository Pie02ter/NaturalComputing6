#!/usr/bin/env python3
"""
One-at-a-time parameter sweeps at the project baseline configuration.

Compares how much total_time and fairness_gap_time move when varying wall
repulsion parameters versus accel / interpersonal avoidance. Use the printed
ranges to justify fixing wall_rep_weight and wall_radius in the 3D GA.
"""
import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.config import DEFAULT_EVALUATION_SEEDS, DEFAULT_PARAMS, PARAM_BOUNDS, PARAM_NAMES
from crowd_evac.ga import evaluate_candidate

BASELINE = np.array(DEFAULT_PARAMS, dtype=float)


def clip_params(vec):
    out = np.array(vec, dtype=float).copy()
    for i in range(5):
        lo, hi = PARAM_BOUNDS[i]
        out[i] = float(np.clip(out[i], lo, hi))
    return out.tolist()


def sweep_axis(axis_index, num_points, seeds):
    lo, hi = PARAM_BOUNDS[axis_index]
    values = np.linspace(lo, hi, num=num_points)
    rows = []
    for v in values:
        p = BASELINE.copy()
        p[axis_index] = v
        p = clip_params(p)
        ev = evaluate_candidate(params=p, seeds=seeds, log_path=None, cache=None)
        gap = ev["fairness_gap_time"]
        gap = float("nan") if gap is None else float(gap)
        rows.append((float(v), float(ev["total_time"]), gap))
    return rows


def summarize(param_name, rows):
    times = [r[1] for r in rows]
    gaps = [r[2] for r in rows if not np.isnan(r[2])]
    tr = max(times) - min(times)
    gr = (max(gaps) - min(gaps)) if gaps else float("nan")
    return {"param": param_name, "range_total_time": tr, "range_fairness_gap": gr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=11, help="Grid points per axis (inclusive).")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="Evaluation seeds (default: config default set).")
    args = parser.parse_args()
    seeds = list(args.seeds) if args.seeds else list(DEFAULT_EVALUATION_SEEDS)

    wall_axes = [(3, PARAM_NAMES[3]), (4, PARAM_NAMES[4])]
    primary_axes = [(0, PARAM_NAMES[0]), (1, PARAM_NAMES[1]), (2, PARAM_NAMES[2])]

    results = []
    for idx, name in wall_axes + primary_axes:
        rows = sweep_axis(idx, args.points, seeds)
        results.append(summarize(name, rows))

    print("OAT sensitivity (seeds=%s, points_per_axis=%s)" % (seeds, args.points))
    print("baseline params:", BASELINE.tolist())
    for r in results:
        print(
            "  {:<18}  Δtotal_time={:.4f}  Δfairness_gap={:.4f}".format(
                r["param"] + ":", r["range_total_time"], r["range_fairness_gap"]
            )
        )

    wall_dt = np.mean([results[i]["range_total_time"] for i in range(2)])
    primary_dt = np.mean([results[i]["range_total_time"] for i in range(2, 5)])
    wall_g = np.nanmean([results[i]["range_fairness_gap"] for i in range(2)])
    primary_g = np.nanmean([results[i]["range_fairness_gap"] for i in range(2, 5)])
    print("mean Δtotal_time — wall params: {:.4f}, primary params: {:.4f}".format(wall_dt, primary_dt))
    print("mean Δfairness_gap — wall params: {:.4f}, primary params: {:.4f}".format(wall_g, primary_g))


if __name__ == "__main__":
    main()
