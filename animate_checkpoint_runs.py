import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from checkpoint_pipeline import CHECKPOINT_RESULTS_DIR, CHECKPOINT_SETTINGS
from config import LAYOUTS
from simulator import run_simulation


METHOD_LABELS = {
    "fixed_default": "Fixed default",
    "random_search": "Random search",
    "ga_no_fairness": "GA no fairness",
    "ga_fairness": "GA fairness",
}


def _method_label(method):
    return METHOD_LABELS.get(method, method)


def _infer_exit_side(result):
    room_width, room_height = result["room_size"]
    exit_x, exit_y = result["exit_pos"]
    distances = {
        "left": abs(exit_x),
        "right": abs(room_width - exit_x),
        "bottom": abs(exit_y),
        "top": abs(room_height - exit_y),
    }
    return min(distances, key=distances.get)


def _draw_room_with_door(ax, result):
    room_width, room_height = result["room_size"]
    exit_x, exit_y = result["exit_pos"]
    exit_width = result["exit_width"]
    half_width = exit_width * 0.5
    exit_side = result.get("exit_side") or _infer_exit_side(result)

    def wall(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="#334155", linewidth=1.5)

    def door(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="#16a34a", linewidth=4, solid_capstyle="round")

    if exit_side == "right":
        door_start = max(0.0, exit_y - half_width)
        door_end = min(room_height, exit_y + half_width)
        wall(0, 0, room_width, 0)
        wall(0, room_height, room_width, room_height)
        wall(0, 0, 0, room_height)
        wall(room_width, 0, room_width, door_start)
        wall(room_width, door_end, room_width, room_height)
        door(room_width, door_start, room_width, door_end)
    elif exit_side == "left":
        door_start = max(0.0, exit_y - half_width)
        door_end = min(room_height, exit_y + half_width)
        wall(0, 0, room_width, 0)
        wall(0, room_height, room_width, room_height)
        wall(room_width, 0, room_width, room_height)
        wall(0, 0, 0, door_start)
        wall(0, door_end, 0, room_height)
        door(0, door_start, 0, door_end)
    elif exit_side == "top":
        door_start = max(0.0, exit_x - half_width)
        door_end = min(room_width, exit_x + half_width)
        wall(0, 0, room_width, 0)
        wall(0, 0, 0, room_height)
        wall(room_width, 0, room_width, room_height)
        wall(0, room_height, door_start, room_height)
        wall(door_end, room_height, room_width, room_height)
        door(door_start, room_height, door_end, room_height)
    else:
        door_start = max(0.0, exit_x - half_width)
        door_end = min(room_width, exit_x + half_width)
        wall(0, room_height, room_width, room_height)
        wall(0, 0, 0, room_height)
        wall(room_width, 0, room_width, room_height)
        wall(0, 0, door_start, 0)
        wall(door_end, 0, room_width, 0)
        door(door_start, 0, door_end, 0)


def _load_checkpoint_methods(results_path):
    summary_json = results_path / "checkpoint_summary.json"
    if summary_json.exists():
        payload = json.loads(summary_json.read_text(encoding="utf-8"))
        return payload.get("settings", CHECKPOINT_SETTINGS), payload["methods"]

    summary_csv = results_path / "checkpoint_summary.csv"
    if not summary_csv.exists():
        raise FileNotFoundError(f"Missing checkpoint summary at {summary_csv}. Run run_checkpoint_experiment.py first.")

    methods = []
    with summary_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entry = dict(row)
            entry["best_params"] = json.loads(row["best_params"])
            for key in ["fitness", "total_time", "fairness_gap_time", "mean_congestion", "near_collisions", "remaining_agents"]:
                entry[key] = None if row[key] == "" else float(row[key])
            methods.append(entry)
    return CHECKPOINT_SETTINGS, methods


def _run_replay(method_entry, settings, seed):
    layout_name = settings["layout"]
    if layout_name not in LAYOUTS:
        raise ValueError(f"Unknown layout '{layout_name}'")

    layout = LAYOUTS[layout_name]
    result = run_simulation(
        params=method_entry["best_params"],
        num_high=int(settings["num_high"]),
        num_low=int(settings["num_low"]),
        room_size=layout["room_size"],
        exit_pos=layout["exit_pos"],
        exit_width=layout["exit_width"],
        max_ticks=int(settings["max_ticks"]),
        dt=float(settings["dt"]),
        seed=int(seed),
        frame_stride=int(settings.get("frame_stride", CHECKPOINT_SETTINGS["frame_stride"])),
        capture_frames=True,
    )
    result["method"] = method_entry["method"]
    result["label"] = _method_label(method_entry["method"])
    result["exit_width"] = layout["exit_width"]
    result["visualization_seed"] = int(seed)
    return result


def _draw_frame(ax, result, frame):
    positions = np.array(frame["positions"], dtype=float)
    active = np.array(frame["active"], dtype=bool)
    types = np.array(frame["types"], dtype=int)
    room_width, room_height = result["room_size"]
    tick = int(frame["tick"])
    time_value = tick * float(result.get("dt", 0.1))
    remaining = int(np.count_nonzero(active))
    fairness_gap = result["fairness_gap_time"]
    fairness_text = "-" if fairness_gap is None else f"{fairness_gap:.2f}s"

    ax.clear()
    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_height)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#f8fafc")
    ax.set_title(
        f"{result['label']}\nseed {result['visualization_seed']} | t={time_value:.1f}s | remaining={remaining}\nrun T={result['total_time']:.2f}s | G={fairness_text}",
        fontsize=9,
    )

    _draw_room_with_door(ax, result)

    high_mask = active & (types == 1)
    low_mask = active & (types == 0)
    has_visible_agents = False
    if np.any(high_mask):
        ax.scatter(positions[high_mask, 0], positions[high_mask, 1], c="#2563eb", s=24, label="High", edgecolors="white", linewidths=0.3)
        has_visible_agents = True
    if np.any(low_mask):
        ax.scatter(positions[low_mask, 0], positions[low_mask, 1], c="#dc2626", s=24, label="Low", edgecolors="white", linewidths=0.3)
        has_visible_agents = True
    if has_visible_agents:
        ax.legend(loc="upper left", fontsize=7, framealpha=0.9)


def _animation_writer(output_format, fps):
    if output_format == "gif":
        return animation.PillowWriter(fps=fps)
    if output_format == "mp4":
        return animation.FFMpegWriter(fps=fps)
    raise ValueError(f"Unsupported animation format '{output_format}'")


def _save_animation(anim, fig, path, output_format, fps):
    path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(str(path), writer=_animation_writer(output_format, fps))
    plt.close(fig)


def _animation_path(output_dir, name, output_format):
    return output_dir / f"{name}.{output_format}"


def save_individual_animation(result, output_dir, output_format="gif", fps=12):
    path = _animation_path(output_dir, result["method"], output_format)
    fig, ax = plt.subplots(figsize=(5.2, 5.5))
    frames = result["frames"]

    def update(index):
        _draw_frame(ax, result, frames[index])
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    _save_animation(anim, fig, path, output_format, fps)
    return path


def save_side_by_side_animation(results, output_dir, output_format="gif", fps=12):
    path = _animation_path(output_dir, "checkpoint_comparison", output_format)
    columns = 2
    rows = math.ceil(len(results) / columns)
    fig, axes = plt.subplots(rows, columns, figsize=(10.5, 5.4 * rows))
    axes = np.atleast_1d(axes).flatten()
    max_frames = max(len(result["frames"]) for result in results)

    def update(index):
        for ax, result in zip(axes, results):
            frame = result["frames"][min(index, len(result["frames"]) - 1)]
            _draw_frame(ax, result, frame)
        for ax in axes[len(results):]:
            ax.axis("off")
        return []

    anim = animation.FuncAnimation(fig, update, frames=max_frames, interval=1000 / fps, blit=False)
    _save_animation(anim, fig, path, output_format, fps)
    return path


def generate_checkpoint_animations(
    results_dir=CHECKPOINT_RESULTS_DIR,
    seed=0,
    output_format="gif",
    fps=12,
    make_individual=True,
    make_side_by_side=True,
):
    results_path = Path(results_dir)
    output_dir = results_path / "animations"
    settings, methods = _load_checkpoint_methods(results_path)
    replays = [_run_replay(method_entry, settings, seed) for method_entry in methods]

    individual_outputs = {}
    if make_individual:
        for replay in replays:
            path = save_individual_animation(replay, output_dir, output_format=output_format, fps=fps)
            individual_outputs[replay["method"]] = str(path)

    side_by_side_output = None
    if make_side_by_side:
        side_by_side_output = str(save_side_by_side_animation(replays, output_dir, output_format=output_format, fps=fps))

    return {
        "seed": int(seed),
        "format": output_format,
        "fps": int(fps),
        "individual": individual_outputs,
        "side_by_side": side_by_side_output,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate checkpoint replay animations from saved best parameters.")
    parser.add_argument("--results-dir", default=str(CHECKPOINT_RESULTS_DIR), help="Checkpoint results directory.")
    parser.add_argument("--seed", type=int, default=0, help="Visualization seed used for every method replay.")
    parser.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Animation output format.")
    parser.add_argument("--fps", type=int, default=12, help="Animation frames per second.")
    parser.add_argument("--no-individual", action="store_true", help="Skip one animation per method.")
    parser.add_argument("--no-side-by-side", action="store_true", help="Skip the 2x2 comparison animation.")
    args = parser.parse_args()

    outputs = generate_checkpoint_animations(
        results_dir=args.results_dir,
        seed=args.seed,
        output_format=args.format,
        fps=args.fps,
        make_individual=not args.no_individual,
        make_side_by_side=not args.no_side_by_side,
    )
    print("Checkpoint animations complete.")
    for method, path in outputs["individual"].items():
        print(f"{method}: {path}")
    if outputs["side_by_side"]:
        print(f"side_by_side: {outputs['side_by_side']}")


if __name__ == "__main__":
    main()
