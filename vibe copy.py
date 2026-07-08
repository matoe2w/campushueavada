import sys

import numpy as np
import pygame

# ==========================================
# 1. UCSG CAMPUS TOPOLOGY CONFIGURATION
# ==========================================
inf = np.inf

# Updated spatial coordinate grid with Economics pushed further up
node_coords = np.array(
    [
        [460, 640],  # 0: A - Facultad de Artes
        [410, 540],  # 1: B - Facultad de Jurisprudencia
        [180, 340],  # 2: C - Facultad de Ciencias Economicas (Pushed up from 460)
        [260, 240],  # 3: D - Facultad de Educacion Tecnica
        [700, 140],  # 4: E - Facultad de Ciencias Medicas
        [840, 360],  # 5: F - Facultad de Filosofia y Letras
        [810, 520],  # 6: G - Facultad de Arquitectura y Diseno
        [660, 560],  # 7: H - Facultad de Ingenieria
        [720, 680],  # 8: I - Edificio de Posgrado
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

num_nodes = len(node_names)
campus_graph = np.full((num_nodes, num_nodes), inf)
np.fill_diagonal(campus_graph, 0)

# Geographically mapped connections including the new transit links
geographical_connections = [
    # Main Entrance Area & Bottom-Center Neighbors
    (0, 1),  # Artes to Jurisprudencia
    (0, 8),  # Artes to Posgrado (Front entrance road)
    (1, 9),  # Jurisprudencia to Biblioteca
    (1, 11),  # Jurisprudencia to Cruce Sur
    # Left Campus Ring & New Cruce Norte Plug
    (2, 3),  # Economicas to Ed. Tecnica
    (2, 9),  # Economicas to Biblioteca
    (2, 10),  # NEW: Economicas plugged directly into Cruce Norte
    (3, 10),  # Ed. Tecnica to Cruce Norte
    # Top & Right Campus Ring
    (4, 5),  # Medicas to Filosofia
    (4, 10),  # Medicas to Cruce Norte
    (5, 6),  # Filosofia to Arquitectura
    (6, 7),  # Arquitectura to Ingenieria
    (6, 11),  # Arquitectura to Cruce Sur
    (7, 8),  # Ingenieria to Posgrado
    (7, 11),  # Ingenieria to Cruce Sur
    (8, 11),  # NEW: Posgrado plugged directly into Cruce Sur
    # Central Central Walkway Distribution Spine
    (9, 10),  # Biblioteca to Cruce Norte
    (9, 11),  # Biblioteca to Cruce Sur
    (10, 11),  # Cruce Norte to Cruce Sur
]

# Compute geometric pixel distances dynamically for valid neighbor paths
for u, v in geographical_connections:
    dx = node_coords[u, 0] - node_coords[v, 0]
    dy = node_coords[u, 1] - node_coords[v, 1]
    pixel_distance = int(np.sqrt(dx**2 + dy**2))
    campus_graph[u, v] = pixel_distance
    campus_graph[v, u] = pixel_distance

# Unique stickiness profile (Structural paths have 0% dwell time)
node_wait_probabilities = np.array(
    [
        0.70,
        0.70,
        0.80,
        0.60,
        0.85,
        0.70,
        0.80,
        0.90,
        0.70,
        0.50,
        0.00,
        0.00,  # Pass-through flow points
    ]
)

# Attraction Weight (Relative likelihood of selecting this node as a next destination)
node_attraction_weights = np.array(
    [
        1.2,
        1.2,
        1.0,
        0.9,
        1.5,
        1.0,
        1.1,
        1.1,
        0.8,
        1.6,
        1.0,
        1.0,  # Core routing distributions for transit hubs
    ]
)

SQUIGGLE_AMPLITUDE = 10
SQUIGGLE_FREQUENCY = 2

# ==========================================
# 2. PYGAME DESKTOP SURFACE INITIALIZATION
# ==========================================
pygame.init()

TIME_MULTIPLIER = 300
WIDTH, HEIGHT = 1300, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("UCSG Campus Live Network Simulation")
clock = pygame.time.Clock()

label_font = pygame.font.SysFont("Arial", 12, bold=True)
title_font = pygame.font.SysFont("Arial", 18, bold=True)

COLOR_BG = (248, 249, 250)
COLOR_SIDEBAR = (235, 238, 242)
COLOR_NODE = (163, 0, 58)
COLOR_HUB = (50, 80, 120)  # Visual distinction for path nodes
COLOR_LINE = (210, 214, 219)
COLOR_WALKING = (40, 167, 69)
COLOR_RESTING = (220, 53, 69)
COLOR_TEXT = (33, 37, 41)

# ==========================================
# 3. ADVANCED SIMULATION AGENT BODY
# ==========================================
num_students = 1200

current_nodes = np.random.randint(0, num_nodes, size=num_students)
next_nodes = np.zeros(num_students, dtype=int)
distance_walked = np.zeros(num_students)
wait_times = np.zeros(num_students)

for idx in range(num_students):
    start_node = current_nodes[idx]
    connections = campus_graph[start_node]
    valid_paths = np.where((connections > 0) & (connections != inf))[0]

    path_weights = node_attraction_weights[valid_paths]
    path_probs = path_weights / np.sum(path_weights)
    next_nodes[idx] = np.random.choice(valid_paths, p=path_probs)

speeds = np.random.normal(loc=1.35, scale=0.15, size=num_students)
speeds = np.maximum(speeds, 0.6)

# ==========================================
# 4. PRE-CALCULATING THE GRAPH RAILS
# ==========================================
cached_rail_lines = []
for i in range(len(campus_graph)):
    for j in range(i + 1, len(campus_graph)):
        if campus_graph[i, j] != inf and campus_graph[i, j] > 0:
            x_i, y_i = node_coords[i]
            x_j, y_j = node_coords[j]

            line_dx = x_j - x_i
            line_dy = y_j - y_i
            line_L = np.sqrt(line_dx**2 + line_dy**2)

            line_nx = -line_dy / line_L
            line_ny = line_dx / line_L

            p_vals = np.linspace(0, 1, 120)
            line_squiggle = SQUIGGLE_AMPLITUDE * np.sin(
                SQUIGGLE_FREQUENCY * np.pi * p_vals
            )

            curve_x = x_i + p_vals * line_dx + line_nx * line_squiggle
            curve_y = y_i + p_vals * line_dy + line_ny * line_squiggle

            points = list(zip(curve_x.astype(int), curve_y.astype(int)))
            cached_rail_lines.append(points)

# ==========================================
# 5. CORE RUNTIME PIPELINE
# ==========================================
running = True
step_time = 0.0

print("Running UCSG Network Graph Simulation... Close window to safely exit.")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    sim_dt = (1.0 / 60.0) * TIME_MULTIPLIER
    step_time += sim_dt

    waiting = wait_times > 0
    wait_times[waiting] -= sim_dt
    moving = wait_times <= 0

    distance_walked[moving] += speeds[moving] * sim_dt

    changed_mind = (np.random.rand(num_students) < 0.0003) & moving
    if np.any(changed_mind):
        temp_nodes = current_nodes[changed_mind].copy()
        current_nodes[changed_mind] = next_nodes[changed_mind]
        next_nodes[changed_mind] = temp_nodes

        edge_lengths = campus_graph[
            current_nodes[changed_mind], next_nodes[changed_mind]
        ]
        distance_walked[changed_mind] = edge_lengths - distance_walked[changed_mind]

    segment_lengths = campus_graph[current_nodes, next_nodes]
    arrived = (distance_walked >= segment_lengths) & moving

    if np.any(arrived):
        arrived_indices = np.where(arrived)[0]

        for idx in arrived_indices:
            node_arrived_at = next_nodes[idx]
            stay_likelihood = node_wait_probabilities[node_arrived_at]

            if np.random.rand() < stay_likelihood:
                wait_times[idx] = np.random.uniform(3600, 10800)
            else:
                wait_times[idx] = 0

            connections = campus_graph[node_arrived_at]
            valid_paths = np.where((connections > 0) & (connections != inf))[0]

            path_weights = node_attraction_weights[valid_paths]
            path_probs = path_weights / np.sum(path_weights)
            chosen_path = np.random.choice(valid_paths, p=path_probs)

            current_nodes[idx] = node_arrived_at
            next_nodes[idx] = chosen_path
            distance_walked[idx] = 0

    # ==========================================
    # 6. VECTORIZED SPACE TRANSFORMS
    # ==========================================
    current_lengths = campus_graph[current_nodes, next_nodes]
    progress_pct = np.clip(distance_walked / current_lengths, 0.0, 1.0)

    flip_mask = current_nodes > next_nodes
    p_track = np.where(flip_mask, 1.0 - progress_pct, progress_pct)

    id_start = np.where(flip_mask, next_nodes, current_nodes)
    id_end = np.where(flip_mask, current_nodes, next_nodes)

    pos_start = node_coords[id_start]
    pos_end = node_coords[id_end]

    dx = pos_end[:, 0] - pos_start[:, 0]
    dy = pos_end[:, 1] - pos_start[:, 1]
    L = np.sqrt(dx**2 + dy**2)
    L = np.where(L == 0, 1, L)

    nx = -dy / L
    ny = dx / L

    student_squiggle = SQUIGGLE_AMPLITUDE * np.sin(SQUIGGLE_FREQUENCY * np.pi * p_track)
    student_x = pos_start[:, 0] + dx * p_track + nx * student_squiggle
    student_y = pos_start[:, 1] + dy * p_track + ny * student_squiggle

    faculty_headcounts = np.bincount(current_nodes[wait_times > 0], minlength=num_nodes)

    # ==========================================
    # 7. BLITTING AND SURFACE LAYERING
    # ==========================================
    screen.fill(COLOR_BG)

    for points in cached_rail_lines:
        pygame.draw.lines(screen, COLOR_LINE, False, points, 2)

    for i in range(num_students):
        color = COLOR_RESTING if wait_times[i] > 0 else COLOR_WALKING
        pygame.draw.circle(screen, color, (int(student_x[i]), int(student_y[i])), 3)

    for i, coord in enumerate(node_coords):
        node_color = COLOR_HUB if i >= 10 else COLOR_NODE
        pygame.draw.circle(screen, node_color, (coord[0], coord[1]), 14)

    # Render labels with live population values appended for actual campus facilities
    for i, name in enumerate(node_names):
        display_text = f"{name} ({faculty_headcounts[i]})" if i < 10 else name
        text_surface = label_font.render(display_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(
            center=(node_coords[i, 0], node_coords[i, 1] - 22)
        )
        screen.blit(text_surface, text_rect)

    hours_elapsed = int(step_time // 3600)
    mins_elapsed = int((step_time % 3600) // 60)
    title_text = f"UCSG Campus Network Infrastructure Engine — Elapsed Time: {hours_elapsed}h {mins_elapsed}m"
    title_surface = title_font.render(title_text, True, COLOR_TEXT)
    screen.blit(title_surface, (25, 25))

    active_walkers = np.sum(wait_times <= 0)
    metrics_text = f"Active Pedestrians on Pathways: {active_walkers}  |  Total Population: {num_students}"
    metrics_surface = label_font.render(metrics_text, True, (100, 110, 120))
    screen.blit(metrics_surface, (25, 55))

    # ==========================================
    # 8. LIVE DATA GRAPH SIDEBAR PANEL
    # ==========================================
    pygame.draw.rect(screen, COLOR_SIDEBAR, (1000, 0, 300, HEIGHT))
    pygame.draw.line(screen, (195, 200, 205), (1000, 0), (1000, HEIGHT), 2)

    sidebar_title = title_font.render("Faculty Population Graphs", True, COLOR_TEXT)
    screen.blit(sidebar_title, (1025, 25))

    for i in range(10):
        name = node_names[i]
        y_pos = 85 + i * 68
        count = faculty_headcounts[i]

        data_string = f"{name}: {count} inside"
        data_surface = label_font.render(data_string, True, COLOR_TEXT)
        screen.blit(data_surface, (1025, y_pos))

        max_bar_width = 240
        fill_ratio = count / 350
        bar_fill_w = int(np.clip(fill_ratio * max_bar_width, 0, max_bar_width))

        pygame.draw.rect(
            screen,
            (210, 215, 222),
            (1025, y_pos + 20, max_bar_width, 10),
            border_radius=3,
        )
        if count > 0:
            pygame.draw.rect(
                screen, COLOR_NODE, (1025, y_pos + 20, bar_fill_w, 10), border_radius=3
            )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
