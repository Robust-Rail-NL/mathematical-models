import gc
import MILP as M
import csv
import os
from pathlib import Path
import random
import math

random.seed(1)
algo = M.solve

location = '/home/thomasverwaal/Robust-Rail-NL/mathematical-models/locations/location_solver.json'
mixed_traffic = False
time_out = 1800

GROUP_SIZE = 5

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))

scenarios = []
input_folder = Path(f"/home/thomasverwaal/Robust-Rail-NL/mathematical-models/scenarios_solver_milp/")
results_file = f"results_milp/MILP"
for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
    scenarios.append((location, file_path))

num_scenarios = len(scenarios)

start_idx = task_id * GROUP_SIZE
end_idx = min(start_idx + GROUP_SIZE, num_scenarios)


subset = scenarios[start_idx:end_idx]

print(f"Task {task_id} processing scenarios {start_idx} to {end_idx - 1}")

results_file_new = f"{results_file}_task{task_id}.csv"


with open(results_file_new, mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["num_trains", "time", "time_first_solution", "solution_found"])

  for loc, scenario in subset:
    print(f"Processing scenario {scenario}")
    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = M.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, time_first_solution, solution_found = M.solve(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_out)

    num_trains = len(agents)
    writer.writerow([num_trains, time, time, solution_found])
    
    print(f"Finished {scenario} | trains={num_trains}, k={k}, time={time}")
    del nodes, edges, conflict_edges, agents
    del x_values_filtered, p_values_filtered
    gc.collect()