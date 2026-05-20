import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from crowd_evac.config import DEFAULT_GA_SEED_VECTOR, DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, LAYOUTS, sim_kwargs_from_layout
from crowd_evac.ga import evaluate_candidate, merge_active_to_full
from crowd_evac.simulator import run_simulation


def test_ga_merge_matches_default():
    full = merge_active_to_full(DEFAULT_GA_SEED_VECTOR).tolist()
    assert full == DEFAULT_PARAMS
    a = evaluate_candidate(DEFAULT_PARAMS, seeds=[11], log_path=None)
    b = evaluate_candidate(full, seeds=[11], log_path=None)
    assert abs(a["fitness"] - b["fitness"]) < 1e-9
    assert abs(a["total_time"] - b["total_time"]) < 1e-9


def test_simulation(layout_name=None, num_high=None, num_low=None, max_ticks=5000):
    layout_name = layout_name or DEFAULT_SIMULATION_SETTINGS["layout"]
    layout = LAYOUTS[layout_name]
    start_time = time.time()
    result = run_simulation(
        params=DEFAULT_PARAMS,
        num_high=num_high or DEFAULT_SIMULATION_SETTINGS["num_high"],
        num_low=num_low or DEFAULT_SIMULATION_SETTINGS["num_low"],
        max_ticks=max_ticks,
        dt=DEFAULT_SIMULATION_SETTINGS["dt"],
        seed=DEFAULT_SIMULATION_SETTINGS["seed"],
        **sim_kwargs_from_layout(layout),
    )
    print(
        f"layout={layout_name} all_evacuated={result['all_evacuated']} "
        f"ticks={result['ticks']} remaining={result['remaining_agents']} "
        f"near_collisions={result['near_collisions']} time={time.time() - start_time:.4f}s"
    )
    assert result["remaining_agents"] == 0, f"{layout_name} failed to evacuate all agents"


if __name__ == "__main__":
    test_ga_merge_matches_default()
    test_simulation()
    test_simulation(layout_name="hospital_corridor", num_high=40, num_low=15, max_ticks=5000)
    print("Smoke tests passed.")
