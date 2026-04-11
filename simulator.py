import numpy as np

class EvacuationModel:
    def __init__(self, num_high, num_low, room_size=(20.0, 20.0), exit_pos=(10.0, 20.0)):
        self.num_agents = num_high + num_low
        self.room_size = np.array(room_size)
        self.exit_pos = np.array(exit_pos)

        # Initialize states
        # Random starting positions in the lower half of the room
        self.positions = np.random.rand(self.num_agents, 2) * [self.room_size[0], self.room_size[1] / 2]
        self.velocities = np.zeros((self.num_agents, 2))
        
        # Agents have heterogenous traits: (1 for high mobility, 0 for low mobility)
        self.types = np.array([1] * num_high + [0] * num_low)

        # Speeds are based on empirical data
        self.max_speeds = np.where(self.types == 1, 1.5, 0.5)
        self.active = np.ones(self.num_agents, dtype=bool)  # All agents start as active
    
    def pair_wise_distances(self):
        """
        Calculates the vector frm every agent to every other agent.
        Return diffs (N, N, 2) and dists (N, N)
        This is the core of local avoidance rules.
        """
        active_index = np.where(self.active)[0]
        pos = self.positions[active_index]

        # Get matrix of differences diffs[i,j] = pos[j] - pos[i], after that calculate distances for all pairs
        diffs = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]  # Shape: (M, M, 2)
        dists = np.linalg.norm(diffs, axis=2)                  # Shape: (M, M)
        np.fill_diagonal(dists, np.inf)                        # Ignore self
        return diffs, dists


    def step(self, params, dt=0.1):
        # Unpack parameters
        accel_factor, exit_treshold, agent_rep_weight, agent_radius, wall_rep_weight, wall_radius= params

        # Only process active agetns
        active_index = self.active
        if not np.any(active_index):
            return  False
        
        # Get local arrays for active agents
        pos = self.positions[active_index]
        vel = self.velocities[active_index]
        max_speeds = self.max_speeds[active_index]
        
        # Compute desired direction (only for active agents)
        directions = self.exit_pos - pos
        distances = np.linalg.norm(directions, axis=1, keepdims=True)
        desired_direction = directions / (distances + 1e-6) # Avoid division by zero

        # Desired velocity and update velocity
        desired_velocity = desired_direction * max_speeds[:, np.newaxis]
        acceleration = (desired_velocity - vel) * accel_factor

        ## Agent and Wall repulsion ##
        diffs, dists = self.pair_wise_distances()

        # We need to mask agetns within perception radius, and then calculate repulsive forces (inverse square law for sharp avoidance)
        in_range = dists < agent_radius
        # Calculate repulsion magnitude for all pairs
        repulsion_mag = agent_rep_weight / (dists**2 + 1e-6)
        
        # Apply the mask: zero out forces for agents outside the radius
        repulsion_mag *= in_range
        
        # Multiply magnitude by the normalized direction vector (diffs / dists)
        # We add np.newaxis to magnitude so it broadcasts against the X,Y of diffs
        force_vectors = (diffs / (dists[:, :, np.newaxis] + 1e-6)) * repulsion_mag[:, :, np.newaxis]
        
        # Sum all the pairwise forces for each agent.
        # Summing over axis 1 collapses the (M, M, 2) array back to (M, 2)
        agent_forces = np.sum(force_vectors, axis=1) 

        # Wall repulsion
        wall_forces = np.zeros_like(pos)
        # distances to walls (left, right, bottom, top)
        dist_left = pos[:, 0]
        dist_right = self.room_size[0] - pos[:, 0]
        dist_bottom = pos[:, 1]
        dist_top = self.room_size[1] - pos[:, 1]

        # Mask for walls within perception radius
        in_range_left = dist_left < wall_radius
        in_range_right = dist_right < wall_radius
        in_range_bottom = dist_bottom < wall_radius
        in_range_top = dist_top < wall_radius

        # Wall repulsion forces 
        wall_forces[in_range_left, 0 ] += wall_rep_weight / (dist_left[in_range_left]**2 + 1e-6)
        wall_forces[in_range_right, 0] -= wall_rep_weight / (dist_right[in_range_right]**2 + 1e-6)
        wall_forces[in_range_bottom, 1] += wall_rep_weight / (dist_bottom[in_range_bottom]**2 + 1e-6)
        wall_forces[in_range_top, 1] -= wall_rep_weight / (dist_top[in_range_top]**2 + 1e-6)

        # Apply all the forces and update the velocities
        total_acceleration = acceleration + agent_forces + wall_forces
        vel += total_acceleration * dt

        # We need to limit the speeds for the hetergeneous agent
        speeds = np.linalg.norm(vel, axis=1)
        speed_factors = np.minimum(1.0, max_speeds / (speeds + 1e-6))
        vel *= speed_factors[:, np.newaxis]

        # Update positions
        pos += vel * dt
        self.positions[active_index] = pos
        self.velocities[active_index] = vel

        # Check if agents have reached the exit, thus evacuated
        dist_to_exit = np.linalg.norm(self.exit_pos - pos, axis=1)
        evacuated = dist_to_exit < exit_treshold
        global_active_index = np.nonzero(active_index)[0]
        self.active[global_active_index[evacuated]] = False  # Mark evacuated agents
        
        return True
        
