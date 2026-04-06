import pandas as pd
import re
import os
from glob import glob
import math

INPUT_FOLDER = "results_ls/"
OUTPUT_FILE = "results_ls/combined_results.csv"

def extract_filename_info(path):
  match = re.search(r'scenario_solver_(\d+)_trains_(\d+)_units', path)
  return int(match.group(1)), int(match.group(2))

def parse_time_to_seconds(timestr):
  h, m, s = timestr.split(":")
  return int(h)*3600 + int(m)*60 + float(s)

def extract_sm(cost_line):
  if not isinstance(cost_line, str):
    return None
  match = re.search(r'sm=(\d+)', cost_line)
  return int(match.group(1)) if match else None

def extract_cost(cost_line):
  if not isinstance(cost_line, str):
    return None
  match = re.search(r'Cost = ([0-9.]+)', cost_line)
  return float(match.group(1)) if match else None

def process_file(filepath):
  df = pd.read_csv(filepath)
  df = df.fillna("")
  results = []

  for scenario, group in df.groupby("scenario"):
    num_trains, typ = extract_filename_info(scenario)

    total_time = None
    num_movements = None
    time_first_solution = None

    for _, row in group.iterrows():
      cost_line = row["cost_line"]
      time_line = row["time_line"]

      if "Time elapsed" in time_line:
        elapsed = float(re.search(r'([0-9.]+)', time_line).group(1))
        cost = extract_cost(cost_line)

        if cost == 0.0 and time_first_solution is None:
          time_first_solution = elapsed
        elif cost is None and time_first_solution is None:
          time_first_solution = elapsed

      if "Cost of solution" in cost_line:
        num_movements = extract_sm(cost_line)

      if "Total computation time" in time_line:
        time_str = time_line.split(": ", 1)[1]
        total_time = parse_time_to_seconds(time_str)

    if time_first_solution is None and total_time is not None:
      time_first_solution = total_time

    solution_found = total_time is not None and total_time <= 1800

    results.append({
      "num_trains": int(num_trains),
      "type": int(typ),
      "time": total_time,
      "time_first_solution": time_first_solution,
      "solution_found": solution_found,
      "num_movements": num_movements
    })

  return results

all_results = []

for file in glob(os.path.join(INPUT_FOLDER, "*.csv")):
  print(f"Processing {file}...")
  file_results = process_file(file)
  all_results.extend(file_results)

out_df = pd.DataFrame(all_results)

out_df['num_trains'] = out_df['num_trains'].astype(int)
out_df['type'] = out_df['type'].astype(int)

def type_order(row):
  n = int(row['num_trains'])
  t = int(row['type'])
  if t == 1:
    return 1
  elif t == 5:
    return 2
  elif t == math.ceil(n / 3):
    return 3
  elif t == n:
    return 4
  else:
    return 5

out_df['type_order'] = out_df.apply(type_order, axis=1)
out_df = out_df.sort_values(by=['num_trains', 'type_order'], ascending=True)
out_df = out_df.drop(columns=['type_order'])

out_df.to_csv(OUTPUT_FILE, index=False)

print("Done! Saved to:", OUTPUT_FILE)