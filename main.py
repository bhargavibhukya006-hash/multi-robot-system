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
w = World()
coord = Coordinator(w)
vis = Visualizer(w)

metrics = {
    'steps_taken': 0,
    'collisions_avoided': 0,
    'wait_actions': 0
}

# Provide an initial trail sync
vis.update(metrics=metrics, mode=MODE)

# Run simulation
step = 0
while True:
    print(f"\n--- STEP {step} ---")
    metrics['steps_taken'] += 1
    
    events = []

    # 1. Allocate tasks only on the first step
    if step == 0:
        coord.allocate_tasks()

    # 2. Simulate failure at step 5
    if step == 5:
        print("\n*** FAILURE EVENT: Agent 1 ***")
        coord.handle_agent_failure(1)
        events.append("AGENT FAILURE DETECTED: Agent 1")

    # 3. Decide movements with Mode Handling
    intended_actions = {}
    paths = {}
    predicted_positions = set()

    for aid in w.get_active_agents():
        start = w.agent_positions[aid]
        role = w.agent_roles[aid]

        # Role-based multi-stage goal assignment
        if role == "PRIMARY_CARRIER":
            if start == w.primary_target:
                w.agent_stages[aid] = "FINISHED"
            goal = w.primary_target if w.agent_stages[aid] == "WORKING" else w.final_destination

        elif role == "SECONDARY_CARRIER":
            if start == w.secondary_target:
                w.agent_stages[aid] = "FINISHED"
            goal = w.secondary_target if w.agent_stages[aid] == "WORKING" else w.completed_destination

        elif role == "SCOUT":
            if start == w.scout_target:
                w.agent_stages[aid] = "FINISHED"
            goal = w.scout_target if w.agent_stages[aid] == "WORKING" else w.completed_destination

        else:
            goal = w.target_position

        # Decision layer returns both next_step and the path
        next_step, path = decide_next_move(aid, start, goal, w, predicted_positions, MODE)

        print(f"Agent {aid}: {start} -> {next_step}")

        intended_actions[aid] = next_step
        paths[aid] = path
        if next_step != start:
            predicted_positions.add(next_step)

    # 4. Resolve collisions
    safe_actions = coord.resolve_collisions(intended_actions)
    
    # Analyze metrics
    for aid in safe_actions:
        if aid in intended_actions:
            if intended_actions[aid] != safe_actions[aid]:
                metrics['collisions_avoided'] += 1

        if safe_actions[aid] == w.agent_positions[aid]:
            metrics['wait_actions'] += 1

    # 5. Capture old positions for animation
    old_positions = {aid: pos for aid, pos in w.agent_positions.items()}

    # 6. Update positions
    w.update_positions(safe_actions)

    # 7. Print state
    w.print_state()

    # 8. Update visualization with smooth animation and metrics
    new_positions = {aid: pos for aid, pos in w.agent_positions.items()}
    vis.animate_step(old_positions, new_positions, paths, events, metrics, MODE)

    # Check if everyone is at their final parking spot
    all_finished = True
    for aid in w.get_active_agents():
        pos = w.agent_positions[aid]
        role = w.agent_roles[aid]
        if role == "PRIMARY_CARRIER" and pos != w.final_destination:
            all_finished = False
        elif role in ["SECONDARY_CARRIER", "SCOUT"] and pos != w.completed_destination:
            all_finished = False

    if all_finished and step > 5:
        break
        
    step += 1

# ==========================================
# METRICS AND END
# ==========================================
print("\n===== METRICS =====")
print(f"Mode: {MODE}")
print(f"Steps: {metrics['steps_taken']}")
print(f"Collisions Avoided: {metrics['collisions_avoided']}")
print(f"Wait Actions: {metrics['wait_actions']}")
print("===================")

print("\nSimulation finished. Close window to exit.")

while True:
    vis.update(metrics=metrics, mode=MODE)