import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from ..config import DEFAULT_SIMULATION_SETTINGS, LAYOUTS
from ..simulator import run_simulation
from .styles import method_label


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


def run_replay(entry, settings, seed):
    settings = dict(DEFAULT_SIMULATION_SETTINGS, **settings)
    layout = LAYOUTS[settings["layout"]]
    result = run_simulation(
        params=entry["params"],
        num_high=int(settings["num_high"]),
        num_low=int(settings["num_low"]),
        room_size=layout["room_size"],
        exit_pos=layout["exit_pos"],
        exit_width=layout["exit_width"],
        max_ticks=int(settings["max_ticks"]),
        dt=float(settings["dt"]),
        seed=int(seed),
        frame_stride=int(settings.get("frame_stride", DEFAULT_SIMULATION_SETTINGS["frame_stride"])),
        capture_frames=True,
    )
    result["method"] = entry["method"]
    result["label"] = entry.get("label", method_label(entry["method"]))
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
    if np.any(high_mask):
        ax.scatter(positions[high_mask, 0], positions[high_mask, 1], c="#2563eb", s=24, label="High", edgecolors="white", linewidths=0.3)
    if np.any(low_mask):
        ax.scatter(positions[low_mask, 0], positions[low_mask, 1], c="#dc2626", s=24, label="Low", edgecolors="white", linewidths=0.3)
    if np.any(high_mask) or np.any(low_mask):
        ax.legend(loc="upper left", fontsize=7, framealpha=0.9)


def _writer(output_format, fps):
    if output_format == "gif":
        return animation.PillowWriter(fps=fps)
    if output_format == "mp4":
        return animation.FFMpegWriter(fps=fps)
    raise ValueError(f"Unsupported animation format '{output_format}'")


def save_individual_animation(result, output_dir, output_format="gif", fps=12):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result['method']}.{output_format}"
    fig, ax = plt.subplots(figsize=(5.2, 5.5))
    frames = result["frames"]

    def update(index):
        _draw_frame(ax, result, frames[index])
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    anim.save(str(path), writer=_writer(output_format, fps))
    plt.close(fig)
    return str(path)


def save_side_by_side_animation(results, output_dir, output_format="gif", fps=12):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"method_comparison.{output_format}"
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
    anim.save(str(path), writer=_writer(output_format, fps))
    plt.close(fig)
    return str(path)


def make_standard_animations(entries, settings, results_dir, seed=11, output_format="gif", fps=12):
    output_dir = Path(results_dir) / "animations"
    replays = [run_replay(entry, settings, seed) for entry in entries]
    individual = {result["method"]: save_individual_animation(result, output_dir, output_format, fps) for result in replays}
    side_by_side = save_side_by_side_animation(replays, output_dir, output_format, fps)
    return {"individual": individual, "side_by_side": side_by_side}
