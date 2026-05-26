import os
import csv
import re

input_folder = "sp_continuous_results/"
output_file = "sp_continuous_results.csv"

type_order = {
  "1": 0,
  "5": 1,
  "1/3": 2,
  "num_trains": 3
}

all_rows = []
header = None

for filename in os.listdir(input_folder):
  if filename.startswith("combined"):
    continue
  if filename.endswith(".csv"):
    filepath = os.path.join(input_folder, filename)
    with open(filepath, "r", newline="") as f:
      reader = csv.reader(f)
      rows = list(reader)
      if len(rows) <= 1:
        continue
      if header is None:
        header = rows[0]
      for row in rows[1:]:
        if row == header:
          continue
        num_trains = int(row[0])
        if num_trains == 5:
          print(filename)
        type_val = row[1]
        if type_val.isdigit() and int(type_val) == num_trains:
          row[1] = "num_trains"
        all_rows.append(row)

def sort_key(row):
  num_trains = int(row[0])
  type_val = row[1]
  return (num_trains, type_order.get(type_val, 999))

all_rows.sort(key=sort_key)

with open(output_file, "w", newline="") as f:
  writer = csv.writer(f)
  writer.writerow(header)
  writer.writerows(all_rows)

print(f"Combined file written to {output_file}")



# get only feasible solutions for sp

folder_path = "solutions_sp_continuous"
output_csv = "sp_continuous_results_common.csv"

rows = []

# Match:
# sp_rho2_task0_scenario_solver_10_trains_10_units1.json
pattern = re.compile(
  r"sp_rho\d+_task\d+_(scenario_.+)\.json$"
)
# sp_rho0.5_task299_scenario_solver_5_trains_5_units8.json
pattern = re.compile(
  r"sp_rho[0-9.]+_task\d+_(scenario_solver_\d+_trains_\d+_units\d+)\.json$"
)

for filename in os.listdir(folder_path):
  if not filename.endswith(".json"):
    continue

  match = pattern.match(filename)
  if not match:
    continue

  extracted_name = match.group(1)
  endtime = match.group(2)

  file_path = os.path.join(folder_path, filename)

  with open(file_path, "r") as f:
    content = f.read()

  # Skip files where solution was not found
  if "found\nTrue" not in content:
    continue

  # Extract computation time from the last conflicts,time entry
  computation_time = None

  conflict_time_matches = re.findall(
    r"^\d+,\s*([0-9.]+)$",
    content,
    re.MULTILINE
  )

  if conflict_time_matches:
    computation_time = conflict_time_matches[-1]

  rows.append({
    "filename": extracted_name,
    "found": True,
    "endtime": endtime,
    "computation_time": computation_time
  })

with open(output_csv, "w", newline="") as csvfile:
  writer = csv.DictWriter(
    csvfile,
    fieldnames=[
      "filename",
      "found",
      "endtime",
      "computation_time"
    ]
  )

  writer.writeheader()
  writer.writerows(rows)

print(f"Saved {len(rows)} rows to {output_csv}")

