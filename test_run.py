import time
from config import DEFAULT_PARAMS, DEFAULT_SIMULATION_SETTINGS, LAYOUTS
from simulator import run_simulation

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
    test_simulation()
