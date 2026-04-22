# Layout 1: The standard baseline room
LAYOUT_STANDARD = {
    "room_size": (5.0, 5.0),
    "exit_pos": (5.0, 1.0),
    "exit_width": 0.2,
}

# Layout 2: A wide, narrow hallway
LAYOUT_CORRIDOR = {
    "room_size": (30.0, 10.0),
    "exit_pos": (30.0, 5.0),
    "exit_width": 0.4,
}

# Layout 3: A large hall with an asymmetric exit
LAYOUT_ASYMMETRIC = {
    "room_size": (30.0, 30.0),
    "exit_pos": (5.0, 30.0),
    "exit_width": 0.5,
}

LAYOUTS = {
    "standard": LAYOUT_STANDARD,
    "corridor": LAYOUT_CORRIDOR,
    "asymmetric": LAYOUT_ASYMMETRIC,
}

PARAM_NAMES = [
    "accel_factor",
    "exit_threshold",
    "agent_rep_weight",
    "agent_radius",
    "wall_rep_weight",
    "wall_radius",
]

DEFAULT_PARAMS = [2.0, 1.0, 0.5, 2.0, 0.5, 1.0]

DEFAULT_SIMULATION_SETTINGS = {
    "layout": "standard",
    "num_high": 30,
    "num_low": 10,
    "max_ticks": 500,
    "dt": 0.1,
    "frame_stride": 4,
    "seed": 42,
}

DEFAULT_EVALUATION_SEEDS = [11, 29, 47]

GA_DEFAULTS = {
    "population_size": 24,
    "generations": 25,
    "elite_count": 2,
    "tournament_size": 3,
    "crossover_probability": 0.9,
    "mutation_probability": 0.2,
    "mutation_sigma_scale": 0.1,
}

HEURISTIC_PARAM_SETS = {
    "heuristic_1": [1.8, 0.9, 1.2, 2.2, 0.7, 1.0],
    "heuristic_2": [2.4, 1.1, 0.9, 1.6, 0.9, 1.2],
}

# Default GA bounds for the parameters:
# [accel_factor, exit_threshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius]
PARAM_BOUNDS = [
    (0.1, 5.0),  # accel_factor
    (0.5, 2.0),  # exit_threshold
    (0.1, 5.0),  # agent_rep_weight
    (0.5, 3.0),  # agent_radius
    (0.1, 5.0),  # wall_rep_weight
    (0.5, 2.0),  # wall_radius
]
