import sys

import numpy as np
import pygame

# ==========================================
# 1. UCSG CAMPUS TOPOLOGY CONFIGURATION
# ==========================================
inf = np.inf

node_coords = np.array(
    [
        [460, 640],  # 0: A - Facultad de Artes
        [410, 540],  # 1: B - Facultad de Jurisprudencia
        [180, 340],  # 2: C - Facultad de Ciencias Economicas
        [260, 240],  # 3: D - Facultad de Educacion Tecnica
        [700, 140],  # 4: E - Facultad de Ciencias Medicas
        [840, 360],  # 5: F - Facultad de Filosofia y Letras
        [810, 520],  # 6: G - Facultad de Arquitectura y Diseno
        [660, 560],  # 7: H - Facultad de Ingenieria
        [720, 680],  # 8: I - Edificio de Posgrado (Massive Complex)
        [380, 460],  # 9: Biblioteca General (Central Hub Plaza)
        [440, 340],  # 10: Cruce Camino Norte (Transit Hub Node)
        [540, 550],  # 11: Cruce Camino Sur (Transit Hub Node)
    ]
)

node_names = [
    "Fac. Artes",
    "Fac. Jurisprudencia",
    "Fac. Economicas",
    "Fac. Ed. Tecnica",
    "Fac. Medicas",
    "Fac. Filosofia",
    "Fac. Arquitectura",
    "Fac. Ingenieria",
    "Postgrado",
    "Biblioteca General",
    "Cruce Norte",
    "Cruce Sur",
]

# Total seats = 25+35+50+40+65+35+40+45+60+130 = 530
node_capacities = np.array([25, 35, 50, 40, 65, 35, 40, 45, 60, 130, 0, 0])

# Massive attraction weight shift applied directly to the Library (Node 9)
node_attraction_weights = np.array(
    [1.2, # Artes
     1.3, # Jurisprudencia
     1.6, # Econ.
     0.9, # Ed. Técnica
     2.0, # Med.
     0.6, # filosofía
     1.4, # Arch.
     1.4, # Ing.
     2.2, # Postgrado
     10.0, # Biblioteca
     0.5, # Cruce norte
     0.5 # Cruce sur
    ] # ATTRACTION WEIGHTS
)

num_nodes = len(node_names)
campus_graph = np.full((num_nodes, num_nodes), inf)
np.fill_diagonal(campus_graph, 0)

geographical_connections = [
    (0, 1),
    (0, 8),
    (1, 9),
    (1, 11),
    (2, 3),
    (2, 9),
    (2, 10),
    (3, 10),
    (4, 5),
    (4, 10),
    (5, 6),
    (6, 7),
    (6, 11),
    (7, 8),
    (7, 11),
    (8, 11),
    (9, 10),
    (9, 11),
    (10, 11),
]

for u, v in geographical_connections:
    dx = node_coords[u, 0] - node_coords[v, 0]
    dy = node_coords[u, 1] - node_coords[v, 1]
    pixel_distance = int(np.sqrt(dx**2 + dy**2))
    campus_graph[u, v] = pixel_distance
    campus_graph[v, u] = pixel_distance

SQUIGGLE_AMPLITUDE = 10
SQUIGGLE_FREQUENCY = 2

# ==========================================
# 2. PYGAME DESKTOP SURFACE INITIALIZATION
# ==========================================
pygame.init()

# Time multiplier lowered to exactly 1000 simulated seconds per real second
TIME_MULTIPLIER = 600
WIDTH, HEIGHT = 1300, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("UCSG Predictive Infrastructure Simulation")
clock = pygame.time.Clock()

label_font = pygame.font.SysFont("Arial", 12, bold=True)
title_font = pygame.font.SysFont("Arial", 18, bold=True)
ui_font = pygame.font.SysFont("Arial", 14, bold=True)

COLOR_BG = (248, 249, 250)
COLOR_SIDEBAR = (235, 238, 242)
COLOR_NODE = (163, 0, 58)
COLOR_HUB = (50, 80, 120)
COLOR_LINE = (210, 214, 219)
COLOR_WALKING = (40, 167, 69)
COLOR_RESTING = (220, 53, 69)
COLOR_TEXT = (33, 37, 41)

# ==========================================
# 3. INTERACTIVE ENGINE SIMULATION VARIABLES
# ==========================================
USE_STUDY_APP = False
APP_CERTAINTY = 1.00

MAX_POOL_AGENTS = 550
# Set strictly to match total physical capacity across the architecture
TARGET_ACTIVE_STUDENTS = int(np.sum(node_capacities) + 200)

agent_states = np.zeros(MAX_POOL_AGENTS, dtype=int)
current_nodes = np.zeros(MAX_POOL_AGENTS, dtype=int)
next_nodes = np.zeros(MAX_POOL_AGENTS, dtype=int)
distance_walked = np.zeros(MAX_POOL_AGENTS)
wait_times = np.zeros(MAX_POOL_AGENTS)
patience_counters = np.random.randint(50, 100, size=MAX_POOL_AGENTS)
speeds = np.random.normal(loc=1.35, scale=0.15, size=MAX_POOL_AGENTS)
speeds = np.maximum(speeds, 0.6)

cluster_offsets = np.random.uniform(-12, 12, size=(MAX_POOL_AGENTS, 2))

# Unified Analytics Framework
search_times = np.zeros(MAX_POOL_AGENTS)
failed_attempts = np.zeros(MAX_POOL_AGENTS, dtype=int)
total_search_time_accumulated = 0.0
total_search_trips_completed = 0


def get_occupancy():
    counts = np.zeros(num_nodes, dtype=int)
    for i in range(MAX_POOL_AGENTS):
        if agent_states[i] == 2:
            counts[current_nodes[i]] += 1
    return counts


def select_next_node(start_node, occupancy_array):
    connections = campus_graph[start_node]
    valid_paths = np.where((connections > 0) & (connections != inf))[0]
    weights = node_attraction_weights[valid_paths].copy()

    if USE_STUDY_APP:
        for idx, path_node in enumerate(valid_paths):
            if path_node < 10:
                fullness = occupancy_array[path_node] / node_capacities[path_node]
                weights[idx] *= max(0.001, 1.0 - (fullness * APP_CERTAINTY))

    probs = weights / np.sum(weights)
    return np.random.choice(valid_paths, p=probs)


# Precalculate pathways
cached_rail_lines = []
for i in range(len(campus_graph)):
    for j in range(i + 1, len(campus_graph)):
        if campus_graph[i, j] != inf and campus_graph[i, j] > 0:
            x_i, y_i = node_coords[i]
            x_j, y_j = node_coords[j]
            line_dx, line_dy = x_j - x_i, y_j - y_i
            line_L = np.sqrt(line_dx**2 + line_dy**2)
            line_nx, line_ny = -line_dy / line_L, line_dx / line_L
            p_vals = np.linspace(0, 1, 120)
            line_squiggle = SQUIGGLE_AMPLITUDE * np.sin(
                SQUIGGLE_FREQUENCY * np.pi * p_vals
            )
            curve_x = x_i + p_vals * line_dx + line_nx * line_squiggle
            curve_y = y_i + p_vals * line_dy + line_ny * line_squiggle
            cached_rail_lines.append(
                list(zip(curve_x.astype(int), curve_y.astype(int)))
            )

# ==========================================
# 4. CORE RUNTIME PIPELINE
# ==========================================
running = True
step_time = 0.0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                USE_STUDY_APP = not USE_STUDY_APP

    sim_dt = (1.0 / 60.0) * TIME_MULTIPLIER
    step_time += sim_dt

    faculty_headcounts = get_occupancy()
    active_count = np.sum(agent_states > 0)

    # Spawning Framework
    # Change the spawn rate logic in the main loop
    if active_count < TARGET_ACTIVE_STUDENTS:
        inactive_slots = np.where(agent_states == 0)[0]
        if (
            len(inactive_slots) > 0 and np.random.rand() < 0.9
        ):  # Increased from 0.4 to 0.9
            spawn_idx = inactive_slots[0]
            # ... rest of your spawn logic
            agent_states[spawn_idx] = 1
            current_nodes[spawn_idx] = np.random.randint(0, num_nodes)
            next_nodes[spawn_idx] = select_next_node(
                current_nodes[spawn_idx], faculty_headcounts
            )
            distance_walked[spawn_idx] = 0
            wait_times[spawn_idx] = 0
            search_times[spawn_idx] = 0.0
            failed_attempts[spawn_idx] = 0
            patience_counters[spawn_idx] = np.random.randint(3, 6)

    # Processing Systems
    for idx in range(MAX_POOL_AGENTS):
        if agent_states[idx] == 0:
            continue

        if agent_states[idx] == 2:
            wait_times[idx] -= sim_dt
            if wait_times[idx] <= 0:
                agent_states[idx] = 0
            continue

        if agent_states[idx] == 1:
            if failed_attempts[idx] > 0:
                search_times[idx] += sim_dt

            segment_L = campus_graph[current_nodes[idx], next_nodes[idx]]
            distance_walked[idx] += speeds[idx] * sim_dt

            if distance_walked[idx] >= segment_L:
                node_arrived = next_nodes[idx]

                # --- REPLACE THIS SECTION IN YOUR PROCESSING LOOP ---
                # Ensure strict capacity enforcement
                if node_arrived < 10:
                    if faculty_headcounts[node_arrived] < node_capacities[node_arrived]:
                        # Successfully found a seat
                        total_search_time_accumulated += search_times[idx]
                        total_search_trips_completed += 1

                        current_nodes[idx] = node_arrived
                        faculty_headcounts[node_arrived] += 1
                        agent_states[idx] = 2

                        # Stays for a long duration
                        wait_times[idx] = np.random.uniform(5400, 14400)
                        continue
                    else:
                        # FAILED to find a seat, log this as a search event
                        failed_attempts[idx] += 1
                        # DO NOT let them stay at the node
                        current_nodes[idx] = node_arrived
                        next_nodes[idx] = select_next_node(
                            node_arrived, faculty_headcounts
                        )
                        distance_walked[idx] = 0
                        continue

                current_nodes[idx] = node_arrived
                next_nodes[idx] = select_next_node(node_arrived, faculty_headcounts)
                distance_walked[idx] = 0

    # Vectorized Rendering Transforms
    walking_mask = agent_states == 1
    student_x = np.zeros(MAX_POOL_AGENTS)
    student_y = np.zeros(MAX_POOL_AGENTS)

    if np.any(walking_mask):
        c_n = current_nodes[walking_mask]
        n_n = next_nodes[walking_mask]
        lengths = campus_graph[c_n, n_n]
        pct = np.clip(distance_walked[walking_mask] / lengths, 0.0, 1.0)

        flip = c_n > n_n
        p_track = np.where(flip, 1.0 - pct, pct)
        id_start = np.where(flip, n_n, c_n)
        id_end = np.where(flip, c_n, n_n)

        pos_s = node_coords[id_start]
        pos_e = node_coords[id_end]

        dx = pos_e[:, 0] - pos_s[:, 0]
        dy = pos_e[:, 1] - pos_s[:, 1]
        L = np.maximum(1, np.sqrt(dx**2 + dy**2))

        nx, ny = -dy / L, dx / L
        sq = SQUIGGLE_AMPLITUDE * np.sin(SQUIGGLE_FREQUENCY * np.pi * p_track)

        student_x[walking_mask] = pos_s[:, 0] + dx * p_track + nx * sq
        student_y[walking_mask] = pos_s[:, 1] + dy * p_track + ny * sq

    studying_mask = agent_states == 2
    if np.any(studying_mask):
        student_x[studying_mask] = (
            node_coords[current_nodes[studying_mask], 0]
            + cluster_offsets[studying_mask, 2]
            if cluster_offsets.shape[1] > 2
            else cluster_offsets[studying_mask, 0]
        )
        student_y[studying_mask] = (
            node_coords[current_nodes[studying_mask], 1]
            + cluster_offsets[studying_mask, 1]
        )

    # ==========================================
    # 5. BLITTING AND SURFACE LAYERING
    # ==========================================
    screen.fill(COLOR_BG)

    for points in cached_rail_lines:
        pygame.draw.lines(screen, COLOR_LINE, False, points, 2)

    for i in range(MAX_POOL_AGENTS):
        if agent_states[i] == 1:
            pygame.draw.circle(
                screen, COLOR_WALKING, (int(student_x[i]), int(student_y[i])), 3
            )
        elif agent_states[i] == 2:
            pygame.draw.circle(
                screen, COLOR_RESTING, (int(student_x[i]), int(student_y[i])), 3
            )

    for i, coord in enumerate(node_coords):
        node_color = COLOR_HUB if i >= 10 else COLOR_NODE
        pygame.draw.circle(screen, node_color, (coord[0], coord[1]), 14)

    for i, name in enumerate(node_names):
        display_text = (
            f"{name} ({faculty_headcounts[i]}/{node_capacities[i]})" if i < 10 else name
        )
        text_surface = label_font.render(display_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(
            center=(node_coords[i, 0], node_coords[i, 1] - 22)
        )
        screen.blit(text_surface, text_rect)

    hours = int(step_time // 3600)
    mins = int((step_time % 3600) // 60)
    title_text = f"UCSG Infrastructure Optimization Lab — Time: {hours}h {mins}m"
    title_surface = title_font.render(title_text, True, COLOR_TEXT)
    screen.blit(title_surface, (25, 25))

    app_status_text = f"STUDY APP PATH ROUTING: {'ACTIVE (85% certainty)' if USE_STUDY_APP else 'OFF (Pure Random Search)'}"
    app_status_color = (40, 120, 200) if USE_STUDY_APP else (140, 145, 150)
    app_surface = ui_font.render(app_status_text, True, app_status_color)
    screen.blit(app_surface, (25, 55))

    if total_search_trips_completed > 0:
        avg_search_minutes = (
            total_search_time_accumulated / total_search_trips_completed
        ) / 60.0
        metric_text = f"Average Time Spent Looking For a Spot: {avg_search_minutes:.1f} Simulation Minutes"
    else:
        metric_text = (
            "Average Time Spent Looking For a Spot: Collecting initial data..."
        )

    metric_surface = ui_font.render(
        metric_text, True, COLOR_NODE if not USE_STUDY_APP else COLOR_WALKING
    )
    screen.blit(metric_surface, (25, 80))

    instruction_surface = label_font.render(
        "Press 'A' on your keyboard to toggle the App live", True, (120, 130, 140)
    )
    screen.blit(instruction_surface, (25, 105))

    # ==========================================
    # 6. LIVE DATA GRAPH SIDEBAR PANEL
    # ==========================================
    pygame.draw.rect(screen, COLOR_SIDEBAR, (1000, 0, 300, HEIGHT))
    pygame.draw.line(screen, (195, 200, 205), (1000, 0), (1000, HEIGHT), 2)

    sidebar_title = title_font.render("Seat Occupancy Metrics", True, COLOR_TEXT)
    screen.blit(sidebar_title, (1025, 25))

    for i in range(10):
        name = node_names[i]
        y_pos = 85 + i * 68
        count = faculty_headcounts[i]
        cap = node_capacities[i]

        data_string = f"{name}: {count} / {cap} Seats Occupied"
        data_surface = label_font.render(data_string, True, COLOR_TEXT)
        screen.blit(data_surface, (1025, y_pos))

        max_bar_width = 240
        fill_ratio = count / cap if cap > 0 else 0
        bar_fill_w = int(np.clip(fill_ratio * max_bar_width, 0, max_bar_width))

        pygame.draw.rect(
            screen,
            (210, 215, 222),
            (1025, y_pos + 20, max_bar_width, 10),
            border_radius=3,
        )
        if count > 0:
            bar_color = COLOR_RESTING if fill_ratio >= 0.9 else COLOR_HUB
            pygame.draw.rect(
                screen, bar_color, (1025, y_pos + 20, bar_fill_w, 10), border_radius=3
            )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
