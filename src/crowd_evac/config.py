# Layout 1: The standard baseline room
LAYOUT_STANDARD = {
    "room_size": (5.0, 5.0),
    "exit_pos": (5.0, 1.0),
    "exit_width": 0.6,
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

# Layout 4: Simplified hospital corridor network inspired by a floor evacuation plan.
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
        # Top-room to corridor wall (deeper rooms, narrower corridor)
        ((0.0, 10.8), (1.9, 10.8)),
        ((2.9, 10.8), (6.7, 10.8)),
        ((7.7, 10.8), (11.5, 10.8)),
        ((12.5, 10.8), (16.3, 10.8)),
        ((17.3, 10.8), (21.1, 10.8)),
        ((22.1, 10.8), (24.0, 10.8)),
        # Bottom-room to corridor wall
        ((0.0, 6.0), (1.9, 6.0)),
        ((2.9, 6.0), (6.7, 6.0)),
        ((7.7, 6.0), (11.5, 6.0)),
        ((12.5, 6.0), (16.3, 6.0)),
        ((17.3, 6.0), (21.1, 6.0)),
        ((22.1, 6.0), (24.0, 6.0)),
        # Room partition walls
        ((4.8, 10.8), (4.8, 16.8)),
        ((9.6, 10.8), (9.6, 16.8)),
        ((14.4, 10.8), (14.4, 16.8)),
        ((19.2, 10.8), (19.2, 16.8)),
        ((4.8, 0.0), (4.8, 6.0)),
        ((9.6, 0.0), (9.6, 6.0)),
        ((14.4, 0.0), (14.4, 6.0)),
        ((19.2, 0.0), (19.2, 6.0)),
        # Single large central corridor: no extra middle separator walls.
    ],
    "spawn_zones": [
        # Top rooms
        {"rect": (0.7, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 0},
        {"rect": (5.5, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 1},
        {"rect": (10.3, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 1},
        {"rect": (15.1, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 2},
        {"rect": (19.9, 11.2, 3.4, 5.1), "weight": 1.0, "exit_index": 2},
        # Bottom rooms
        {"rect": (0.7, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 0},
        {"rect": (5.5, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (10.3, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (15.1, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
        {"rect": (19.9, 0.5, 3.4, 5.1), "weight": 1.0, "exit_index": 3},
    ],
    "navigation_nodes": [
        # Room centers (top then bottom)
        (2.4, 14.2), (7.2, 14.2), (12.0, 14.2), (16.8, 14.2), (21.6, 14.2),
        (2.4, 2.6), (7.2, 2.6), (12.0, 2.6), (16.8, 2.6), (21.6, 2.6),
        # Doorway anchors (top then bottom)
        (2.4, 10.0), (7.2, 10.0), (12.0, 10.0), (16.8, 10.0), (21.6, 10.0),
        (2.4, 6.8), (7.2, 6.8), (12.0, 6.8), (16.8, 6.8), (21.6, 6.8),
        # Main corridor line
        (2.4, 8.4), (7.2, 8.4), (12.0, 8.4), (16.8, 8.4), (21.6, 8.4),
        # Exit anchors (left corridor end, right corridor end)
        (0.4, 8.4), (23.6, 8.4),
    ],
    "navigation_edges": [
        # Room center -> doorway
        (0, 10), (1, 11), (2, 12), (3, 13), (4, 14),
        (5, 15), (6, 16), (7, 17), (8, 18), (9, 19),
        # Doorway -> main corridor
        (10, 20), (11, 21), (12, 22), (13, 23), (14, 24),
        (15, 20), (16, 21), (17, 22), (18, 23), (19, 24),
        # Main corridor connectivity
        (20, 21), (21, 22), (22, 23), (23, 24),
        # Exit connectors
        (20, 25), (24, 26),
    ],
}

LAYOUTS = {
    "standard": LAYOUT_STANDARD,
    "corridor": LAYOUT_CORRIDOR,
    "asymmetric": LAYOUT_ASYMMETRIC,
    "hospital_corridor": LAYOUT_HOSPITAL_CORRIDOR,
}


def sim_kwargs_from_layout(layout):
    kwargs = {"room_size": layout["room_size"]}
    if "exits" in layout:
        kwargs["exits"] = layout["exits"]
    else:
        kwargs["exit_pos"] = layout["exit_pos"]
        kwargs["exit_width"] = layout["exit_width"]
    if "internal_walls" in layout:
        kwargs["internal_walls"] = layout["internal_walls"]
    if "spawn_zones" in layout:
        kwargs["spawn_zones"] = layout["spawn_zones"]
    if "agent_body_radius" in layout:
        kwargs["agent_body_radius"] = layout["agent_body_radius"]
    if "near_collision_distance" in layout:
        kwargs["near_collision_distance"] = layout["near_collision_distance"]
    if "navigation_nodes" in layout:
        kwargs["navigation_nodes"] = layout["navigation_nodes"]
    if "navigation_edges" in layout:
        kwargs["navigation_edges"] = layout["navigation_edges"]
    return kwargs


def layout_default_params(layout, fallback=None):
    return list(layout.get("default_params", fallback or DEFAULT_PARAMS))


def layout_payload(layout):
    payload = {
        "room_size": list(layout["room_size"]),
    }
    if "exits" in layout:
        payload["exits"] = [
            {
                "pos": list(exit_info["pos"]),
                "width": exit_info["width"],
                "side": exit_info.get("side"),
            }
            for exit_info in layout["exits"]
        ]
    else:
        payload["exit_pos"] = list(layout["exit_pos"])
        payload["exit_width"] = layout["exit_width"]
    if "internal_walls" in layout:
        payload["internal_walls"] = [
            [list(start), list(end)] for start, end in layout["internal_walls"]
        ]
    if "spawn_zones" in layout:
        payload["spawn_zones"] = [
            {
                "rect": list(zone["rect"]),
                "weight": zone.get("weight", 1.0),
                **({"exit_index": zone["exit_index"]} if "exit_index" in zone else {}),
            }
            for zone in layout["spawn_zones"]
        ]
    if "agent_body_radius" in layout:
        payload["agent_body_radius"] = layout["agent_body_radius"]
    if "near_collision_distance" in layout:
        payload["near_collision_distance"] = layout["near_collision_distance"]
    if "navigation_nodes" in layout:
        payload["navigation_nodes"] = [list(node) for node in layout["navigation_nodes"]]
    if "navigation_edges" in layout:
        payload["navigation_edges"] = [list(edge) for edge in layout["navigation_edges"]]
    if "default_params" in layout:
        payload["default_params"] = list(layout["default_params"])
    if "recommended_settings" in layout:
        payload["recommended_settings"] = dict(layout["recommended_settings"])
    return payload

PARAM_NAMES = [
    "accel_factor",
    "agent_rep_weight",
    "agent_radius",
    "wall_rep_weight",
    "wall_radius",
]

DEFAULT_PARAMS = [2.0, 0.5, 2.0, 0.5, 1.0]

# Wall repulsion held fixed during GA (research focuses on interpersonal avoidance + acceleration).
# Must stay aligned with DEFAULT_PARAMS[3] and DEFAULT_PARAMS[4].
FIXED_WALL_REP_WEIGHT = 0.5
FIXED_WALL_RADIUS = 1.0

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

HEURISTIC_PARAM_SETS = {
    "heuristic_1": [1.8, 1.2, 2.2, 0.7, 1.0],
    "heuristic_2": [2.4, 0.9, 1.6, 0.9, 1.2],
}

EXPERIMENT_PRESETS = {
    "standard_baseline": {
        "label": "Standard Baseline",
        "description": "Balanced baseline scenario for comparing default, heuristic, random search, and GA.",
        "suite": "standard",
        "settings": {
            "layout": "standard",
            "num_high": 30,
            "num_low": 10,
            "max_ticks": 500,
            "dt": 0.1,
            "seed": 42,
            "frame_stride": 4,
        },
        "evaluation_seeds": [11, 29, 47],
        "fitness_weights": DEFAULT_FITNESS_WEIGHTS,
        "ga_settings": {
            "population_size": 24,
            "generations": 25,
            "elite_count": 2,
            "tournament_size": 3,
            "crossover_probability": 0.9,
            "mutation_probability": 0.2,
            "mutation_sigma_scale": 0.1,
            "rng_seed": 123,
        },
        "random_candidates": 600,
    },
    "fairness_focus": {
        "label": "Fairness Focus",
        "description": "More balanced mobility groups with a stronger fairness penalty.",
        "suite": "standard",
        "settings": {
            "layout": "standard",
            "num_high": 20,
            "num_low": 20,
            "max_ticks": 600,
            "dt": 0.1,
            "seed": 42,
            "frame_stride": 4,
        },
        "evaluation_seeds": [11, 29, 47],
        "fitness_weights": {
            "time": 1.0,
            "collisions": 0.05,
            "congestion": 1.0,
            "fairness": 3.0,
            "incomplete_base": 1000.0,
            "incomplete_agent": 10.0,
        },
        "ga_settings": {
            "population_size": 24,
            "generations": 25,
            "elite_count": 2,
            "tournament_size": 3,
            "crossover_probability": 0.9,
            "mutation_probability": 0.2,
            "mutation_sigma_scale": 0.1,
            "rng_seed": 123,
        },
        "random_candidates": 600,
    },
    "generalization_sweep": {
        "label": "Generalization Sweep",
        "description": "Train on the standard scenario, then test across layouts and densities.",
        "suite": "generalization",
        "settings": {
            "layout": "standard",
            "num_high": 30,
            "num_low": 10,
            "max_ticks": 500,
            "dt": 0.1,
            "seed": 42,
            "frame_stride": 4,
        },
        "evaluation_seeds": [11, 29, 47],
        "fitness_weights": DEFAULT_FITNESS_WEIGHTS,
        "ga_settings": {
            "population_size": 24,
            "generations": 25,
            "elite_count": 2,
            "tournament_size": 3,
            "crossover_probability": 0.9,
            "mutation_probability": 0.2,
            "mutation_sigma_scale": 0.1,
            "rng_seed": 123,
        },
        "random_candidates": 600,
    },
}

# Default GA bounds for local movement-rule parameters:
# [accel_factor, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius]
PARAM_BOUNDS = [
    (0.1, 5.0),  # accel_factor
    (0.1, 5.0),  # agent_rep_weight
    (0.5, 3.0),  # agent_radius
    (0.1, 5.0),  # wall_rep_weight
    (0.5, 2.0),  # wall_radius
]

# GA genome: only indices 0–2 (bottleneck / crowd interaction); walls use FIXED_WALL_* above.
GA_ACTIVE_INDICES = (0, 1, 2)
GA_PARAM_NAMES = [PARAM_NAMES[i] for i in GA_ACTIVE_INDICES]
GA_PARAM_BOUNDS = [PARAM_BOUNDS[i] for i in GA_ACTIVE_INDICES]
DEFAULT_GA_SEED_VECTOR = [DEFAULT_PARAMS[i] for i in GA_ACTIVE_INDICES]
