# visualization.py

import pygame
import sys
import math

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (150, 150, 255)
YELLOW = (255, 255, 0)

CELL_SIZE = 40
TRAIL_LENGTH = 10

class Visualizer:
    def __init__(self, world):
        pygame.init()
        pygame.font.init()
        self.world = world
        self.size = world.grid_size * CELL_SIZE
        self.screen = pygame.display.set_mode((self.size, self.size))
        pygame.display.set_caption("Advanced Multi-Agent System")
        self.font = pygame.font.SysFont("Arial", 12)
        self.large_font = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Trail history: agent_id -> list of (x,y) screen coordinates
        self.trails = {aid: [] for aid in range(self.world.num_agents)}
        self.agent_colors = [(255, 50, 50), (50, 50, 255), (255, 165, 0), (128, 0, 128)]

    def draw_grid(self):
        for x in range(0, self.size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, self.size))
        for y in range(0, self.size, CELL_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (self.size, y))

    def draw_obstacles(self):
        for (x, y) in self.world.obstacles:
            pygame.draw.rect(
                self.screen,
                BLACK,
                (y * CELL_SIZE, x * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )

    def draw_target(self):
        x, y = self.world.target_position
        pygame.draw.rect(self.screen, GREEN, (y * CELL_SIZE, x * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        center_x = y * CELL_SIZE + CELL_SIZE // 2
        center_y = x * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, WHITE, (center_x, center_y), CELL_SIZE // 3)
        pygame.draw.circle(self.screen, GREEN, (center_x, center_y), CELL_SIZE // 4)

    def draw_paths(self, paths):
        if not paths:
            return
        for aid, path in paths.items():
            if not path or len(path) < 2:
                continue
            points = []
            for (x, y) in path:
                center_x = y * CELL_SIZE + CELL_SIZE // 2
                center_y = x * CELL_SIZE + CELL_SIZE // 2
                points.append((center_x, center_y))
            pygame.draw.lines(self.screen, LIGHT_BLUE, False, points, 2)

    def draw_trails(self):
        for aid, trail in self.trails.items():
            if len(trail) < 2:
                continue
            color = self.agent_colors[aid % len(self.agent_colors)]
            
            # Draw fading trail dots or lines
            for i, pos in enumerate(trail):
                fade_alpha = (i + 1) / len(trail)
                radius = max(1, int(4 * fade_alpha))
                # Create a faded color by interpolating with WHITE
                r = int(WHITE[0] + (color[0] - WHITE[0]) * fade_alpha)
                g = int(WHITE[1] + (color[1] - WHITE[1]) * fade_alpha)
                b = int(WHITE[2] + (color[2] - WHITE[2]) * fade_alpha)
                
                pygame.draw.circle(self.screen, (r, g, b), (int(pos[0]), int(pos[1])), radius)

    def draw_agents(self, old_positions, new_positions, alpha):
        for aid in range(self.world.num_agents):
            if aid not in old_positions or aid not in new_positions:
                continue
                
            old_x, old_y = old_positions[aid]
            new_x, new_y = new_positions[aid]
            
            cur_x = old_x + (new_x - old_x) * alpha
            cur_y = old_y + (new_y - old_y) * alpha
            
            status = self.world.agent_status[aid]
            
            center_x = int(cur_y * CELL_SIZE + CELL_SIZE / 2)
            center_y = int(cur_x * CELL_SIZE + CELL_SIZE / 2)
            
            base_color = self.agent_colors[aid % len(self.agent_colors)]
            
            if status == "BLOCKED":
                pygame.draw.circle(self.screen, GRAY, (center_x, center_y), CELL_SIZE // 3)
                pygame.draw.line(self.screen, RED, (center_x - 5, center_y - 5), (center_x + 5, center_y + 5), 2)
                pygame.draw.line(self.screen, RED, (center_x - 5, center_y + 5), (center_x + 5, center_y - 5), 2)
            else:
                pygame.draw.circle(self.screen, base_color, (center_x, center_y), CELL_SIZE // 3)
                
                # Draw directional triangle/arrow
                dx = new_x - old_x
                dy = new_y - old_y
                if dx != 0 or dy != 0:
                    angle = math.atan2(dx, dy) # Since x is row, y is col, orientation in pygame might be interesting
                    # Let's just point arrow slightly offset
                    tip_x = center_x + math.sin(angle) * (CELL_SIZE // 3)
                    tip_y = center_y + math.cos(angle) * (CELL_SIZE // 3)
                    pygame.draw.circle(self.screen, BLACK, (int(tip_x), int(tip_y)), 3)

            # Draw role text
            role = self.world.agent_roles[aid]
            text_surface = self.font.render(role, True, BLACK)
            text_rect = text_surface.get_rect(center=(center_x, center_y - CELL_SIZE // 3 - 8))
            self.screen.blit(text_surface, text_rect)

    def draw_events(self, events):
        if not events:
            return
        for idx, event_text in enumerate(events):
            text_surf = self.large_font.render(event_text, True, RED)
            rect = text_surf.get_rect(center=(self.size // 2, 30 + idx * 30))
            # Optional semi-transparent background
            bg_rect = rect.inflate(10, 10)
            pygame.draw.rect(self.screen, YELLOW, bg_rect)
            pygame.draw.rect(self.screen, RED, bg_rect, 2)
            self.screen.blit(text_surf, rect)

    def draw_metrics(self, metrics, mode):
        if not metrics:
            return
            
        texts = [
            f"MODE: {mode}",
            f"STEP: {metrics.get('steps_taken', 0)}",
            f"COLLISIONS AVOIDED: {metrics.get('collisions_avoided', 0)}",
            f"WAIT ACTIONS: {metrics.get('wait_actions', 0)}"
        ]
        
        # Draw background panel
        panel_width = 180
        panel_height = len(texts) * 20 + 10
        panel_rect = pygame.Rect(5, 5, panel_width, panel_height)
        pygame.draw.rect(self.screen, WHITE, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        
        for idx, text in enumerate(texts):
            # Emphasize the Mode
            weight = True if idx == 0 else False
            color = BLUE if idx == 0 else BLACK
            
            # Since SysFont font objects cannot be modified post creation trivially for bold, 
            # we rely on large_font or just use default
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (10, 10 + idx * 20))

    def animate_step(self, old_positions, new_positions, paths, events=None, metrics=None, mode="RULE"):
        frames = 15
        clock = pygame.time.Clock()
        
        for frame in range(frames + 1):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            alpha = frame / float(frames)
            
            self.screen.fill(WHITE)
            self.draw_grid()
            self.draw_obstacles()
            self.draw_target()
            
            if paths:
                self.draw_paths(paths)
                
            self.draw_trails()
            self.draw_agents(old_positions, new_positions, alpha)
            
            if events:
                self.draw_events(events)
                
            if metrics:
                self.draw_metrics(metrics, mode)

            pygame.display.flip()
            clock.tick(60)
            
        # Update trails after movement finishes
        for aid in range(self.world.num_agents):
            if aid in new_positions:
                pos = new_positions[aid]
                center_x = pos[1] * CELL_SIZE + CELL_SIZE // 2
                center_y = pos[0] * CELL_SIZE + CELL_SIZE // 2
                # Only add if moved or no trail exists
                if not self.trails[aid] or self.trails[aid][-1] != (center_x, center_y):
                    self.trails[aid].append((center_x, center_y))
                if len(self.trails[aid]) > TRAIL_LENGTH:
                    self.trails[aid].pop(0)

    # Fallback / Static update matching old API for the final loop
    def update(self, paths=None, events=None, metrics=None, mode="RULE"):
        self.animate_step(self.world.agent_positions, self.world.agent_positions, paths, events, metrics, mode)