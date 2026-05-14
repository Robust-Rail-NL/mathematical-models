# import os
# import csv

# input_folder = "results_360_sp_c"
# output_file = "results_360_sp_c/combined_results.csv"

# type_order = {
#   "1": 0,
#   "5": 1,
#   "1/3": 2,
#   "num_trains": 3
# }

# all_rows = []
# header = None

# for filename in os.listdir(input_folder):
#   if filename.startswith("combined"):
#     continue
#   if filename.endswith(".csv"):
#     filepath = os.path.join(input_folder, filename)
#     with open(filepath, "r", newline="") as f:
#       reader = csv.reader(f)
#       rows = list(reader)
#       if len(rows) <= 1:
#         continue
#       if header is None:
#         header = rows[0]
#       for row in rows[1:]:
#         if row == header:
#           continue
#         num_trains = int(row[0])
#         if num_trains == 5:
#           print(filename)
#         type_val = row[1]
#         if type_val.isdigit() and int(type_val) == num_trains:
#           row[1] = "num_trains"
#         all_rows.append(row)

# def sort_key(row):
#   num_trains = int(row[0])
#   type_val = row[1]
#   return (num_trains, type_order.get(type_val, 999))

# all_rows.sort(key=sort_key)

# with open(output_file, "w", newline="") as f:
#   writer = csv.writer(f)
#   writer.writerow(header)
#   writer.writerows(all_rows)

# print(f"Combined file written to {output_file}")

# import os
# import csv

# input_folder = "results_rho_experiment"
# output_file = "results_rho_experiment/combined_results.csv"

# all_rows = []
# header = None

# for filename in os.listdir(input_folder):
#     if filename.startswith("combined"):
#         continue
#     if filename.endswith(".csv"):
#         filepath = os.path.join(input_folder, filename)
#         with open(filepath, "r", newline="") as f:
#             reader = csv.reader(f)
#             rows = list(reader)

#             if len(rows) <= 1:
#                 continue

#             if header is None:
#                 header = rows[0]

#             for row in rows[1:]:
#                 if row == header:
#                     continue
#                 all_rows.append(row)

# # Sort by rho (column 0, float)
# def sort_key(row):
#     return float(row[0])

# all_rows.sort(key=sort_key)

# with open(output_file, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(header)
#     writer.writerows(all_rows)

# print(f"Combined file written to {output_file}")


# import os
# import csv
# from collections import defaultdict

# input_folder = "results_n_experiment"
# output_file = "results_n_experiment/combined_results.csv"

# all_rows = []
# header = None

# # Stats
# true_counts = defaultdict(int)
# total_counts = defaultdict(int)

# time_sums = defaultdict(float)
# time_counts = defaultdict(int)

# success_time_sums = defaultdict(float)
# success_time_counts = defaultdict(int)

# for filename in os.listdir(input_folder):
#     if filename.startswith("combined"):
#         continue
#     if filename.endswith(".csv"):
#         filepath = os.path.join(input_folder, filename)
#         with open(filepath, "r", newline="") as f:
#             reader = csv.reader(f)
#             rows = list(reader)

#             if len(rows) <= 1:
#                 continue

#             if header is None:
#                 header = rows[0]

#             for row in rows[1:]:
#                 if row == header:
#                     continue

#                 rho = float(row[0])
#                 time_val = float(row[3])
#                 solution_found = row[5].strip().lower() == "true"

#                 # Counts
#                 total_counts[rho] += 1
#                 if solution_found:
#                     true_counts[rho] += 1

#                 # Time stats (all runs)
#                 time_sums[rho] += time_val
#                 time_counts[rho] += 1

#                 # Time stats (successful runs only)
#                 if solution_found:
#                     success_time_sums[rho] += time_val
#                     success_time_counts[rho] += 1

#                 all_rows.append(row)

# # Sort by rho
# all_rows.sort(key=lambda row: float(row[0]))

# # Write combined file
# with open(output_file, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(header)
#     writer.writerows(all_rows)

# print(f"Combined file written to {output_file}")

# # ---- RESULTS ----

# print("\nSuccess count per n:")
# for rho in sorted(total_counts.keys()):
#     print(f"n={rho}: {true_counts[rho]}/{total_counts[rho]}")

# print("\nAverage computation time per n (all runs):")
# for rho in sorted(time_counts.keys()):
#     avg_time = time_sums[rho] / time_counts[rho]
#     print(f"n={rho}: {avg_time:.2f} s")

# print("\nAverage computation time per n (successful runs only):")
# for rho in sorted(success_time_counts.keys()):
#     avg_time = success_time_sums[rho] / success_time_counts[rho]
#     print(f"n={rho}: {avg_time:.2f} s")

# combine time
# import os
# import csv

# input_folder = "results_time_20_sp"
# output_file = "results_time_20_sp/combined_results2.csv"

# all_rows = []
# header = None

# for filename in os.listdir(input_folder):
#     if filename.startswith("combined"):
#         continue
#     if filename.endswith(".csv"):
#         filepath = os.path.join(input_folder, filename)
#         with open(filepath, "r", newline="") as f:
#             reader = csv.reader(f)
#             rows = list(reader)

#             if len(rows) <= 1:
#                 continue

#             if header is None:
#                 header = rows[0]

#             for row in rows[1:]:
#                 if row == header:
#                     continue
#                 all_rows.append(row)

# # Sort by end_time (column 1)
# def sort_key(row):
#     return float(row[1])  # or int(row[1]) if always integer

# all_rows.sort(key=sort_key)

# with open(output_file, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(header)
#     writer.writerows(all_rows)

# print(f"Combined file written to {output_file}")



# get only feasible solutions for sp
# import os
# import csv
# import re

# folder_path = "solutions_360_sp"
# output_csv = "results_360_sp/combined_results_2.csv"

# rows = []

# pattern = re.compile(
#   r"sp_rho.*?_task\d+_(.+)_(\d+)\.json$"
# )

# for filename in os.listdir(folder_path):
#   if not filename.endswith(".json"):
#     continue

#   match = pattern.match(filename)
#   if not match:
#     continue

#   extracted_name = match.group(1)
#   endtime = match.group(2)

#   file_path = os.path.join(folder_path, filename)

#   with open(file_path, "r") as f:
#     content = f.read()

#   # Skip files where solution was not found
#   if "found\nTrue" not in content:
#     continue

#   # Extract computation time from the last conflicts,time entry
#   computation_time = None

#   conflict_time_matches = re.findall(
#     r"^\d+,\s*([0-9.]+)$",
#     content,
#     re.MULTILINE
#   )

#   if conflict_time_matches:
#     computation_time = conflict_time_matches[-1]

#   rows.append({
#     "filename": extracted_name,
#     "found": True,
#     "endtime": endtime,
#     "computation_time": computation_time
#   })

# with open(output_csv, "w", newline="") as csvfile:
#   writer = csv.DictWriter(
#     csvfile,
#     fieldnames=[
#       "filename",
#       "found",
#       "endtime",
#       "computation_time"
#     ]
#   )

#   writer.writeheader()
#   writer.writerows(rows)

# print(f"Saved {len(rows)} rows to {output_csv}")


# combine only feasible soltuion found true for sp continuous
# import os
# import csv
# import re

# folder_path = "solutions_360_sp_c"
# output_csv = "results_360_sp_c/combined_results_2.csv"

# rows = []

# # Match:
# # sp_rho2_task0_scenario_solver_10_trains_10_units1.json
# pattern = re.compile(
#   r"sp_rho\d+_task\d+_(scenario_.+)\.json$"
# )
# # sp_rho0.5_task299_scenario_solver_5_trains_5_units8.json
# pattern = re.compile(
#   r"sp_rho[0-9.]+_task\d+_(scenario_solver_\d+_trains_\d+_units\d+)\.json$"
# )

# for filename in os.listdir(folder_path):

#   if not filename.endswith(".json"):
#     continue

#   match = pattern.match(filename)

#   if not match:
#     continue

#   # Extract:
#   # scenario_solver_10_trains_10_units1
#   extracted_name = match.group(1)

#   file_path = os.path.join(
#     folder_path,
#     filename
#   )

#   with open(file_path, "r") as f:
#     content = f.read()

#   # Skip unsolved files
#   if "found\nTrue" not in content:
#     continue

#   # =========================
#   # EXTRACT COMPUTATION TIME
#   # =========================
#   computation_time = None

#   conflict_time_matches = re.findall(
#     r"^\d+,\s*([0-9.]+)$",
#     content,
#     re.MULTILINE
#   )

#   if conflict_time_matches:
#     computation_time = conflict_time_matches[-1]

#   rows.append({
#     "filename": extracted_name,
#     "found": True,
#     "computation_time": computation_time
#   })

# # =========================
# # WRITE CSV
# # =========================
# with open(output_csv, "w", newline="") as csvfile:

#   writer = csv.DictWriter(
#     csvfile,
#     fieldnames=[
#       "filename",
#       "found",
#       "computation_time"
#     ]
#   )

#   writer.writeheader()
#   writer.writerows(rows)

# print(
#   f"Saved {len(rows)} rows to "
#   f"{output_csv}"
# )
