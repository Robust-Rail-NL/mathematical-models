import Lagrangian as L
import MILP as M
import ADMM as A
import csv
import os
from pathlib import Path

# algo = M.solve
# algo = L.Lagrangian
algo = A.Lagrangian

location = 'locations/binckhorst.json'
input_folder = "binckhorst"
mixed_traffic = False
matching = True # If matching is false, uncomment in load_scenario.py the i in the displayname of in and out trains
rho_string = "1.99"

algo_string = "MILP"
if algo == L.Lagrangian:
  algo_string = "Lagrangian"
elif algo == A.Lagrangian:
  algo_string = "ADMM"

if matching:
  matching_string = "matching"
  input_folder = f"{input_folder}_matching"
  type = True
else:
  type = False
  matching_string = "no_matching"

if mixed_traffic:
  mixed_traffic_string = "mixed_traffic_true"
  input_folder = f"{input_folder}_mixed_traffic_true"
else:
  mixed_traffic_string = "mixed_traffic_false"
  input_folder = f"{input_folder}_mixed_traffic_false"  



results_file = f"results/{matching_string}/{algo_string}_{mixed_traffic_string}_rho{rho_string}"
solution_file = f"solutions/{matching_string}/{algo_string}_{mixed_traffic_string}_rho{rho_string}"

l_s = []
input_folder = Path(f"scenarios/{input_folder}")
print(input_folder)
i = 0
for subfolder in sorted(input_folder.iterdir(), key=lambda p: p.name):
  type = []
  for file_path in sorted(subfolder.iterdir(), key=lambda p: p.name):
    type.append((location, file_path))
  l_s.append(type)

i = 0
for sublist in l_s:
  results_file_new = f"{results_file}_types{i}.csv"
  solution_file_new = f"{solution_file}_types{i}"
  if i == 0 or i == 2 or i == 3 or i == 4 or i == 5:
    i += 1
    continue
  i += 1
  with open(results_file_new, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["num_trains", "k", "time", "time_solution"])
    for loc, scenario in sublist:
      solution_file_new2 = f"{solution_file_new}_{os.path.basename(scenario)}"
      # print(solution_file_new2)
      print(f"Processing scenario {scenario} with location {loc}")
      # print(results_file_new)
      filename = os.path.basename(scenario)
      time_solution = None
      if algo == L.Lagrangian:
        nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r, m = L.setup(loc, scenario)
        k, time = L.Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r, m)
        num_trains = len(agents)
        writer.writerow([num_trains, k, time])
      elif algo == A.Lagrangian:
        nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho = A.setup(loc, scenario)
        k, time, x_values_filtered, p_values_filtered = A.Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho)
        filename = os.path.basename(scenario)  
        num_trains = len(agents)
        writer.writerow([num_trains, k, time])
        
        with open(solution_file_new2, mode="w", newline="") as solution_file:
          solution_writer = csv.writer(solution_file)
          solution_writer.writerow(["agent", "i", "j", "t"])
          for agent, node, j, t in x_values_filtered:
            solution_writer.writerow([agent, node, j, t])
          solution_writer.writerow(["agent", "n", "t"])
          for agent, n, t in p_values_filtered:
            solution_writer.writerow([agent, n, t])
        
      elif algo == M.solve:
        nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = M.setup(loc, scenario)
        k, time, time_solution = M.solve(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types)
        num_trains = len(agents)
        writer.writerow([num_trains, k, time, time_solution])
      print(f"Finished scenario {scenario} with {num_trains} trains: k={k}, time={time}, time_solution={time_solution}")
      