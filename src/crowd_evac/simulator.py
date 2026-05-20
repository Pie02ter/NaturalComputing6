import numpy as np


def _normalize_exits(room_size, exit_pos=None, exit_width=None, exits=None):
    room_size = np.array(room_size, dtype=float)
    if exits is not None:
        normalized = []
        for entry in exits:
            pos = np.array(entry["pos"], dtype=float)
            width = float(entry["width"])
            side = entry.get("side")
            if side is None:
                side = _infer_exit_side_for_pos(room_size, pos)
            normalized.append({"pos": pos, "width": width, "side": side})
        return normalized

    if exit_pos is None:
        raise ValueError("Either exits or exit_pos must be provided.")
    pos = np.array(exit_pos, dtype=float)
    width = 0.2 if exit_width is None else float(exit_width)
    side = _infer_exit_side_for_pos(room_size, pos)
    return [{"pos": pos, "width": width, "side": side}]


def _infer_exit_side_for_pos(room_size, exit_pos):
    distances = {
        "left": abs(exit_pos[0]),
        "right": abs(room_size[0] - exit_pos[0]),
        "bottom": abs(exit_pos[1]),
        "top": abs(room_size[1] - exit_pos[1]),
    }
    return min(distances, key=distances.get)


def _normalize_internal_walls(internal_walls):
    if not internal_walls:
        return np.zeros((0, 2, 2), dtype=float)
    segments = []
    for segment in internal_walls:
        start = np.array(segment[0], dtype=float)
        end = np.array(segment[1], dtype=float)
        segments.append([start, end])
    return np.array(segments, dtype=float)


def _normalize_spawn_zones(spawn_zones):
    if not spawn_zones:
        return None
    normalized = []
    for zone in spawn_zones:
        rect = np.array(zone["rect"], dtype=float)
        weight = float(zone.get("weight", 1.0))
        exit_index = zone.get("exit_index")
        normalized.append({"rect": rect, "weight": weight, "exit_index": exit_index})
    return normalized


def _point_segment_vectors(pos, segments):
    """Return closest-point vectors from agents to each wall segment."""
    if segments.size == 0:
        return np.zeros((pos.shape[0], 0, 2), dtype=float), np.full((pos.shape[0], 0), np.inf)

    start = segments[:, 0, :]
    end = segments[:, 1, :]
    seg_vec = end - start
    seg_len_sq = np.sum(seg_vec**2, axis=1)
    seg_len_sq = np.where(seg_len_sq < 1e-9, 1e-9, seg_len_sq)

    rel = pos[:, np.newaxis, :] - start[np.newaxis, :, :]
    t = np.clip(np.sum(rel * seg_vec[np.newaxis, :, :], axis=2) / seg_len_sq[np.newaxis, :], 0.0, 1.0)
    closest = start[np.newaxis, :, :] + t[:, :, np.newaxis] * seg_vec[np.newaxis, :, :]
    delta = pos[:, np.newaxis, :] - closest
    dists = np.linalg.norm(delta, axis=2)
    return delta, dists


class EvacuationModel:
    def __init__(
        self,
        num_high,
        num_low,
        room_size=(20.0, 20.0),
        exit_pos=(10.0, 20.0),
        exit_width=0.2,
        exits=None,
        internal_walls=None,
        spawn_zones=None,
        agent_body_radius=0.0,
        rng=None,
    ):
        self.num_agents = num_high + num_low
        self.agent_body_radius = float(agent_body_radius)
        self.room_size = np.array(room_size, dtype=float)
        self.exits = _normalize_exits(self.room_size, exit_pos=exit_pos, exit_width=exit_width, exits=exits)
        self.exit_pos = self.exits[0]["pos"]
        self.exit_width = self.exits[0]["width"]
        self.exit_side = self.exits[0]["side"]
        self.internal_walls = _normalize_internal_walls(internal_walls)
        self.spawn_zones = _normalize_spawn_zones(spawn_zones)
        self.rng = rng if rng is not None else np.random.default_rng()

        self.positions, self.target_exit_indices = self._sample_initial_positions()
        self.velocities = np.zeros((self.num_agents, 2), dtype=float)

        self.types = np.array([1] * num_high + [0] * num_low)
        self.max_speeds = np.where(self.types == 1, 1.5, 0.5)
        self.active = np.ones(self.num_agents, dtype=bool)

    def _sample_initial_positions(self):
        if self.spawn_zones is None:
            positions = self.rng.random((self.num_agents, 2)) * [self.room_size[0], self.room_size[1] / 2]
            return positions, None

        weights = np.array([zone["weight"] for zone in self.spawn_zones], dtype=float)
        weights /= weights.sum()
        positions = np.zeros((self.num_agents, 2), dtype=float)
        target_exit_indices = np.zeros(self.num_agents, dtype=int)
        for index in range(self.num_agents):
            zone_index = int(self.rng.choice(len(self.spawn_zones), p=weights))
            zone = self.spawn_zones[zone_index]
            positions[index] = self._sample_spawn_point_in_zone(zone)
            exit_index = zone.get("exit_index")
            if exit_index is None:
                exit_index = int(
                    np.argmin(
                        np.linalg.norm(
                            np.array([exit_info["pos"] for exit_info in self.exits])[np.newaxis, :, :]
                            - positions[index][np.newaxis, np.newaxis, :],
                            axis=2,
                        )[0]
                    )
                )
            target_exit_indices[index] = int(exit_index)
        return positions, target_exit_indices

    def _sample_spawn_point_in_zone(self, zone, max_attempts=50):
        spawn_margin = max(0.25, self.agent_body_radius + 0.1)
        x, y, width, height = zone["rect"]
        for _ in range(max_attempts):
            point = np.array(
                [
                    x + self.rng.random() * width,
                    y + self.rng.random() * height,
                ],
                dtype=float,
            )
            if not self._point_too_close_to_internal_walls(point, spawn_margin):
                return point
        return np.array([x + width * 0.5, y + height * 0.5], dtype=float)

    def _point_too_close_to_internal_walls(self, point, threshold):
        if self.internal_walls.size == 0:
            return False
        _, dists = _point_segment_vectors(point[np.newaxis, :], self.internal_walls)
        return bool(np.any(dists[0] < threshold))

    def _door_mask_for_exit(self, pos, exit_info):
        half_width = exit_info["width"] * 0.5
        exit_pos = exit_info["pos"]
        side = exit_info["side"]
        if side in ("left", "right"):
            return np.abs(pos[:, 1] - exit_pos[1]) <= half_width
        return np.abs(pos[:, 0] - exit_pos[0]) <= half_width

    def _combined_door_mask(self, pos, side):
        mask = np.zeros(pos.shape[0], dtype=bool)
        for exit_info in self.exits:
            if exit_info["side"] == side:
                mask |= self._door_mask_for_exit(pos, exit_info)
        return mask

    def _evacuation_mask(self, pos, capture=0.2):
        evacuated = np.zeros(pos.shape[0], dtype=bool)
        for exit_info in self.exits:
            in_door = self._door_mask_for_exit(pos, exit_info)
            side = exit_info["side"]
            if side == "left":
                evacuated |= (pos[:, 0] <= capture) & in_door
            elif side == "right":
                evacuated |= (pos[:, 0] >= self.room_size[0] - capture) & in_door
            elif side == "bottom":
                evacuated |= (pos[:, 1] <= capture) & in_door
            else:
                evacuated |= (pos[:, 1] >= self.room_size[1] - capture) & in_door
        return evacuated

    def _target_positions(self, pos, active_mask):
        if self.target_exit_indices is None:
            return self._nearest_exit_targets(pos)

        exit_positions = np.array([exit_info["pos"] for exit_info in self.exits], dtype=float)
        active_exit_indices = self.target_exit_indices[active_mask]
        return exit_positions[active_exit_indices]

    def _nearest_exit_targets(self, pos):
        exit_positions = np.array([exit_info["pos"] for exit_info in self.exits], dtype=float)
        deltas = exit_positions[np.newaxis, :, :] - pos[:, np.newaxis, :]
        dists = np.linalg.norm(deltas, axis=2)
        nearest = np.argmin(dists, axis=1)
        return exit_positions[nearest]

    def _keep_inside_closed_walls(self, pos, vel):
        left = pos[:, 0] < 0.0
        right = pos[:, 0] > self.room_size[0]
        bottom = pos[:, 1] < 0.0
        top = pos[:, 1] > self.room_size[1]

        pos[left, 0] = 0.0
        vel[left, 0] = np.maximum(0.0, vel[left, 0])
        pos[right, 0] = self.room_size[0]
        vel[right, 0] = np.minimum(0.0, vel[right, 0])
        pos[bottom, 1] = 0.0
        vel[bottom, 1] = np.maximum(0.0, vel[bottom, 1])
        pos[top, 1] = self.room_size[1]
        vel[top, 1] = np.minimum(0.0, vel[top, 1])

    def _effective_wall_radius(self, wall_radius):
        return wall_radius + self.agent_body_radius

    def _internal_wall_forces(self, pos, wall_rep_weight, wall_radius):
        if self.internal_walls.size == 0:
            return np.zeros_like(pos)

        delta, dists = _point_segment_vectors(pos, self.internal_walls)
        interaction_radius = self._effective_wall_radius(wall_radius)
        in_range = dists < interaction_radius
        safe_dists = np.where(in_range, dists, 1.0)
        repulsion = wall_rep_weight / (safe_dists**2 + 1e-6)
        repulsion *= in_range

        unit = delta / (dists[:, :, np.newaxis] + 1e-6)
        forces = np.sum(unit * repulsion[:, :, np.newaxis], axis=1)
        return forces

    def _enforce_agent_separation(self, pos, vel, iterations=5):
        min_dist = 2.0 * self.agent_body_radius
        if self.agent_body_radius <= 0.0 or pos.shape[0] < 2:
            return pos, vel

        for _ in range(iterations):
            diffs = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
            dists = np.linalg.norm(diffs, axis=2)
            upper = np.triu(np.ones_like(dists, dtype=bool), k=1)
            overlap = np.maximum(0.0, min_dist - dists)
            overlap *= upper

            if not np.any(overlap):
                break

            safe_dists = np.where(overlap > 0.0, dists, 1.0)
            unit = diffs / (safe_dists[:, :, np.newaxis] + 1e-6)
            pair_correction = unit * overlap[:, :, np.newaxis] * 0.5
            correction = np.sum(pair_correction, axis=1) - np.sum(pair_correction, axis=0)
            pos += correction

            if np.any(correction):
                correction_speed = np.linalg.norm(correction, axis=1, keepdims=True)
                outward = correction / (correction_speed + 1e-6)
                inward_speed = np.sum(vel * outward, axis=1, keepdims=True)
                vel -= np.maximum(0.0, inward_speed) * outward

        return pos, vel

    def pair_wise_distances(self):
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
        exit_positions = np.array([exit_info["pos"] for exit_info in self.exits], dtype=float)
        dists = np.linalg.norm(exit_positions[np.newaxis, :, :] - pos[:, np.newaxis, :], axis=2)
        min_dists = np.min(dists, axis=1)
        return int(np.count_nonzero(min_dists < threshold))

    def snapshot(self, tick):
        return {
            "tick": int(tick),
            "positions": self.positions.tolist(),
            "active": self.active.astype(int).tolist(),
            "types": self.types.tolist(),
        }

    def step(self, params, dt=0.1):
        accel_factor, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius = params

        active_mask = self.active
        if not np.any(active_mask):
            return False

        pos = self.positions[active_mask]
        vel = self.velocities[active_mask]
        max_speeds = self.max_speeds[active_mask]

        target_positions = self._target_positions(pos, active_mask)
        directions = target_positions - pos
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
        interaction_radius = self._effective_wall_radius(wall_radius)
        dist_left = pos[:, 0]
        dist_right = self.room_size[0] - pos[:, 0]
        dist_bottom = pos[:, 1]
        dist_top = self.room_size[1] - pos[:, 1]

        in_range_left = dist_left < interaction_radius
        in_range_right = dist_right < interaction_radius
        in_range_bottom = dist_bottom < interaction_radius
        in_range_top = dist_top < interaction_radius

        in_range_left &= ~self._combined_door_mask(pos, "left")
        in_range_right &= ~self._combined_door_mask(pos, "right")
        in_range_bottom &= ~self._combined_door_mask(pos, "bottom")
        in_range_top &= ~self._combined_door_mask(pos, "top")

        wall_forces[in_range_left, 0] += wall_rep_weight / (dist_left[in_range_left] ** 2 + 1e-6)
        wall_forces[in_range_right, 0] -= wall_rep_weight / (dist_right[in_range_right] ** 2 + 1e-6)
        wall_forces[in_range_bottom, 1] += wall_rep_weight / (dist_bottom[in_range_bottom] ** 2 + 1e-6)
        wall_forces[in_range_top, 1] -= wall_rep_weight / (dist_top[in_range_top] ** 2 + 1e-6)
        wall_forces += self._internal_wall_forces(pos, wall_rep_weight, wall_radius)

        total_acceleration = acceleration + agent_forces + wall_forces
        vel += total_acceleration * dt

        speeds = np.linalg.norm(vel, axis=1)
        speed_factors = np.minimum(1.0, max_speeds / (speeds + 1e-6))
        vel *= speed_factors[:, np.newaxis]

        pos += vel * dt
        evacuated = self._evacuation_mask(pos)
        remaining_mask = ~evacuated
        if np.any(remaining_mask):
            remaining_pos = pos[remaining_mask]
            remaining_vel = vel[remaining_mask]
            if self.agent_body_radius > 0.0:
                remaining_pos, remaining_vel = self._enforce_agent_separation(remaining_pos, remaining_vel)
            self._keep_inside_closed_walls(remaining_pos, remaining_vel)
            pos[remaining_mask] = remaining_pos
            vel[remaining_mask] = remaining_vel

        self.positions[active_mask] = pos
        self.velocities[active_mask] = vel

        global_active_index = np.nonzero(active_mask)[0]
        self.active[global_active_index[evacuated]] = False
        return True


def _group_mean(values, mask):
    group_values = values[mask]
    valid_values = group_values[~np.isnan(group_values)]
    if valid_values.size == 0:
        return None
    return float(np.mean(valid_values))


def _serialize_exits(exits):
    return [
        {
            "pos": [float(exit_info["pos"][0]), float(exit_info["pos"][1])],
            "width": float(exit_info["width"]),
            "side": exit_info["side"],
        }
        for exit_info in exits
    ]


def _serialize_internal_walls(internal_walls):
    if not internal_walls:
        return []
    return [
        [[float(start[0]), float(start[1])], [float(end[0]), float(end[1])]]
        for start, end in internal_walls
    ]


def _serialize_spawn_zones(spawn_zones):
    if not spawn_zones:
        return []
    serialized = []
    for zone in spawn_zones:
        rect = zone["rect"]
        entry = {
            "rect": [float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])],
            "weight": float(zone.get("weight", 1.0)),
        }
        if zone.get("exit_index") is not None:
            entry["exit_index"] = int(zone["exit_index"])
        serialized.append(entry)
    return serialized


def run_simulation(
    params,
    num_high=30,
    num_low=10,
    room_size=(20.0, 20.0),
    exit_pos=(10.0, 20.0),
    exit_width=0.2,
    exits=None,
    internal_walls=None,
    spawn_zones=None,
    agent_body_radius=0.0,
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
        exit_width=exit_width,
        exits=exits,
        internal_walls=internal_walls,
        spawn_zones=spawn_zones,
        agent_body_radius=agent_body_radius,
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
    primary_exit = model.exits[0]
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
        "exit_pos": [float(primary_exit["pos"][0]), float(primary_exit["pos"][1])],
        "exit_width": float(primary_exit["width"]),
        "exit_side": primary_exit["side"],
        "exits": _serialize_exits(model.exits),
        "internal_walls": _serialize_internal_walls(internal_walls),
        "spawn_zones": _serialize_spawn_zones(spawn_zones),
        "agent_body_radius": float(agent_body_radius),
        "dt": float(dt),
    }
