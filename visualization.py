import numpy as np
import matplotlib.pyplot as plt
from simulator import EvacuationModel
import matplotlib.animation as animation
from config import LAYOUT_STANDARD, LAYOUT_CORRIDOR
import os

def animate_simulation(params, num_high=30, num_low=10, max_ticks=500, filename="evacuation.mp4"):

    # Initialize model
    model = EvacuationModel(
        num_high=num_high, 
        num_low=num_low, 
        room_size=LAYOUT_STANDARD["room_size"], 
        exit_pos=LAYOUT_STANDARD["exit_pos"]
    )

    # Setup figure and axis
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, LAYOUT_STANDARD["room_size"][0])
    ax.set_ylim(0, LAYOUT_STANDARD["room_size"][1])
    ax.set_aspect('equal')
    ax.set_title("Evacuation Simulation")

    # Exit of the figure
    exit_marker = plt.Circle(LAYOUT_STANDARD["exit_pos"], LAYOUT_STANDARD["exit_width"] / 2, color='green', alpha=0.5)
    ax.add_patch(exit_marker)

    #  Scatter plot for the two groups
    scatter_high = ax.scatter([], [], c='blue', label='High Mobility', s=20)
    scatter_low = ax.scatter([], [], c='red', label='Low Mobility', s=20)
    ax.legend()

    def init():
        # emty 2D array to initialize the scatter plot
        empty_data = np.array([[np.nan, np.nan]])
        scatter_high.set_offsets(empty_data)
        scatter_low.set_offsets(empty_data)
        return scatter_high, scatter_low
    
    def update(frame):
        # Run one step of the simulation
        model.step(params, dt=0.1)

        # Empty data fallback
        empty_data = np.array([[np.nan, np.nan]])

        # If simulation is done, return current state
        if not np.any(model.active):
            return scatter_high, scatter_low
        
        # Filter positins by mbility type and active status
        current_pos = model.positions
        active_mask = model.active

        # Types: 1 for high mobility, 0 for low mobility
        high_mask = active_mask & (model.types == 1)
        low_mask = active_mask & (model.types == 0)

        # Update scatter data
        if np.any(high_mask):
            scatter_high.set_offsets(current_pos[high_mask])
        else:
            scatter_high.set_offsets(np.empty((0, 2)))
        
        if np.any(low_mask):
            scatter_low.set_offsets(current_pos[low_mask])
        else:
            scatter_low.set_offsets(np.empty((0, 2)))
        
        return scatter_high, scatter_low

    # Create animation
    anim = animation.FuncAnimation(fig, update, init_func=init, frames=max_ticks, blit=True)
    anim.save(filename, writer='pillow', fps=30)
    plt.close(fig)

if __name__ == "__main__":
    # Same test parameters as before:
    # [accel_factor, exit_threshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius]
    test_params = [2.0, 1.0, 2.0, 3.0, 0.5, 1.0]
    
    # Create an absolute path in your current folder
    save_path = os.path.abspath("test_evacuation.gif")

    # Save as GIF first, as it requires no extra system dependencies
    animate_simulation(test_params, filename="test_evacuation.gif")
    # Verify if it actually created the file
    if os.path.exists(save_path):
        print("SUCCESS")
    else:
        print("ERROR: Matplotlib finished, but the file was not created. Writer issue.")