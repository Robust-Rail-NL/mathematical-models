import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src", "gurobi"))

import gc
import Lagrangian as L
import MILP as M
import ADMM as A
import shortest_path as SP
import shortest_path_continuous as SPC
import csv
from pathlib import Path
import random

random.seed(1)

def extract_end_time(file_path):
    name = os.path.basename(file_path)
    name = name.replace(".json", "")
    parts = name.split("_")
    
    # last part is the end time
    end_time = int(parts[-1])
    return end_time


def compute_number_of_movements(x_values):
  count = 0
  for a, i, j, t in x_values: 
    if i != j:
      count += 1
  return count

algo = SPC.Lagrangian
location = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "locations", "location_solver.json")
rho_string = "0.5"
algo_string = "sp"
rho = 0.5
time_out = 1800

GROUP_SIZE = 5

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))


scenarios = []
input_folder = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "data_time_window", "scenarios_solver"))

for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
    scenarios.append((location, file_path))

num_scenarios = len(scenarios)

start_idx = task_id * GROUP_SIZE
end_idx = min(start_idx + GROUP_SIZE, num_scenarios)

subset = scenarios[start_idx:end_idx]

print(f"Task {task_id} processing scenarios {start_idx} to {end_idx - 1}")

# Folders to store results and solutions
output_folder = os.path.join(os.path.dirname(__file__), "output")
result_folder = os.path.join(output_folder, "results_time_window_sp_continuous")
solution_folder = os.path.join(output_folder, "solutions_time_window_sp_continuous")
results_file = os.path.join(result_folder, f"{algo_string}_rho{rho_string}_task{task_id}.csv")
solution_file = os.path.join(solution_folder, f"{algo_string}_rho{rho_string}_task{task_id}")
os.makedirs(result_folder, exist_ok=True)
os.makedirs(solution_folder, exist_ok=True)

with open(results_file, mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["num_trains", "end_time", "k", "time", "time_first_solution", "solution_found", "num_movements"])

  for loc, scenario in subset:
    print(f"Processing scenario {scenario}")

    current_solution_file = f"{solution_file}_{os.path.basename(scenario)}.csv"
    # nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = SP.setup(loc, scenario)
    nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes, node_to_idx, edge_to_idx, agent_to_idx, edge_group_matrix = SPC.setup(loc, scenario)
    k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = SPC.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out, macro_edge_nodes=macro_edge_nodes, node_to_idx=node_to_idx, edge_to_idx=edge_to_idx, agent_to_idx=agent_to_idx, edge_group_matrix=edge_group_matrix)

    num_trains = len(agents)
    end_time_val = extract_end_time(scenario)
    num_movements = compute_number_of_movements(x_values_filtered)
    
    writer.writerow([num_trains, end_time_val, k, time, time, solution_found, num_movements])

    with open(current_solution_file, mode="w", newline="") as s_file:
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