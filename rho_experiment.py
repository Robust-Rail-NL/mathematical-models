import gc

import Lagrangian as L
import MILP as M
import ADMM_constraint_edges as A
import csv
import os
from pathlib import Path
import random
import math

random.seed(1)

def compute_number_of_movements(x_values):
  count = 0
  for a, i, j, t in x_values: 
    if i != j:
      count += 1
  return count

algo = A.Lagrangian

location = '/home/thomasverwaal/Robust-Rail-NL/mathematical-models/locations/location_solver.json'

rho_list = [0.1, 0.5, 1, 1.5, 2, 3]
time_out = 1800

GROUP_SIZE = 6

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))

algo_string = "ADMM"

base_results_dir = Path("results_rho_experiment")
base_results_dir.mkdir(exist_ok=True)

# --- Load scenarios ---
scenarios = []
input_folder = Path("/home/thomasverwaal/Robust-Rail-NL/mathematical-models/time_experiment_scenarios/")

for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
    scenarios.append((location, file_path))

# --- Create (scenario, rho) combinations ---
jobs = []
for loc, scenario in scenarios:
  for rho in rho_list:
    jobs.append((loc, scenario, rho))

num_jobs = len(jobs)

start_idx = task_id * GROUP_SIZE
end_idx = min(start_idx + GROUP_SIZE, num_jobs)

subset = jobs[start_idx:end_idx]

print(f"Task {task_id} processing jobs {start_idx} to {end_idx - 1}")

# --- One output file per task ---
results_file = base_results_dir/f"{algo_string}_task{task_id}.csv"

with open(results_file, mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["rho", "num_trains", "k", "time", "time_first_solution", "solution_found", "num_movements"])

  for loc, scenario, rho in subset:
    print(f"Processing scenario {scenario} with rho={rho}")

    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = A.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = A.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)

    num_trains = len(agents)
    num_movements = compute_number_of_movements(x_values_filtered)

    writer.writerow([rho, num_trains, k, time, time, solution_found, num_movements])

    print(f"Finished {scenario} | rho={rho}, trains={num_trains}, k={k}, time={time}")

    del nodes, edges, conflict_edges, agents
    del x_values_filtered, p_values_filtered
    gc.collect()