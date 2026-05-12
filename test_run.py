import time

from config import DEFAULT_GA_SEED_VECTOR, DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, LAYOUTS
from ga import evaluate_candidate, merge_active_to_full
from simulator import run_simulation


def test_ga_merge_matches_default():
    full = merge_active_to_full(DEFAULT_GA_SEED_VECTOR).tolist()
    assert full == DEFAULT_PARAMS
    seeds = [11]
    a = evaluate_candidate(DEFAULT_PARAMS, seeds=seeds, log_path=None)
    b = evaluate_candidate(full, seeds=seeds, log_path=None)
    assert abs(a["fitness"] - b["fitness"]) < 1e-9
    assert abs(a["total_time"] - b["total_time"]) < 1e-9


def test_simulation():
    print("Initializing run_simulation...")
    layout = LAYOUTS[DEFAULT_SIMULATION_SETTINGS["layout"]]
    start_time = time.time()

    result = run_simulation(
        params=DEFAULT_PARAMS,
        num_high=DEFAULT_SIMULATION_SETTINGS["num_high"],
        num_low=DEFAULT_SIMULATION_SETTINGS["num_low"],
        room_size=layout["room_size"],
        exit_pos=layout["exit_pos"],
        exit_width=layout["exit_width"],
        max_ticks=5000,
        dt=DEFAULT_SIMULATION_SETTINGS["dt"],
        seed=DEFAULT_SIMULATION_SETTINGS["seed"],
    )

    compute_time = time.time() - start_time

    print("-" * 30)
    if not result["all_evacuated"]:
        print("WARNING: Simulation reached max_ticks. Agents are likely stuck.")
    else:
        print(f"SUCCESS: All agents evacuated in {result['ticks']} ticks.")

    print(f"Agents remaining: {result['remaining_agents']}")
    print(f"Near collisions: {result['near_collisions']}")
    print(f"Computation time: {compute_time:.4f} seconds")
    print("-" * 30)

if __name__ == "__main__":
    test_ga_merge_matches_default()
    print("GA merge / evaluate consistency: OK")
    test_simulation()
