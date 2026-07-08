import sys
import pygame
import numpy as np

# ==========================================
# 1. UCSG CAMPUS TOPOLOGY CONFIGURATION
# ==========================================
inf = np.inf
campus_graph = np.array([
    #  A    B    C    D    E    F    G    H    I   Bib   <-- Destination Node
    [  0, 110, inf, inf, inf, inf, inf, inf, 380, inf],  # A: Artes
    [110,   0, 240, inf, inf, inf, inf, 420, inf,  60],  # B: Jurisprudencia <-> Library
    [inf, 240,   0, 310, inf, inf, inf, inf, inf, 120],  # C: Economicas     <-> Library
    [inf, inf, 310,   0, 580, 480, inf, inf, inf, inf],  # D: Ed. Tecnica
    [inf, inf, inf, 580,   0, 360, inf, inf, inf, inf],  # E: Medicas
    [inf, inf, inf, 480, 360,   0, 180, inf, inf, inf],  # F: Filosofia
    [inf, inf, inf, inf, inf, 180,   0,  90, inf, inf],  # G: Arquitectura
    [inf, 420, inf, inf, inf, inf,  90,   0, 140, 250],  # H: Ingenieria     <-> Library
    [380, inf, inf, inf, inf, inf, inf, 140,   0, inf],  # I: Posgrado
    [inf,  60, 120, inf, inf, inf, inf, 250, inf,   0],  # Bib: Biblioteca General
])
# Pixel coordinates mapped to match the layout of the UCSG map images
# Window size: 1000x800. (0,0) is top-left.
node_coords = np.array([
    [460, 640],  # 0: A - Facultad de Artes
    [410, 540],  # 1: B - Facultad de Jurisprudencia
    [180, 460],  # 2: C - Facultad de Ciencias Economicas
    [260, 240],  # 3: D - Facultad de Educacion Tecnica
    [700, 140],  # 4: E - Facultad de Ciencias Medicas
    [840, 360],  # 5: F - Facultad de Filosofia y Letras
    [810, 520],  # 6: G - Facultad de Arquitectura y Diseno
    [660, 560],  # 7: H - Facultad de Ingenieria
    [720, 680],  # 8: I - Edificio de Posgrado
    [380, 460],  # 9: Biblioteca General (Central Loop Cluster)
])

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
    "Biblioteca General"  # Index 9
]

# Wave configurations for realistic winding pedestrian pathways
SQUIGGLE_AMPLITUDE = 20
SQUIGGLE_FREQUENCY = 2

# ==========================================
# 2. PYGAME DESKTOP SURFACE INITIALIZATION
# ==========================================
pygame.init()
#
# here is the damn multiplier
#
TIME_MULTIPLIER = 10
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("UCSG Campus Live Network Simulation")
clock = pygame.time.Clock()

# UI Graphics assets
label_font = pygame.font.SysFont("Arial", 12, bold=True)
title_font = pygame.font.SysFont("Arial", 18, bold=True)

# Color Templates (RGB)
COLOR_BG = (248, 249, 250)       # Clean light off-white
COLOR_NODE = (163, 0, 58)         # UCSG Crimson Magenta Tone
COLOR_LINE = (210, 214, 219)      # Subtle gray path traces
COLOR_WALKING = (40, 167, 69)     # Fluid Green
COLOR_RESTING = (220, 53, 69)     # Soft Action Red
COLOR_TEXT = (33, 37, 41)

# ==========================================
# 3. ADVANCED SIMULATION AGENT BODY
# ==========================================
num_students = 1200  # Scaled up population count for larger campus topology

current_nodes = np.random.randint(0, len(node_names), size=num_students)
next_nodes = np.zeros(num_students, dtype=int)
distance_walked = np.zeros(num_students)
wait_times = np.zeros(num_students)

# Assign valid connected pathway vectors for every spawned entity
for idx in range(num_students):
    start_node = current_nodes[idx]
    connections = campus_graph[start_node]
    valid_paths = np.where((connections > 0) & (connections != inf))[0]
    next_nodes[idx] = np.random.choice(valid_paths)

# Realistic human locomotion distribution parameters (m/s)
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
            line_squiggle = SQUIGGLE_AMPLITUDE * np.sin(SQUIGGLE_FREQUENCY * np.pi * p_vals)

            curve_x = x_i + p_vals * line_dx + line_nx * line_squiggle
            curve_y = y_i + p_vals * line_dy + line_ny * line_squiggle

            points = list(zip(curve_x.astype(int), curve_y.astype(int)))
            cached_rail_lines.append(points)

# ==========================================
# 5. CORE RUNTIME PIPELINE
# ==========================================
running = True
step_time = 0.0
dt = 1.0 / 60.0  # Synced exactly to 60hz frame timing updates

# Change Line 88 to this:
sim_dt = dt * TIME_MULTIPLIER
print("Running UCSG Network Graph Simulation... Close window to safely exit.")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Multiply the frame delta by your warp factor for the simulation math
    sim_dt = (1.0 / 60.0) * TIME_MULTIPLIER
    step_time += sim_dt

    # Processing state vectors using the accelerated time step
    waiting = wait_times > 0
    wait_times[waiting] -= sim_dt
    moving = wait_times <= 0

    # Step forward along graph pathways using accelerated time step
    distance_walked[moving] += speeds[moving] * sim_dt

    # Mid-path conversion event processing
    changed_mind = (np.random.rand(num_students) < 0.0003) & moving
    if np.any(changed_mind):
        temp_nodes = current_nodes[changed_mind].copy()
        current_nodes[changed_mind] = next_nodes[changed_mind]
        next_nodes[changed_mind] = temp_nodes

        edge_lengths = campus_graph[current_nodes[changed_mind], next_nodes[changed_mind]]
        distance_walked[changed_mind] = edge_lengths - distance_walked[changed_mind]

    # Hub arrival processing mechanics
    segment_lengths = campus_graph[current_nodes, next_nodes]
    arrived = (distance_walked >= segment_lengths) & moving

    if np.any(arrived):
        num_arrived = np.sum(arrived)
        # Reasonably scaled class wait steps: random stay duration from 15 to 60 simulated seconds
        wait_times[arrived] = np.random.uniform(15, 60, size=num_arrived)
        arrived_indices = np.where(arrived)[0]

        for idx in arrived_indices:
            node_arrived_at = next_nodes[idx]
            connections = campus_graph[node_arrived_at]
            valid_paths = np.where((connections > 0) & (connections != inf))[0]
            chosen_path = np.random.choice(valid_paths)

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

    # ==========================================
    # 7. BLITTING AND SURFACE LAYERING
    # ==========================================
    screen.fill(COLOR_BG)

    # Base Level: Winding path tracks
    for points in cached_rail_lines:
        pygame.draw.lines(screen, COLOR_LINE, False, points, 2)

    # Mid Level: Dynamic agent particles (scaled to size 3 for crisp streams)
    for i in range(num_students):
        color = COLOR_RESTING if wait_times[i] > 0 else COLOR_WALKING
        pygame.draw.circle(screen, color, (int(student_x[i]), int(student_y[i])), 3)

    # Top Level: Structural building nodes
    for coord in node_coords:
        pygame.draw.circle(screen, COLOR_NODE, (coord[0], coord[1]), 14)

    # Core UI text positioning matrices
    for i, name in enumerate(node_names):
        text_surface = label_font.render(name, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(center=(node_coords[i, 0], node_coords[i, 1] - 22))
        screen.blit(text_surface, text_rect)

    # Simulation info header overlay
    title_text = f"UCSG Campus Network Infrastructure Engine — Running Time: {int(step_time)}s"
    title_surface = title_font.render(title_text, True, COLOR_TEXT)
    screen.blit(title_surface, (25, 25))

    # Real-time counter metrics banner
    active_walkers = np.sum(wait_times <= 0)
    metrics_text = f"Active Pedestrians: {active_walkers}  |  In Lecture Halls: {num_students - active_walkers}"
    metrics_surface = label_font.render(metrics_text, True, (100, 110, 120))
    screen.blit(metrics_surface, (25, 55))

    # Flush rendering frame buffer
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
