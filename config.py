# Layout 1: The standard baseline room
LAYOUT_STANDARD = {
    "room_size": (5.0, 5.0),
    "exit_pos": (5.0, 1.0),
    "exit_width": 0.2 
}

# Layout 2: A wide, narrow hallway
LAYOUT_CORRIDOR = {
    "room_size": (30.0, 10.0),
    "exit_pos": (30.0, 5.0)
}

# Layout 3: A large hall with an asymmetric exit
LAYOUT_ASYMMETRIC = {
    "room_size": (30.0, 30.0),
    "exit_pos": (5.0, 30.0)
}

# Default GA bounds for the parameters:
# [accel_factor, exit_threshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius]
PARAM_BOUNDS = [
    (0.1, 5.0),   # accel_factor
    (0.5, 2.0),   # exit_threshold
    (0.1, 5.0),   # agent_rep_weight
    (0.5, 3.0),   # agent_radius
    (0.1, 5.0),   # wall_rep_weight
    (0.5, 2.0)    # wall_radius
]