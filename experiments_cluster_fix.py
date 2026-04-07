import Lagrangian as L
import MILP as M
import ADMM_constraint_edges as A
import csv
import os
from pathlib import Path
import random
import math

random.seed(1)

def extract_type_category(file_path, num_trains):
    name = os.path.basename(file_path)

    parts = name.split("_")
    num_types = int(parts[4])

    if num_types == 1:
        return "1"
    elif num_types == 5:
        return "5"
    elif num_types == math.ceil(num_trains / 2):
        return "1/2"
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

# ================= SETTINGS =================
# algo = M.solve
# algo = L.Lagrangian
algo = A.Lagrangian

location = '/home/thomasverwaal/Robust-Rail-NL/mathematical-models/locations/location_solver.json'
input_folder = ""
mixed_traffic = False
matching = True # If matching is false, uncomment in load_scenario.py the i in the displayname of in and out trains
rho_string = "2"
rho = 2
time_out = 1800

GROUP_SIZE_ORIGINAL = 5
# GROUP_SIZE = 1

task_id = int(os.environ.get("SLURM_ARRAY_TASK_ID", 0))

algo_string = "MILP"
if algo == L.Lagrangian:
  algo_string = "Lagrangian"
elif algo == A.Lagrangian:
  algo_string = "ADMM"

if algo == A.Lagrangian:
  results_file = f"results_types/{algo_string}_rho{rho_string}"
  solution_file = f"solutions_types/{algo_string}_rho{rho_string}"
else:
  results_file = f"results_final/{algo_string}"
  solution_file = f"solutions_final/{algo_string}"


scenarios = []
input_folder = Path(f"/home/thomasverwaal/Robust-Rail-NL/mathematical-models/scenarios_solver_types/{input_folder}")

# for subfolder in sorted(input_folder.iterdir(), key=lambda p: p.name):
#   for file_path in sorted(subfolder.iterdir(), key=lambda p: p.name):
    # scenarios.append((location, file_path))
for file_path in sorted(input_folder.iterdir(), key=lambda p: p.name):
  if file_path.is_file() and file_path.suffix == ".json":
      scenarios.append((location, file_path))

num_scenarios = len(scenarios)

# scenario_id = task_id
failed_scenarios = [
1150,1151,1152,1153,1154,
1170,1171,1172,1173,1174,
1175,1176,1177,1178,1179,
1180,1181,1182,1183,1184,
1185,1186,1187,1188,1189,
1195,1196,1197,1198,1199,
1240,1241,1242,1243,1244,
1250,1251,1252,1253,1254,
1260,1261,1262,1263,1264,
1265,1266,1267,1268,1269,
1270,1271,1272,1273,1274,
1275,1276,1277,1278,1279,
1280,1281,1282,1283,1284,
1285,1286,1287,1288,1289,
1290,1291,1292,1293,1294,
1295,1296,1297,1298,1299,
1300,1301,1302,1303,1304,
1305,1306,1307,1308,1309,
1310,1311,1312,1313,1314,
1315,1316,1317,1318,1319,
1320,1321,1322,1323,1324,
1330,1331,1332,1333,1334,
1335,1336,1337,1338,1339,
1345,1346,1347,1348,1349,
1360,1361,1362,1363,1364,
1370,1371,1372,1373,1374,
1375,1376,1377,1378,1379
]

scenario_id = failed_scenarios[task_id]
if scenario_id >= num_scenarios:
    print(f"Task {task_id}: no scenario")
    exit()
subset = [scenarios[scenario_id]]
# start_idx = task_id * GROUP_SIZE
original_task_id = scenario_id // GROUP_SIZE_ORIGINAL
# end_idx = min(start_idx + GROUP_SIZE, num_scenarios)

# if start_idx >= num_scenarios:
#   print(f"Task {task_id}: no scenarios to process.")
#   exit()

# subset = scenarios[start_idx:end_idx]

print(f"Task {task_id} processing scenario {scenario_id}")
# print(f"Task {task_id} processing scenarios {start_idx} to {end_idx - 1}")

# results_file_new = f"{results_file}_task{task_id}.csv"
# solution_file_new = f"{solution_file}_task{task_id}"
results_file_new = f"{results_file}_task{original_task_id}.csv"
solution_file_new = f"{solution_file}_task{original_task_id}"

# with open(results_file_new, mode="w", newline="") as file:
file_exists = os.path.exists(results_file_new)

with open(results_file_new, mode="a", newline="") as file:
  writer = csv.writer(file)

  if not file_exists or os.path.getsize(results_file_new) == 0:
    writer.writerow(["num_trains", "type", "k", "time", "time_first_solution", "solution_found", "num_movements"])
  
  # writer = csv.writer(file)
  # # writer.writerow(["num_trains", "k", "time", "time_first_solution", "solution_found", "num_movements"])
  # writer.writerow(["num_trains", "type", "k", "time", "time_first_solution", "solution_found", "num_movements"])

  for loc, scenario in subset:
    print(f"Processing scenario {scenario}")

    solution_file_new2 = f"{solution_file_new}_{os.path.basename(scenario)}"

    if algo == A.Lagrangian:
      nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = A.setup(loc, scenario)
      k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = A.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)
    elif algo == L.Lagrangian:
      nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values = L.setup(loc, scenario)
      k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = L.Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, time_out)
    else:
      nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = M.setup(loc, scenario)
      k, time, x_values_filtered, p_values_filtered, time_first_solution, solution_found = M.solve(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_out)

    num_trains = len(agents)
    type_category = extract_type_category(scenario, num_trains)
    num_movements = compute_number_of_movements(x_values_filtered)

    # writer.writerow([num_trains, k, time, time, solution_found, num_movements])
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