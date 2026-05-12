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

LAYOUTS = {
    "standard": LAYOUT_STANDARD,
    "corridor": LAYOUT_CORRIDOR,
    "asymmetric": LAYOUT_ASYMMETRIC,
}

PARAM_NAMES = [
    "accel_factor",
    "agent_rep_weight",
    "agent_radius",
    "wall_rep_weight",
    "wall_radius",
]

DEFAULT_PARAMS = [2.0, 0.5, 2.0, 0.5, 1.0]

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
