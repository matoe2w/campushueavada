import numpy as np

# ==========================================
# 1. THE CAMPUS MAP
# ==========================================
inf = np.inf
campus_graph = np.array(
    [
        [0, 150, 200, inf],  # 0: Quad connects to Dorms (150m) and Library (200m)
        [150, 0, inf, 100],  # 1: Dorms connect to Quad (150m) and Cafe (100m)
        [200, inf, 0, 50],  # 2: Library connects to Quad (200m) and Cafe (50m)
        [inf, 100, 50, 0],  # 3: Cafe connects to Dorms (100m) and Library (50m)
    ]
)

# ==========================================
# 2. THE STUDENT BODY
# ==========================================
num_students = 1000

# Everyone starts at the Quad (Node 0), heading to the Dorms (Node 1)
current_nodes = np.zeros(num_students, dtype=int)
next_nodes = np.ones(num_students, dtype=int)

# Track progress in meters along their current path segment
distance_walked = np.zeros(num_students)

# Track how long each student should stay at their destination (in seconds)
wait_times = np.zeros(num_students)

# Give everyone a unique walking speed (normally distributed around 1.4 m/s)
speeds = np.random.normal(loc=1.4, scale=0.2, size=num_students)
speeds = np.maximum(speeds, 0.5)  # Prevent negative speeds

# ==========================================
# 3. THE SIMULATION LOOP
# ==========================================
print("Starting the campus simulation...\n")
simulation_steps = 150
dt = 1.0  # 1 second passes per loop iteration

for step in range(simulation_steps):
    print(f"--- Second {step} ---")

    # 1. Count down the timer for anyone who is currently resting inside a building
    waiting = wait_times > 0
    wait_times[waiting] -= dt

    # Create a mask of who is actually allowed to move outside right now
    moving = wait_times <= 0

    # ACTION 1: Walk forward (ONLY if you are moving)
    distance_walked[moving] += speeds[moving] * dt

    # ACTION 2: The "Forgot My Keys" scenario
    # Only apply it to people who are currently outside walking (0.05% chance)
    changed_mind = (np.random.rand(num_students) < 0.00005) & moving

    if np.any(changed_mind):
        print(f"  [!] {np.sum(changed_mind)} students just turned around.")
        temp_nodes = current_nodes[changed_mind].copy()
        current_nodes[changed_mind] = next_nodes[changed_mind]
        next_nodes[changed_mind] = temp_nodes

        edge_lengths = campus_graph[
            current_nodes[changed_mind], next_nodes[changed_mind]
        ]
        distance_walked[changed_mind] = edge_lengths - distance_walked[changed_mind]

    # ACTION 3: Handling Arrivals
    segment_lengths = campus_graph[current_nodes, next_nodes]
    # You can only arrive if you were actually moving this turn
    arrived = (distance_walked >= segment_lengths) & moving

    if np.any(arrived):
        num_arrived = np.sum(arrived)
        print(f"  [*] {num_arrived} students arrived and are hanging out.")

        # Assign a random wait time (e.g., stay for 60 to 300 seconds)
        wait_times[arrived] = np.random.uniform(60, 300, size=num_arrived)

        arrived_indices = np.where(arrived)[0]

        for idx in arrived_indices:
            node_arrived_at = next_nodes[idx]
            connections = campus_graph[node_arrived_at]
            valid_paths = np.where((connections > 0) & (connections != inf))[0]
            chosen_path = np.random.choice(valid_paths)

            # Assign their next route NOW, but they won't walk it until wait_times hits 0
            current_nodes[idx] = node_arrived_at
            next_nodes[idx] = chosen_path

            # Reset their distance completely so they start fresh when their wait is over
            distance_walked[idx] = 0

print("\nSimulation complete.")
