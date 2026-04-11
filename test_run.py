import numpy as np
import time
from simulator import EvacuationModel

def test_simulation():
    print("Initializing EvacuationModel...")
    # Setup: 30 high-mobility and 10 low-mobility agents
    model = EvacuationModel(num_high=30, num_low=10, room_size=(20.0, 20.0), exit_pos=(10.0, 20.0))
    
    # Define test parameters matching the step() unpack order:
    # [accel_factor, exit_threshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius]
    test_params = [2.0, 1.0, 0.5, 2.0, 0.5, 1.0]
    
    max_ticks = 5000
    ticks = 0
    
    print("Starting simulation loop...")
    start_time = time.time()
    
    # Run until all agents are inactive OR we hit the safety limit
    while np.any(model.active) and ticks < max_ticks:
        model.step(test_params, dt=0.1)
        ticks += 1
        
    compute_time = time.time() - start_time
    
    # Output results
    print("-" * 30)
    if ticks >= max_ticks:
        print(f"WARNING: Simulation reached max_ticks ({max_ticks}). Agents are likely stuck.")
    else:
        print(f"SUCCESS: All agents evacuated in {ticks} ticks.")
        
    print(f"Agents remaining: {np.sum(model.active)}")
    print(f"Computation time: {compute_time:.4f} seconds")
    print("-" * 30)

if __name__ == "__main__":
    test_simulation()