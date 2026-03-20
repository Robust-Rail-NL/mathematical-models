import Lagrangian as L
import MILP as M
import ADMM_constraint_edges as A
import csv
import os
from pathlib import Path
import random

random.seed(1)

def compute_number_of_movements(x_values):
  count = 0
  for a, i, j, t in x_values: 
    if i != j:
      count += 1
  return count

# algo = M.solve
# algo = L.Lagrangian
algo = A.Lagrangian

location = 'locations/location_solver.json'
input_folder = ""
# mixed_traffic = False
matching = True # If matching is false, uncomment in load_scenario.py the i in the displayname of in and out trains
rho_string = "2"
rho = 2
time_out = 600

algo_string = "MILP"
if algo == L.Lagrangian:
  algo_string = "Lagrangian"
elif algo == A.Lagrangian:
  algo_string = "ADMM"

# if matching:
#   matching_string = "matching"
#   # input_folder = f"{input_folder}_matching"
#   type = True
# else:
#   type = False
#   matching_string = "no_matching"

# if mixed_traffic:
#   mixed_traffic_string = "mixed_traffic_true"
#   # input_folder = f"{input_folder}_mixed_traffic_true"
# else:
#   mixed_traffic_string = "mixed_traffic_false"
#   # input_folder = f"{input_folder}_mixed_traffic_false"  

# results_file = f"results/{matching_string}/{algo_string}_{mixed_traffic_string}_rho{rho_string}"
# solution_file = f"solutions/{matching_string}/{algo_string}_{mixed_traffic_string}_rho{rho_string}"

if algo == A.Lagrangian:
  results_file = f"results_final/{algo_string}_rho{rho_string}"
  solution_file = f"solutions_final/{algo_string}_rho{rho_string}"
else:
  results_file = f"results_final/{algo_string}"
  solution_file = f"solutions_final/{algo_string}"

l_s = []
# input_folder = Path(f"scenarios/{input_folder}")
input_folder = Path(f"scenarios_final/{input_folder}")
print(input_folder)
i = 0
for subfolder in sorted(input_folder.iterdir(), key=lambda p: p.name):
  type = []
  for file_path in sorted(subfolder.iterdir(), key=lambda p: p.name):
    type.append((location, file_path))
  l_s.append(type)

print(l_s)
i = 0
# for i, sublist in enumerate(l_s):
#   print(i)
#   results_file_new = f"{results_file}_types{i}.csv"
#   solution_file_new = f"{solution_file}_types{i}"
#   print(f"\n=== Type {i} ===")
#   print(f"Results would be written to: {results_file_new}")
#   print(f"Solutions would be written to: {solution_file_new}")
  
#   for loc, scenario in sublist:
#     scenario_name = os.path.basename(scenario)
#     solution_file_new2 = f"{solution_file_new}_{scenario_name}"
#     print(f"Scenario: {scenario}")
#     print(f"Location: {loc}")
#     print(f"Solution file (would be): {solution_file_new2}")
#     print(f"Algorithm to run: {algo_string}")
for sublist in l_s:
  results_file_new = f"{results_file}_types{i}.csv"
  solution_file_new = f"{solution_file}_types{i}"
  i += 1
  with open(results_file_new, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["num_trains", "k", "time", "time_first_solution", "solution_found", "num_movements"])
    for loc, scenario in sublist:
      print(f"Processing scenario {scenario}")
      
      solution_file_new2 = f"{solution_file_new}_{os.path.basename(scenario)}"
      # print(solution_file_new2)
      # print(results_file_new)
      filename = os.path.basename(scenario)
      time_solution = None
      if algo == L.Lagrangian:
        nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values = L.setup(loc, scenario)
        k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = L.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, time_out)
        num_trains = len(agents)
        num_movements = compute_number_of_movements(x_values_filtered)
        writer.writerow([num_trains, k, time, time, solution_found, num_movements])
        
        with open(solution_file_new2, mode="w", newline="") as s_file:
          solution_writer = csv.writer(s_file)
          solution_writer.writerow(["agent", "i", "j", "t"])
          for agent, node, j, t in x_values_filtered:
            solution_writer.writerow([agent, node, j, t])
          solution_writer.writerow(["agent", "n", "t"])
          for agent, n, t in p_values_filtered:
            solution_writer.writerow([agent, n, t])
          solution_writer.writerow(["conflicts", "time"])
          for conflicts, conflict_time in conflict_list:
            solution_writer.writerow([conflicts, conflict_time])
      elif algo == A.Lagrangian:
        nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = A.setup(loc, scenario)
        k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = A.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)
        filename = os.path.basename(scenario)  
        num_trains = len(agents)
        num_movements = compute_number_of_movements(x_values_filtered)
        writer.writerow([num_trains, k, time, time, solution_found, num_movements])
        
        with open(solution_file_new2, mode="w", newline="") as s_file:
          solution_writer = csv.writer(s_file)
          solution_writer.writerow(["agent", "i", "j", "t"])
          for agent, node, j, t in x_values_filtered:
            solution_writer.writerow([agent, node, j, t])
          solution_writer.writerow(["agent", "n", "t"])
          for agent, n, t in p_values_filtered:
            solution_writer.writerow([agent, n, t])
          solution_writer.writerow(["conflicts", "time"])
          for conflicts, conflict_time in conflict_list:
            solution_writer.writerow([conflicts, conflict_time])
      elif algo == M.solve:
        nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = M.setup(loc, scenario)
        k, time, x_values_filtered, p_values_filtered, time_first_solution, solution_found = M.solve(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_out)
        num_trains = len(agents)
        num_movements = compute_number_of_movements(x_values_filtered)
        writer.writerow([num_trains, k, time, time_first_solution, solution_found, num_movements])
        
        with open(solution_file_new2, mode="w", newline="") as s_file:
          solution_writer = csv.writer(s_file)
          solution_writer.writerow(["agent", "i", "j", "t"])
          for agent, node, j, t in x_values_filtered:
            solution_writer.writerow([agent, node, j, t])
          solution_writer.writerow(["agent", "n", "t"])
          for agent, n, t in p_values_filtered:
            solution_writer.writerow([agent, n, t])
        
      print(f"Finished scenario {scenario} with {num_trains} trains: k={k}, time={time}, time_solution={time_solution}")
      