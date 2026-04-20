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
rho_string = "2"
rho = 2
time_out = 3600

GROUP_SIZE = 5

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))

algo_string = "ADMM"

results_file = f"results_time_experiment/{algo_string}_rho{rho_string}"

scenarios = []
input_folder = Path(f"/home/thomasverwaal/Robust-Rail-NL/mathematical-models/time_experiment_scenarios/")

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
  # writer.writerow(["num_trains", "k", "time", "time_first_solution", "solution_found", "num_movements"])
  writer.writerow(["num_trains", "k", "time", "time_first_solution", "solution_found",
                   "num_movements", "total_model_creation_time", "solve_time_total", "admm_update_time_total", "lr_update_time_total"])

  for loc, scenario in subset:
    print(f"Processing scenario {scenario}")


    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = A.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list, total_model_creation_time, solve_time_total, admm_update_time_total, lr_update_time_total = A.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)

    num_trains = len(agents)
    num_movements = compute_number_of_movements(x_values_filtered)

    # writer.writerow([num_trains, k, time, time, solution_found, num_movements])
    writer.writerow([num_trains, k, time, time, solution_found, num_movements,
                     total_model_creation_time, solve_time_total, admm_update_time_total, lr_update_time_total])

    print(f"Finished {scenario} | trains={num_trains}, k={k}, time={time}")
    del nodes, edges, conflict_edges, agents
    del x_values_filtered, p_values_filtered
    gc.collect()