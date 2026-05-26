import gc
import Lagrangian as L
import MILP as M
import ADMM_constraint_edges as A
import shortest_path as SP
import shortest_path_continuous as SPc
import csv
import os
from pathlib import Path
import random
import math

# Imports need to be fixed

random.seed(1)

def extract_type_category(file_path, num_trains):
    name = os.path.basename(file_path)

    parts = name.split("_")
    num_types = int(parts[4])

    if num_types == 1:
        return "1"
    elif num_types == 5:
        return "5"
    elif num_types == math.ceil(num_trains / 3):
        return "1/3"
    elif num_types == math.ceil(num_trains):
        return str(num_trains)
    else:
        return "unknown"

def compute_number_of_movements(x_values):
  count = 0
  for a, i, j, t in x_values: 
    if i != j:
      count += 1
  return count

algo = SPc.Lagrangian

location = '../../data/locations/location_solver.json'
rho_string = "0.5"
algo_string = "sp"
rho = 0.5
time_out = 1800

GROUP_SIZE = 5

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))


scenarios = []
input_folder = Path(f"../../data_types_7hours/scenarios_solver/")

# Folders to store results and solutions
results_file = f"results_360_sp_c/{algo_string}_rho{rho_string}"
solution_file = f"solutions_360_sp_c/{algo_string}_rho{rho_string}"

for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
    scenarios.append((location, file_path))

num_scenarios = len(scenarios)

start_idx = task_id * GROUP_SIZE
end_idx = min(start_idx + GROUP_SIZE, num_scenarios)

subset = scenarios[start_idx:end_idx]

print(f"Task {task_id} processing scenarios {start_idx} to {end_idx - 1}")

results_file_new = f"{results_file}_task{task_id}.csv"
solution_file_new = f"{solution_file}_task{task_id}"

with open(results_file_new, mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["num_trains", "type", "k", "time", "time_first_solution", "solution_found", "num_movements"])

  for loc, scenario in subset:
    print(f"Processing scenario {scenario}")

    solution_file_new2 = f"{solution_file_new}_{os.path.basename(scenario)}"
    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes, node_to_idx, edge_to_idx, agent_to_idx, edge_group_matrix = SPc.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = SPc.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho=0.5, time_out=1800, macro_edge_nodes=macro_edge_nodes, node_to_idx=node_to_idx, edge_to_idx=edge_to_idx, agent_to_idx=agent_to_idx, edge_group_matrix=edge_group_matrix) 

    num_trains = len(agents)
    type_category = extract_type_category(scenario, num_trains)
    num_movements = compute_number_of_movements(x_values_filtered)
    
    writer.writerow([num_trains, type_category, k, time, time, solution_found, num_movements])

    with open(solution_file_new2, mode="w", newline="") as s_file:
      solution_writer = csv.writer(s_file)

      solution_writer.writerow(["agent", "i", "j", "t"])
      for agent, node, j, t in x_values_filtered:
        solution_writer.writerow([agent, node, j, t])

      solution_writer.writerow(["agent", "n", "t"])
      for agent, n, t in p_values_filtered:
        solution_writer.writerow([agent, n, t])

      if algo != M.solve:
        solution_writer.writerow(["conflicts", "time"])
        for conflicts, conflict_time in conflict_list:
          solution_writer.writerow([conflicts, conflict_time])
      
      solution_writer.writerow(["found"])
      solution_writer.writerow([solution_found])

    print(f"Finished {scenario} | trains={num_trains}, k={k}, time={time}")
    del nodes, edges, conflict_edges, agents
    del x_values_filtered, p_values_filtered
    gc.collect()