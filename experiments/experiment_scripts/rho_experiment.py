import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src", "gurobi"))

import gc
from pathlib import Path
import shortest_path as SP
import Lagrangian as L
import MILP as M
import csv
from pathlib import Path
import random

random.seed(1)

def compute_number_of_movements(x_values):
  count = 0
  for a, i, j, t in x_values: 
    if i != j:
      count += 1
  return count

algo = SP.Lagrangian

location = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "locations", "location_solver.json")

# rho_list = [0.1, 0.5, 1, 1.5, 2, 3]
n_list = [0.1, 0.5, 1, 1.5, 2, 3]
rho = 0.5
time_out = 1800

GROUP_SIZE = 6

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))

algo_string = "ADMM"

# --- Load scenarios ---
scenarios = []
input_folder = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "data_rho_n", "scenarios_solver"))

for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
    scenarios.append((location, file_path))

# --- Create (scenario, rho) combinations ---
jobs = []
for loc, scenario in scenarios:
  for n in n_list:
    jobs.append((loc, scenario, n))

num_jobs = len(jobs)

start_idx = task_id * GROUP_SIZE
end_idx = min(start_idx + GROUP_SIZE, num_jobs)

subset = jobs[start_idx:end_idx]

print(f"Task {task_id} processing jobs {start_idx} to {end_idx - 1}")

# --- One output file per task ---

# Folders to store results and solutions
output_folder = os.path.join(os.path.dirname(__file__), "output")
result_folder = os.path.join(output_folder, "results_360_sp_c")
results_file = os.path.join(result_folder, f"{algo_string}_task{task_id}.csv")
os.makedirs(result_folder, exist_ok=True)

with open(results_file, mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["n", "num_trains", "k", "time", "time_first_solution", "solution_found", "num_movements"])

  for loc, scenario, n in subset:
    print(f"Processing scenario {scenario} with n={n}")

    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = SP.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = SP.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)

    num_trains = len(agents)
    num_movements = compute_number_of_movements(x_values_filtered)

    writer.writerow([n, num_trains, k, time, time, solution_found, num_movements])

    print(f"Finished {scenario} | n={n}, trains={num_trains}, k={k}, time={time}")

    del nodes, edges, conflict_edges, agents
    del x_values_filtered, p_values_filtered
    gc.collect()