# Simplified hospital-corridor experiment configuration used in the paper.

HOSPITAL_DEFAULT_PARAMS = [2.0, 1.5, 1.0, 0.5, 1.0]

LAYOUT_HOSPITAL_CORRIDOR = {
    "room_size": (24.0, 16.8),
    "agent_body_radius": 0.35,
    "near_collision_distance": 0.75,
    "default_params": HOSPITAL_DEFAULT_PARAMS,
    "recommended_settings": {
        "num_high": 28,
        "num_low": 12,
        "max_ticks": 1000,
    },
    "exits": [
        {"pos": (0.0, 8.4), "width": 1.4, "side": "left"},
        {"pos": (24.0, 8.4), "width": 1.4, "side": "right"},
    ],
    "internal_walls": [
        ((0.0, 10.8), (1.9, 10.8)),
        ((2.9, 10.8), (6.7, 10.8)),
        ((7.7, 10.8), (11.5, 10.8)),
        ((12.5, 10.8), (16.3, 10.8)),
        ((17.3, 10.8), (21.1, 10.8)),
        ((22.1, 10.8), (24.0, 10.8)),
        ((0.0, 6.0), (1.9, 6.0)),
        ((2.9, 6.0), (6.7, 6.0)),
        ((7.7, 6.0), (11.5, 6.0)),
        ((12.5, 6.0), (16.3, 6.0)),
        ((17.3, 6.0), (21.1, 6.0)),
        ((22.1, 6.0), (24.0, 6.0)),
        ((4.8, 10.8), (4.8, 16.8)),
        ((9.6, 10.8), (9.6, 16.8)),
        ((14.4, 10.8), (14.4, 16.8)),
        ((19.2, 10.8), (19.2, 16.8)),
        ((4.8, 0.0), (4.8, 6.0)),
        ((9.6, 0.0), (9.6, 6.0)),
        ((14.4, 0.0), (14.4, 6.0)),
        ((19.2, 0.0), (19.2, 6.0)),
    ],
    "spawn_zones": [
        {"rect": (0.7, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 0},
        {"rect": (5.5, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 1},
        {"rect": (10.3, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 1},
        {"rect": (15.1, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 2},
        {"rect": (19.9, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 2},
        {"rect": (0.7, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 0},
        {"rect": (5.5, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (10.3, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (15.1, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (19.9, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
    ],
    "navigation_nodes": [
        (2.4, 14.2), (7.2, 14.2), (12.0, 14.2), (16.8, 14.2), (21.6, 14.2),
        (2.4, 2.6), (7.2, 2.6), (12.0, 2.6), (16.8, 2.6), (21.6, 2.6),
        (2.4, 10.0), (7.2, 10.0), (12.0, 10.0), (16.8, 10.0), (21.6, 10.0),
        (2.4, 6.8), (7.2, 6.8), (12.0, 6.8), (16.8, 6.8), (21.6, 6.8),
        (2.4, 8.4), (7.2, 8.4), (12.0, 8.4), (16.8, 8.4), (21.6, 8.4),
        (0.4, 8.4), (23.6, 8.4),
    ],
    "navigation_edges": [
        (0, 10), (1, 11), (2, 12), (3, 13), (4, 14),
        (5, 15), (6, 16), (7, 17), (8, 18), (9, 19),
        (10, 20), (11, 21), (12, 22), (13, 23), (14, 24),
        (15, 20), (16, 21), (17, 22), (18, 23), (19, 24),
        (20, 21), (21, 22), (22, 23), (23, 24),
        (20, 25), (24, 26),
    ],
}

LAYOUTS = {"hospital_corridor": LAYOUT_HOSPITAL_CORRIDOR}


def sim_kwargs_from_layout(layout):
    kwargs = {"room_size": layout["room_size"]}
    if "exits" in layout:
        kwargs["exits"] = layout["exits"]
    else:
        kwargs["exit_pos"] = layout["exit_pos"]
        kwargs["exit_width"] = layout["exit_width"]
    for key in (
        "internal_walls",
        "spawn_zones",
        "agent_body_radius",
        "near_collision_distance",
        "navigation_nodes",
        "navigation_edges",
    ):
        if key in layout:
            kwargs[key] = layout[key]
    return kwargs


PARAM_NAMES = [
    "accel_factor",
    "agent_rep_weight",
    "agent_radius",
    "wall_rep_weight",
    "wall_radius",
]

DEFAULT_PARAMS = HOSPITAL_DEFAULT_PARAMS

# The GA optimizes interpersonal movement parameters only; wall parameters are
# fixed to the values used for all hospital-corridor experiments in the paper.
FIXED_WALL_REP_WEIGHT = HOSPITAL_DEFAULT_PARAMS[3]
FIXED_WALL_RADIUS = HOSPITAL_DEFAULT_PARAMS[4]

DEFAULT_SIMULATION_SETTINGS = {
    "layout": "hospital_corridor",
    "num_high": 28,
    "num_low": 12,
    "max_ticks": 1000,
    "dt": 0.1,
    "frame_stride": 4,
    "seed": 42,
}

DEFAULT_EVALUATION_SEEDS = [11, 29, 47, 53, 61, 73, 89, 97, 101, 109]

DEFAULT_FITNESS_WEIGHTS = {
    "time": 1.0,
    "collisions": 0.05,
    "congestion": 1.0,
    "fairness": 2.0,
    "incomplete_base": 1000.0,
    "incomplete_agent": 10.0,
}

GA_DEFAULTS = {
    "population_size": 24,
    "generations": 25,
    "elite_count": 2,
    "tournament_size": 3,
    "crossover_probability": 0.9,
    "mutation_probability": 0.2,
    "mutation_sigma_scale": 0.1,
}

PARAM_BOUNDS = [
    (0.1, 5.0),  # accel_factor
    (0.1, 5.0),  # agent_rep_weight
    (0.5, 3.0),  # agent_radius
    (0.1, 5.0),  # wall_rep_weight
    (0.5, 2.0),  # wall_radius
]

GA_ACTIVE_INDICES = (0, 1, 2)
GA_PARAM_NAMES = [PARAM_NAMES[i] for i in GA_ACTIVE_INDICES]
GA_PARAM_BOUNDS = [PARAM_BOUNDS[i] for i in GA_ACTIVE_INDICES]
DEFAULT_GA_SEED_VECTOR = [DEFAULT_PARAMS[i] for i in GA_ACTIVE_INDICES]
