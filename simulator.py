import numpy as np


class EvacuationModel:
    def __init__(self, num_high, num_low, room_size=(20.0, 20.0), exit_pos=(10.0, 20.0), rng=None):
        self.num_agents = num_high + num_low
        self.room_size = np.array(room_size, dtype=float)
        self.exit_pos = np.array(exit_pos, dtype=float)
        self.rng = rng if rng is not None else np.random.default_rng()

        # Random starting positions in the lower half of the room.
        self.positions = self.rng.random((self.num_agents, 2)) * [self.room_size[0], self.room_size[1] / 2]
        self.velocities = np.zeros((self.num_agents, 2), dtype=float)

        # Agents have heterogenous traits: 1 for high mobility, 0 for low mobility.
        self.types = np.array([1] * num_high + [0] * num_low)
        self.max_speeds = np.where(self.types == 1, 1.5, 0.5)
        self.active = np.ones(self.num_agents, dtype=bool)

    def pair_wise_distances(self):
        """Return pairwise direction vectors and distances between active agents."""
        active_indices = np.where(self.active)[0]
        pos = self.positions[active_indices]

        diffs = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
        dists = np.linalg.norm(diffs, axis=2)
        np.fill_diagonal(dists, np.inf)
        return diffs, dists

    def count_near_collisions(self, threshold):
        if np.count_nonzero(self.active) < 2:
            return 0

        _, dists = self.pair_wise_distances()
        return int(np.count_nonzero(np.triu(dists < threshold, k=1)))

    def count_agents_near_exit(self, threshold):
        if not np.any(self.active):
            return 0

        pos = self.positions[self.active]
        dist_to_exit = np.linalg.norm(self.exit_pos - pos, axis=1)
        return int(np.count_nonzero(dist_to_exit < threshold))

    def snapshot(self, tick):
        return {
            "tick": int(tick),
            "positions": self.positions.tolist(),
            "active": self.active.astype(int).tolist(),
            "types": self.types.tolist(),
        }

    def step(self, params, dt=0.1):
        accel_factor, exit_threshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius = params

        active_mask = self.active
        if not np.any(active_mask):
            return False

        pos = self.positions[active_mask]
        vel = self.velocities[active_mask]
        max_speeds = self.max_speeds[active_mask]

        directions = self.exit_pos - pos
        distances = np.linalg.norm(directions, axis=1, keepdims=True)
        desired_direction = directions / (distances + 1e-6)

        desired_velocity = desired_direction * max_speeds[:, np.newaxis]
        acceleration = (desired_velocity - vel) * accel_factor

        diffs, dists = self.pair_wise_distances()
        in_range = dists < agent_radius
        repulsion_mag = agent_rep_weight / (dists**2 + 1e-6)
        repulsion_mag *= in_range
        force_vectors = (diffs / (dists[:, :, np.newaxis] + 1e-6)) * repulsion_mag[:, :, np.newaxis]
        agent_forces = np.sum(force_vectors, axis=1)

        wall_forces = np.zeros_like(pos)
        dist_left = pos[:, 0]
        dist_right = self.room_size[0] - pos[:, 0]
        dist_bottom = pos[:, 1]
        dist_top = self.room_size[1] - pos[:, 1]

        in_range_left = dist_left < wall_radius
        in_range_right = dist_right < wall_radius
        in_range_bottom = dist_bottom < wall_radius
        in_range_top = dist_top < wall_radius

        wall_forces[in_range_left, 0] += wall_rep_weight / (dist_left[in_range_left] ** 2 + 1e-6)
        wall_forces[in_range_right, 0] -= wall_rep_weight / (dist_right[in_range_right] ** 2 + 1e-6)
        wall_forces[in_range_bottom, 1] += wall_rep_weight / (dist_bottom[in_range_bottom] ** 2 + 1e-6)
        wall_forces[in_range_top, 1] -= wall_rep_weight / (dist_top[in_range_top] ** 2 + 1e-6)

        total_acceleration = acceleration + agent_forces + wall_forces
        vel += total_acceleration * dt

        speeds = np.linalg.norm(vel, axis=1)
        speed_factors = np.minimum(1.0, max_speeds / (speeds + 1e-6))
        vel *= speed_factors[:, np.newaxis]

        pos += vel * dt
        self.positions[active_mask] = pos
        self.velocities[active_mask] = vel

        dist_to_exit = np.linalg.norm(self.exit_pos - pos, axis=1)
        evacuated = dist_to_exit < exit_threshold
        global_active_index = np.nonzero(active_mask)[0]
        self.active[global_active_index[evacuated]] = False
        return True


def _group_mean(values, mask):
    group_values = values[mask]
    valid_values = group_values[~np.isnan(group_values)]
    if valid_values.size == 0:
        return None
    return float(np.mean(valid_values))


def run_simulation(
    params,
    num_high=30,
    num_low=10,
    room_size=(20.0, 20.0),
    exit_pos=(10.0, 20.0),
    max_ticks=500,
    dt=0.1,
    seed=None,
    frame_stride=4,
    near_collision_distance=0.35,
    congestion_radius=1.5,
    capture_frames=True,
):
    rng = np.random.default_rng(seed)
    model = EvacuationModel(
        num_high=num_high,
        num_low=num_low,
        room_size=room_size,
        exit_pos=exit_pos,
        rng=rng,
    )

    evacuation_ticks = np.full(model.num_agents, np.nan)
    frames = [model.snapshot(0)] if capture_frames else []
    ticks = 0
    near_collision_total = 0
    congestion_total = 0
    congestion_peak = 0

    while np.any(model.active) and ticks < max_ticks:
        was_active = model.active.copy()
        model.step(params, dt=dt)
        ticks += 1

        just_evacuated = was_active & ~model.active
        evacuation_ticks[just_evacuated] = ticks

        near_collision_total += model.count_near_collisions(near_collision_distance)
        current_congestion = model.count_agents_near_exit(congestion_radius)
        congestion_total += current_congestion
        congestion_peak = max(congestion_peak, current_congestion)

        if capture_frames and (ticks % frame_stride == 0 or not np.any(model.active) or ticks == max_ticks):
            frames.append(model.snapshot(ticks))

    high_mask = model.types == 1
    low_mask = model.types == 0
    mean_high_ticks = _group_mean(evacuation_ticks, high_mask)
    mean_low_ticks = _group_mean(evacuation_ticks, low_mask)

    fairness_gap_ticks = None
    if mean_high_ticks is not None and mean_low_ticks is not None:
        fairness_gap_ticks = abs(mean_high_ticks - mean_low_ticks)

    completed_runs = max(1, ticks)
    return {
        "params": [float(value) for value in params],
        "ticks": int(ticks),
        "total_time": float(ticks * dt),
        "all_evacuated": bool(not np.any(model.active)),
        "evacuated_agents": int(np.count_nonzero(~model.active)),
        "remaining_agents": int(np.count_nonzero(model.active)),
        "near_collisions": int(near_collision_total),
        "mean_congestion": float(congestion_total / completed_runs),
        "peak_congestion": int(congestion_peak),
        "mean_high_ticks": mean_high_ticks,
        "mean_low_ticks": mean_low_ticks,
        "mean_high_time": None if mean_high_ticks is None else float(mean_high_ticks * dt),
        "mean_low_time": None if mean_low_ticks is None else float(mean_low_ticks * dt),
        "fairness_gap_ticks": fairness_gap_ticks,
        "fairness_gap_time": None if fairness_gap_ticks is None else float(fairness_gap_ticks * dt),
        "frames": frames,
        "room_size": [float(room_size[0]), float(room_size[1])],
        "exit_pos": [float(exit_pos[0]), float(exit_pos[1])],
    }
        
