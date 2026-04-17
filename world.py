# world.py
# Central environment state for multi-agent system

import config
import random

class World:
    def __init__(self):
        # ==========================================
        # BASIC SETTINGS
        # ==========================================
        self.grid_size = 15
        self.num_agents = 3

        # ==========================================
        # AGENT STATE
        # ==========================================
        self.agent_positions = {
            0: (1, 1),
            1: (2, 2),
            2: (3, 3)
        }

        self.agent_roles = {
            0: "UNASSIGNED",
            1: "UNASSIGNED",
            2: "UNASSIGNED"
        }

        self.agent_status = {
            0: config.STATUS_ACTIVE,
            1: config.STATUS_ACTIVE,
            2: config.STATUS_ACTIVE
        }

        # ==========================================
        # TARGETS AND BASES (MULTI-STAGE)
        # ==========================================
        self.target_position = (12, 12) # Kept for backward compatibility calculation
        
        self.scout_target = (12, 10)
        self.secondary_target = (11, 12)
        self.primary_target = (12, 12)
        
        self.completed_destination = (0, 14) # Destination for non-primary bots
        self.final_destination = (14, 14)    # Destination for the primary bot

        self.agent_stages = {
            0: "WORKING",
            1: "WORKING",
            2: "WORKING"
        }

        # ==========================================
        # OBSTACLES
        # ==========================================
        self.obstacles = set([
            (5, 5), (5, 6), (5, 7),
            (8, 8), (9, 8)
        ])

    # ==========================================
    # ENVIRONMENT GENERATION
    # ==========================================
    def get_random_free_cell(self):
        while True:
            r = random.randint(0, self.grid_size - 1)
            c = random.randint(0, self.grid_size - 1)
            pos = (r, c)
            if pos not in self.obstacles and pos not in self.agent_positions.values():
                if pos != getattr(self, 'target_position', None):
                    return pos

    def generate_environment(self):
        self.obstacles = set()
        self.agent_positions = {}
        self.target_position = None
        
        env_type = getattr(config, "ENV_TYPE", "EMPTY")
        density = getattr(config, "OBSTACLE_DENSITY", 0.0)

        if env_type == "DENSE":
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if random.random() < density:
                        self.obstacles.add((r, c))
                        
        elif env_type == "CORRIDOR":
            for c in range(self.grid_size):
                if c % 3 != 0:
                    for r in range(self.grid_size):
                        if random.random() > 0.1:
                            self.obstacles.add((r, c))
                            
        elif env_type == "RANDOM":
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if random.random() < density:
                        self.obstacles.add((r, c))
                        if random.random() < 0.5:
                            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                                if 0 <= r+dr < self.grid_size and 0 <= c+dc < self.grid_size:
                                    self.obstacles.add((r+dr, c+dc))

        # Assign agents to free cells
        for aid in range(self.num_agents):
            self.agent_positions[aid] = self.get_random_free_cell()
            
        # Assign target to a free cell
        self.target_position = self.get_random_free_cell()
        
        # Ensure the target cell neighborhood has some breathing room
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0), (0,0), (1,1), (-1,-1)]:
            t_r, t_c = self.target_position[0] + dr, self.target_position[1] + dc
            if (t_r, t_c) in self.obstacles:
                self.obstacles.remove((t_r, t_c))

    # ==========================================
    # GET ACTIVE AGENTS
    # ==========================================
    def get_active_agents(self):
        return [
            aid for aid in self.agent_status
            if self.agent_status[aid] == config.STATUS_ACTIVE
        ]

    # ==========================================
    # CHECK VALID POSITION
    # ==========================================
    def is_valid_position(self, pos):
        x, y = pos

        # Check grid bounds
        if x < 0 or y < 0 or x >= self.grid_size or y >= self.grid_size:
            return False

        # Check obstacle
        if pos in self.obstacles:
            return False

        return True

    # ==========================================
    # GET LOCAL VIEW (LIMITED VISIBILITY)
    # ==========================================
    def get_local_view(self, agent_id, radius=2):
        if agent_id not in self.agent_positions:
            return None
            
        cx, cy = self.agent_positions[agent_id]
        
        visible_cells = set()
        local_obstacles = set()
        local_agents = {}
        
        for x in range(cx - radius, cx + radius + 1):
            for y in range(cy - radius, cy + radius + 1):
                if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                    pos = (x, y)
                    visible_cells.add(pos)
                    if pos in self.obstacles:
                        local_obstacles.add(pos)
                        
        for aid, pos in self.agent_positions.items():
            if aid != agent_id and pos in visible_cells:
                local_agents[aid] = pos
                
        return {
            'center': (cx, cy),
            'radius': radius,
            'visible_cells': visible_cells,
            'local_obstacles': local_obstacles,
            'local_agents': local_agents
        }

    # ==========================================
    # UPDATE POSITIONS (after collision resolution)
    # ==========================================
    def update_positions(self, safe_actions):
        for aid, pos in safe_actions.items():
            if self.is_valid_position(pos):
                self.agent_positions[aid] = pos

    # ==========================================
    # CHECK JOINT TASK COMPLETE
    # ==========================================
    def check_joint_task_complete(self):
        primary_aid = None
        secondary_aid = None
        
        for aid, role in self.agent_roles.items():
            if role == "PRIMARY_CARRIER":
                primary_aid = aid
            elif role == "SECONDARY_CARRIER":
                secondary_aid = aid
                
        if primary_aid is None or secondary_aid is None:
            return False
            
        if self.agent_status.get(primary_aid) != config.STATUS_ACTIVE or \
           self.agent_status.get(secondary_aid) != config.STATUS_ACTIVE:
            return False

        primary_pos = self.agent_positions.get(primary_aid)
        secondary_pos = self.agent_positions.get(secondary_aid)
        
        if not primary_pos or not secondary_pos:
            return False
            
        if primary_pos != self.target_position:
            return False
            
        manhattan_dist = abs(secondary_pos[0] - self.target_position[0]) + abs(secondary_pos[1] - self.target_position[1])
        return manhattan_dist <= 1

    # ==========================================
    # RESET WORLD (optional for testing/RL)
    # ==========================================
    def reset(self):
        self.agent_positions = {
            0: (1, 1),
            1: (2, 2),
            2: (3, 3)
        }

        self.agent_roles = {
            0: "UNASSIGNED",
            1: "UNASSIGNED",
            2: "UNASSIGNED"
        }

        self.agent_status = {
            0: config.STATUS_ACTIVE,
            1: config.STATUS_ACTIVE,
            2: config.STATUS_ACTIVE
        }

        self.target_position = (12, 12)
        
        self.agent_stages = {
            0: "WORKING",
            1: "WORKING",
            2: "WORKING"
        }

    # ==========================================
    # PRINT STATE (DEBUGGING)
    # ==========================================
    def print_state(self):
        print("\nWORLD STATE:")
        for aid in range(self.num_agents):
            print(f"Agent {aid}: Pos={self.agent_positions[aid]}, "
                  f"Role={self.agent_roles[aid]}, "
                  f"Status={self.agent_status[aid]}")
        print(f"Target: {self.target_position}")