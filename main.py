# main.py

from world import World
from coordination import Coordinator
from pathfinding import astar
from visualization import Visualizer
import time

MODE = "PREDICT"  # options: "RULE", "PREDICT"

# ==========================================
# DECISION LAYER
# ==========================================
def decide_next_move(aid, start, goal, world, predicted_positions, mode):
    """
    Returns next step using A* and the full path.
    If mode is PREDICT, includes lightweight prediction to preemptively avoid occupied cells.
    No collision logic here (handled by Coordinator).
    """
    path = astar(start, goal, world)

    if len(path) > 1:
        next_step = path[1]
        
        # PREDICTION AWARENESS
        if mode == "PREDICT":
            # If another agent is already predicted to move here, try to wait instead
            if next_step in predicted_positions:
                return start, path
            
        return next_step, path
        
    return start, path


# ==========================================
# MAIN SIMULATION
# ==========================================
import config

w = World()
w.generate_environment()
coord = Coordinator(w)
vis = Visualizer(w)

print(f"\nENVIRONMENT TYPE: {getattr(config, 'ENV_TYPE', 'UNKNOWN')}")

metrics = {
    'steps_taken': 0,
    'collisions_avoided': 0,
    'wait_actions': 0,
    'task_completed': False
}

# Provide an initial trail sync
vis.update(metrics=metrics, mode=MODE)

# Run simulation
MAX_STEPS = 1000
for step in range(MAX_STEPS):
    print(f"\n--- STEP {step} ---")
    metrics['steps_taken'] += 1
    
    events = []

    # 1. Update failures
    coord.update_failures()

    # 2. Allocate tasks
    coord.allocate_tasks()

    # 3. Simulate failure at step 5
    if step == 5:
        print("\n*** FAILURE EVENT: Agent 1 ***")
        coord.handle_agent_failure(1)
        events.append("AGENT FAILURE DETECTED: Agent 1")

    # 4. Decide movements with Mode Handling
    intended_actions = {}
    paths = {}
    predicted_positions = set()

    for aid in w.get_active_agents():
        start = w.agent_positions[aid]
        role = w.agent_roles[aid]

        # Role-based goal assignment
        if role == "PRIMARY_CARRIER":
            goal = w.target_position

        elif role == "SECONDARY_CARRIER":
            goal = (max(0, min(w.grid_size - 1, w.target_position[0] - 1)),
                    w.target_position[1])

        elif role == "SCOUT":
            goal = (w.target_position[0],
                    max(0, min(w.grid_size - 1, w.target_position[1] - 2)))

        else:
            goal = w.target_position

        # Decision layer returns both next_step and the path
        next_step, path = decide_next_move(aid, start, goal, w, predicted_positions, MODE)

        print(f"Agent {aid}: {start} -> {next_step}")

        intended_actions[aid] = next_step
        paths[aid] = path
        if next_step != start:
            predicted_positions.add(next_step)

    # 5. Resolve collisions
    safe_actions = coord.resolve_collisions(intended_actions)
    
    # Analyze metrics
    for aid in safe_actions:
        if aid in intended_actions:
            if intended_actions[aid] != safe_actions[aid]:
                metrics['collisions_avoided'] += 1

        if safe_actions[aid] == w.agent_positions[aid]:
            metrics['wait_actions'] += 1

    # 6. Capture old positions for animation
    old_positions = {aid: pos for aid, pos in w.agent_positions.items()}

    # 7. Update positions
    w.update_positions(safe_actions)

    # Check for joint task completion
    if w.check_joint_task_complete():
        metrics['task_completed'] = True
        events.append("TASK COMPLETED!")
        print("TASK COMPLETED SUCCESSFULLY")

    # 8. Print state
    w.print_state()

    # 9. Update visualization with smooth animation and metrics
    new_positions = {aid: pos for aid, pos in w.agent_positions.items()}
    vis.animate_step(old_positions, new_positions, paths, events, metrics, MODE)

    if metrics['task_completed']:
        break

# ==========================================
# METRICS AND END
# ==========================================
print("\n===== FINAL RESULTS =====")
print(f"Mode: {MODE}")
print(f"Task Completed: {'YES' if metrics['task_completed'] else 'NO'}")
print(f"Steps Taken: {metrics['steps_taken']}")
print(f"Collisions Avoided: {metrics['collisions_avoided']}")
print(f"Wait Actions: {metrics['wait_actions']}")

optimal_steps = 22 # Manhattan dist from (1,1) to (12,12)
efficiency = optimal_steps / metrics['steps_taken'] if metrics['steps_taken'] > 0 else 0
coordination_score = 1 / (1 + metrics['wait_actions'])
print(f"Efficiency: {efficiency:.4f}")
print(f"Coordination Score: {coordination_score:.4f}")
print("=========================")

print("\nSimulation finished. Close window to exit.")

while True:
    vis.update(metrics=metrics, mode=MODE)