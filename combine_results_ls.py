# import pandas as pd
# import re
# import os
# from glob import glob
# import math

# INPUT_FOLDER = "results_ls_discreet_120/"
# OUTPUT_FILE = "results_ls_discreet_120/combined_results.csv"
# INPUT_FOLDER = "data_types_360/results_ls_discreet/"
# OUTPUT_FILE = "data_types_360/results_ls_discreet/combined_results.csv"

# def extract_filename_info(path):
#   match = re.search(r'scenario_solver_(\d+)_trains_(\d+)_units', path)
#   return int(match.group(1)), int(match.group(2))

# def parse_time_to_seconds(timestr):
#   h, m, s = timestr.split(":")
#   return int(h)*3600 + int(m)*60 + float(s)

# def extract_sm(cost_line):
#   if not isinstance(cost_line, str):
#     return None
#   match = re.search(r'sm=(\d+)', cost_line)
#   return int(match.group(1)) if match else None

# def extract_cost(cost_line):
#   if not isinstance(cost_line, str):
#     return None
#   match = re.search(r'Cost = ([0-9.]+)', cost_line)
#   return float(match.group(1)) if match else None

# def process_file(filepath):
#   df = pd.read_csv(filepath)
#   df = df.fillna("")
#   results = []
#   high_cost_count = 0
#   for scenario, group in df.groupby("scenario"):
#     final_cost = None
#     num_trains, typ = extract_filename_info(scenario)

#     total_time = None
#     num_movements = None
#     time_first_solution = None

#     for _, row in group.iterrows():
#       cost_line = row["cost_line"]
#       time_line = row["time_line"]

#       if "Time elapsed" in time_line:
#         elapsed = float(re.search(r'([0-9.]+)', time_line).group(1))
#         cost = extract_cost(cost_line)

#         if cost == 0.0 and time_first_solution is None:
#           time_first_solution = elapsed
#         elif cost is None and time_first_solution is None:
#           time_first_solution = elapsed

#       if "Cost of solution" in cost_line:
#         num_movements = extract_sm(cost_line)
#         final_cost = extract_cost(cost_line)

#       if "Total computation time" in time_line:
#         time_str = time_line.split(": ", 1)[1]
#         total_time = parse_time_to_seconds(time_str)

#     if time_first_solution is None and total_time is not None:
#       time_first_solution = total_time

#     solution_found = total_time is not None and total_time <= 1800
#     if final_cost is not None and final_cost > 2:
#       solution_found = False
#     if final_cost is not None and final_cost > 0:
#       print(f"High cost scenario: {scenario} with cost {final_cost}")
#       high_cost_count += 1
#     results.append({
#       "num_trains": int(num_trains),
#       "type": int(typ),
#       "time": total_time,
#       "time_first_solution": time_first_solution,
#       "solution_found": solution_found,
#       "num_movements": num_movements
#     })

#   return results, high_cost_count

# all_results = []
# total_high_cost = 0

# for file in glob(os.path.join(INPUT_FOLDER, "*.csv")):
#   print(f"Processing {file}...")
#   file_results, file_high_cost = process_file(file)
#   all_results.extend(file_results)
#   total_high_cost += file_high_cost

# out_df = pd.DataFrame(all_results)
# out_df['num_trains'] = out_df['num_trains'].astype(int)
# out_df['type'] = out_df.apply(lambda row: ("num_trains" if int(row['type']) == int(row['num_trains']) else "1/3" if int(row['type']) == math.ceil(int(row['num_trains']) / 3) else row['type']), axis=1)

# def type_order(row):
#   n = int(row['num_trains'])
#   t = row['type']
#   if t == 1:
#     return 1
#   elif t == 5:
#       return 2
#   elif t == "1/3":
#     return 3
#   elif t == "num_trains":
#     return 4
#   else:
#     return 5

# out_df['type_order'] = out_df.apply(type_order, axis=1)
# out_df = out_df.sort_values(by=['num_trains', 'type_order'], ascending=True)
# out_df = out_df.drop(columns=['type_order'])

# out_df.to_csv(OUTPUT_FILE, index=False)
# print(f"Scenarios with final cost > 2: {total_high_cost}")
# print("Done! Saved to:", OUTPUT_FILE)





# import pandas as pd
# import re
# import os
# from glob import glob

# INPUT_FOLDER = "results_ls_discreet_time_20/"
# OUTPUT_FILE = "results_ls_discreet_time_20/combined_results.csv"

# def extract_filename_info(path):
#     # Extract num_trains and end_time
#     match = re.search(r'scenario_solver_(\d+)_trains_\d+_units\d+_(\d+)', path)
#     return int(match.group(1)), int(match.group(2))

# def parse_time_to_seconds(timestr):
#     h, m, s = timestr.split(":")
#     return int(h)*3600 + int(m)*60 + float(s)

# def extract_sm(cost_line):
#     if not isinstance(cost_line, str):
#         return None
#     match = re.search(r'sm=(\d+)', cost_line)
#     return int(match.group(1)) if match else None

# def extract_cost(cost_line):
#     if not isinstance(cost_line, str):
#         return None
#     match = re.search(r'Cost = ([0-9.]+)', cost_line)
#     return float(match.group(1)) if match else None

# def process_file(filepath):
#     df = pd.read_csv(filepath).fillna("")
#     results = []
#     high_cost_count = 0

#     for scenario, group in df.groupby("scenario"):
#         final_cost = None
#         num_trains, end_time = extract_filename_info(scenario)

#         total_time = None
#         num_movements = None
#         time_first_solution = None

#         for _, row in group.iterrows():
#             cost_line = row["cost_line"]
#             time_line = row["time_line"]

#             if "Time elapsed" in time_line:
#                 elapsed = float(re.search(r'([0-9.]+)', time_line).group(1))
#                 cost = extract_cost(cost_line)

#                 if cost == 0.0 and time_first_solution is None:
#                     time_first_solution = elapsed
#                 elif cost is None and time_first_solution is None:
#                     time_first_solution = elapsed

#             if "Cost of solution" in cost_line:
#                 num_movements = extract_sm(cost_line)
#                 final_cost = extract_cost(cost_line)

#             if "Total computation time" in time_line:
#                 time_str = time_line.split(": ", 1)[1]
#                 total_time = parse_time_to_seconds(time_str)

#         if time_first_solution is None and total_time is not None:
#             time_first_solution = total_time

#         solution_found = total_time is not None and total_time <= 1800
#         if final_cost is not None and final_cost > 2:
#             solution_found = False

#         if final_cost is not None and final_cost > 0:
#             print(f"High cost scenario: {scenario} with cost {final_cost}")
#             high_cost_count += 1

#         results.append({
#             "num_trains": num_trains,
#             "end_time": end_time,
#             "time": total_time,
#             "time_first_solution": time_first_solution,
#             "solution_found": solution_found,
#             "num_movements": num_movements
#         })

#     return results, high_cost_count

# # ---- MAIN ----

# all_results = []
# total_high_cost = 0

# for file in glob(os.path.join(INPUT_FOLDER, "*.csv")):
#     print(f"Processing {file}...")
#     file_results, file_high_cost = process_file(file)
#     all_results.extend(file_results)
#     total_high_cost += file_high_cost

# out_df = pd.DataFrame(all_results)

# # Ensure correct types
# out_df['num_trains'] = out_df['num_trains'].astype(int)
# out_df['end_time'] = out_df['end_time'].astype(int)

# # ✅ Sort by end_time (primary), optionally num_trains secondary
# out_df = out_df.sort_values(by=['end_time', 'num_trains'], ascending=True)

# out_df.to_csv(OUTPUT_FILE, index=False)

# print(f"Scenarios with final cost > 2: {total_high_cost}")
# print("Done! Saved to:", OUTPUT_FILE)


# import os
# import csv
# import re

# # =========================
# # INPUT FOLDERS
# # =========================
# folders = [
#   "results_ls_discreet_time_20/",
#   "data_time_20/results_ls_discreet_time_20/",
#   "data_time_20/results_ls_discreet_time_20_2/"
# ]

# output_csv = (
#   "results_ls_discreet_time_20/"
#   "combined_results_2.csv"
# )

# rows = []

# # =========================
# # PROCESS ALL FOLDERS
# # =========================
# for folder_path in folders:

#   print(f"Processing folder: {folder_path}")

#   for file in os.listdir(folder_path):

#     if not file.endswith(".csv"):
#       continue

#     if file.startswith("combined"):
#       continue

#     file_path = os.path.join(
#       folder_path,
#       file
#     )

#     scenario_data = {}

#     with open(file_path, "r", newline="") as f:

#       reader = csv.DictReader(f)

#       for row in reader:

#         scenario_path = row["scenario"]
#         cost_line = row["cost_line"]
#         time_line = row["time_line"]

#         filename = os.path.basename(
#           scenario_path
#         )

#         match = re.match(
#           r"scenario_(.+)_(\d+)\.json",
#           filename
#         )

#         if not match:
#           continue

#         extracted_name = match.group(1)
#         endtime = int(match.group(2))

#         # =========================
#         # FILTER ENDTIME
#         # =========================
#         if endtime > 6000:
#           continue

#         if filename not in scenario_data:

#           scenario_data[filename] = {
#             "filename": extracted_name,
#             "endtime": endtime,
#             "last_solution_line": None,
#             "total_computation_time": None
#           }

#         if "Cost of solution" in cost_line:

#           scenario_data[filename][
#             "last_solution_line"
#           ] = cost_line

#           time_match = re.search(
#             r"Total computation time:\s*([0-9:.]+)",
#             time_line
#           )

#           if time_match:

#             scenario_data[filename][
#               "total_computation_time"
#             ] = time_match.group(1)

#     # =========================
#     # STORE RESULTS
#     # =========================
#     for scenario in scenario_data.values():

#       last_line = scenario[
#         "last_solution_line"
#       ]

#       if (
#         last_line is not None and
#         "Cost = 0.0" in last_line
#       ):

#         rows.append({
#           "filename": scenario["filename"],
#           "found": True,
#           "endtime": scenario["endtime"],
#           "total_computation_time":
#             scenario["total_computation_time"]
#         })

# # =========================
# # WRITE OUTPUT CSV
# # =========================
# with open(output_csv, "w", newline="") as f:

#   writer = csv.DictWriter(
#     f,
#     fieldnames=[
#       "filename",
#       "found",
#       "endtime",
#       "total_computation_time"
#     ]
#   )

#   writer.writeheader()
#   writer.writerows(rows)

# print(
#   f"Saved {len(rows)} rows to "
#   f"{output_csv}"
# )

# combine results for 360 only feasible
# import os
# import csv
# import re

# # =========================
# # INPUT FOLDERS
# # =========================
# folders = [
#   "data_types_360/results_ls_discreet/",
# ]

# output_csv = (
#   "data_types_360/results_ls_discreet/"
#   "combined_results_2.csv"
# )

# rows = []

# # =========================
# # PROCESS ALL FOLDERS
# # =========================
# for folder_path in folders:

#   print(f"Processing folder: {folder_path}")

#   for file in os.listdir(folder_path):

#     if not file.endswith(".csv"):
#       continue

#     if file.startswith("combined"):
#       continue

#     file_path = os.path.join(
#       folder_path,
#       file
#     )

#     scenario_data = {}

#     with open(file_path, "r", newline="") as f:

#       reader = csv.DictReader(f)

#       for row in reader:

#         scenario_path = row["scenario"]
#         cost_line = row["cost_line"]
#         time_line = row["time_line"]

#         filename = os.path.basename(
#           scenario_path
#         )

#         # =========================
#         # EXTRACT SCENARIO NAME
#         # =========================
#         match = re.match(
#           r"(scenario_solver_\d+_trains_\d+_units\d+)\.json",
#           filename
#         )

#         if not match:
#           continue

#         extracted_name = match.group(1)

#         if filename not in scenario_data:

#           scenario_data[filename] = {
#             "filename": extracted_name,
#             "last_solution_line": None,
#             "total_computation_time": None
#           }

#         # =========================
#         # STORE SOLUTION INFO
#         # =========================
#         if "Cost of solution" in cost_line:

#           scenario_data[filename][
#             "last_solution_line"
#           ] = cost_line

#           time_match = re.search(
#             r"Total computation time:\s*([0-9:.]+)",
#             time_line
#           )

#           if time_match:

#             scenario_data[filename][
#               "total_computation_time"
#             ] = time_match.group(1)

#     # =========================
#     # STORE RESULTS
#     # =========================
#     for scenario in scenario_data.values():

#       last_line = scenario[
#         "last_solution_line"
#       ]

#       if (
#         last_line is not None and
#         "Cost = 0.0" in last_line
#       ):

#         rows.append({
#           "filename": scenario["filename"],
#           "found": True,
#           "total_computation_time":
#             scenario["total_computation_time"]
#         })

# # =========================
# # WRITE OUTPUT CSV
# # =========================
# with open(output_csv, "w", newline="") as f:

#   writer = csv.DictWriter(
#     f,
#     fieldnames=[
#       "filename",
#       "found",
#       "total_computation_time"
#     ]
#   )

#   writer.writeheader()
#   writer.writerows(rows)

# print(
#   f"Saved {len(rows)} rows to "
#   f"{output_csv}"
# )