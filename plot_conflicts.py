# import os
# import pandas as pd
# import matplotlib.pyplot as plt
# import re

# folder = "solutions_types_120"
# data = {}
# pattern = re.compile(r"(\d+)_trains")

# for filename in os.listdir(folder):
#   match = pattern.search(filename)
#   if not match:
#     continue
#   num_trains = int(match.group(1))
#   filepath = os.path.join(folder, filename)

#   with open(filepath, "r") as f:
#     lines = f.readlines()

#   start_idx = None
#   for i, line in enumerate(lines):
#     if line.strip() == "conflicts,time":
#       start_idx = i + 1
#       break
#   if start_idx is None:
#     continue

#   conflicts, times = [], []
#   for line in lines[start_idx:]:
#     line = line.strip()
#     if not line:
#       continue
#     parts = line.split(",")
#     if len(parts) < 2:
#       continue
#     conflicts.append(float(parts[0]))
#     times.append(float(parts[1]) / 60.0)

#   if len(times) == 0:
#     continue

#   df = pd.DataFrame({"time": times, "conflicts": conflicts})
#   data.setdefault(num_trains, []).append(df)

# avg_data = {}

# for num_trains, dfs in data.items():
#   max_time = max(df["time"].max() for df in dfs)
#   max_minute = int(max_time)

#   filled_dfs = []

#   for scenario in dfs:
#     minute_map = {}
#     for t, c in zip(scenario["time"], scenario["conflicts"]):
#       minute = int(t)
#       minute_map[minute] = c

#     filled_minutes = []
#     filled_conflicts = []

#     current_value = scenario["conflicts"].iloc[0]

#     for m in range(max_minute + 1):
#       if m in minute_map:
#         current_value = minute_map[m]
#       filled_minutes.append(m)
#       filled_conflicts.append(current_value)

#     filled_dfs.append(pd.DataFrame({"time_min": filled_minutes, "conflicts": filled_conflicts}))

#   combined = pd.concat(filled_dfs)
#   avg = combined.groupby("time_min")["conflicts"].mean()
#   avg_data[num_trains] = avg

# plt.figure()
# plt.xlim(0, 33)
# for num_trains in sorted(avg_data.keys()):
#   avg = avg_data[num_trains]
#   plt.plot(avg.index, avg.values, label=f"{num_trains} trains")

# plt.xlabel("Time (minutes)")
# plt.ylabel("Number of conflicts")
# plt.title("ALR: Conflicts vs Time ")
# plt.legend()
# plt.grid()

# plt.savefig("results/ALR_conflicts.png", dpi=300, bbox_inches="tight")





# folders = ["data_types_360/results_ls_discreet", "data_types_360/results_ls"]
# # folders = ["results_ls_120"]

# conflict_pattern = re.compile(r"cr=(\d+), dd=(\d+), da=(\d+), tlv=(\d+)")
# time_elapsed_pattern = re.compile(r"Time elapsed: ([\d.]+) seconds")
# total_time_pattern = re.compile(r"Total computation time: (\d+):(\d+):([\d.]+)")
# train_pattern = re.compile(r"scenario_solver_(\d+)_trains")

# for folder in folders:
#   data = {}

#   for filename in os.listdir(folder):
#     if filename == "combined_results.csv":
#       continue

#     filepath = os.path.join(folder, filename)

#     with open(filepath, "r") as f:
#       lines = f.readlines()

#     conflicts, times = [], []
#     num_trains = None

#     for line in lines:
#       if "NO_COST_FOUND" in line:
#         continue

#       if num_trains is None:
#         train_match = train_pattern.search(line)
#         if train_match:
#           num_trains = int(train_match.group(1))

#       conflict_match = conflict_pattern.search(line)
      
#       time_minute = None
#       time_match = time_elapsed_pattern.search(line)
#       if time_match:
#         time_minute = float(time_match.group(1)) / 60.0
#       else:
#         total_match = total_time_pattern.search(line)
#         if total_match:
#           hours = int(total_match.group(1))
#           minutes = int(total_match.group(2))
#           seconds = float(total_match.group(3))

#           total_seconds = hours * 3600 + minutes * 60 + seconds
#           time_minute = total_seconds / 60.0

#       if not conflict_match or not time_minute:
#         continue

#       cr = int(conflict_match.group(1))
#       dd = int(conflict_match.group(2))
#       da = int(conflict_match.group(3))
#       tlv = int(conflict_match.group(4))

#       total_conflicts = cr + dd + da + tlv
#       # time_min = float(time_match.group(1)) / 60.0

#       conflicts.append(total_conflicts)
#       times.append(time_minute)
    
    
#     if len(times) == 0 or num_trains is None:
#       continue

#     # t0 = times[0]
#     # times = [t - t0 for t in times]

#     df = pd.DataFrame({"time": times, "conflicts": conflicts})
#     data.setdefault(num_trains, []).append(df)

#     # if num_trains == 25:
#     #   print(f"\nFILE: {filename}")
#     #   for t, c in zip(times, conflicts):
#     #     print(f"time={t:.2f}, conflicts={c}")

#   avg_data = {}

#   for num_trains, dfs in data.items():
#     # max_time = max(df["time"].max() for df in dfs)
#     max_minute = 30

#     filled_dfs = []

#     for df in dfs:
#       minute_map = {}
#       for t, c in zip(df["time"], df["conflicts"]):
#         minute_map[int(t)] = c

#       filled_minutes = []
#       filled_conflicts = []

#       current_value = df["conflicts"].iloc[0]

#       for m in range(max_minute + 1):
#         if m in minute_map:
#           current_value = minute_map[m]
#         filled_minutes.append(m)
#         filled_conflicts.append(current_value)

#       filled_dfs.append(pd.DataFrame({"time_min": filled_minutes, "conflicts": filled_conflicts}))
#       # if num_trains == 25:
#       #   print("\nMINUTE MAP:")
#       #   for k in sorted(minute_map.keys()):
#       #     print(f"minute={k}, conflicts={minute_map[k]}")
#       # if num_trains == 25:
#       #   print("\nFILLED:")
#       #   for m, c in zip(filled_minutes, filled_conflicts):
#       #     print(f"minute={m}, conflicts={c}")
#     combined = pd.concat(filled_dfs)
#     avg = combined.groupby("time_min")["conflicts"].mean()

#     avg_data[num_trains] = avg

#   plt.figure()
#   plt.xlim(0, 33)

#   for num_trains in sorted(avg_data.keys()):
#     avg = avg_data[num_trains]
#     plt.plot(avg.index, avg.values, label=f"{num_trains} trains")

#   name = "LS Discreet" if "discreet" in folder else "LS Continuous"
#   plt.xlabel("Time (minutes)")
#   plt.ylabel("Number of conflicts")
#   plt.title(f"{name}: Conflicts vs Time")
#   plt.legend()
#   plt.grid()

#   outname = "LS_discreet_conflicts_360.png" if "discreet" in folder else "LS_conflicts_360.png"
#   plt.savefig(f"results/{outname}", dpi=300, bbox_inches="tight")




import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import re
import numpy as np

# --- Setup for Color Coding ---
# This creates a gradient from your light blue to your dark blue
custom_blues = mcolors.LinearSegmentedColormap.from_list("custom_blues", ["#bdd7e7", "#08519c"])

folder = "data_types_360/solutions_types_360"
data = {}
pattern = re.compile(r"(\d+)_trains")

for filename in os.listdir(folder):
  match = pattern.search(filename)
  if not match:
    continue
  num_trains = int(match.group(1))
  filepath = os.path.join(folder, filename)
  with open(filepath, "r") as f:
    lines = f.readlines()
  start_idx = None
  for i, line in enumerate(lines):
    if line.strip() == "conflicts,time":
      start_idx = i + 1
      break
  if start_idx is None:
    continue
  conflicts, times = [], []
  for line in lines[start_idx:]:
    line = line.strip()
    if not line:
      continue
    parts = line.split(",")
    if len(parts) < 2:
      continue
    conflicts.append(float(parts[0]))
    times.append(float(parts[1]) / 60.0)
  if len(times) == 0:
    continue
  df = pd.DataFrame({"time": times, "conflicts": conflicts})
  data.setdefault(num_trains, []).append(df)

avg_data = {}
for num_trains, dfs in data.items():
  max_time = max(df["time"].max() for df in dfs)
  max_minute = int(max_time)
  filled_dfs = []
  for scenario in dfs:
    minute_map = {}
    for t, c in zip(scenario["time"], scenario["conflicts"]):
      minute = int(t)
      minute_map[minute] = c
    filled_minutes = []
    filled_conflicts = []
    current_value = scenario["conflicts"].iloc[0]
    for m in range(max_minute + 1):
      if m in minute_map:
        current_value = minute_map[m]
      filled_minutes.append(m)
      filled_conflicts.append(current_value)
    filled_dfs.append(pd.DataFrame({"time_min": filled_minutes, "conflicts": filled_conflicts}))
  combined = pd.concat(filled_dfs)
  avg = combined.groupby("time_min")["conflicts"].mean()
  avg_data[num_trains] = avg

# Plotting first section (ALR)
plt.figure()
plt.xlim(0, 33)
sorted_keys = sorted(avg_data.keys())
for i, num_trains in enumerate(sorted_keys):
  avg = avg_data[num_trains]
  color = custom_blues(i / (len(sorted_keys) - 1)) if len(sorted_keys) > 1 else "#08519c"
  plt.plot(avg.index, avg.values, label=f"{num_trains} trains", color=color)
plt.xlabel("Time (minutes)")
plt.ylabel("Number of conflicts")
plt.title("ALR: Conflicts vs Time ")
plt.legend()
plt.grid()
plt.savefig("results/ALR_conflicts.png", dpi=300, bbox_inches="tight")

# --- Second Section (LS) ---
folders = ["data_types_360/results_ls_discreet", "data_types_360/results_ls"]
conflict_pattern = re.compile(r"cr=(\d+), dd=(\d+), da=(\d+), tlv=(\d+)")
time_elapsed_pattern = re.compile(r"Time elapsed: ([\d.]+) seconds")
total_time_pattern = re.compile(r"Total computation time: (\d+):(\d+):([\d.]+)")
train_pattern = re.compile(r"scenario_solver_(\d+)_trains")

for folder in folders:
  data = {}
  for filename in os.listdir(folder):
    if filename == "combined_results.csv":
      continue
    filepath = os.path.join(folder, filename)
    with open(filepath, "r") as f:
      lines = f.readlines()
    conflicts, times = [], []
    num_trains = None
    for line in lines:
      if "NO_COST_FOUND" in line:
        continue
      if num_trains is None:
        train_match = train_pattern.search(line)
        if train_match:
          num_trains = int(train_match.group(1))
      conflict_match = conflict_pattern.search(line)
      
      time_minute = None
      time_match = time_elapsed_pattern.search(line)
      if time_match:
        time_minute = float(time_match.group(1)) / 60.0
      else:
        total_match = total_time_pattern.search(line)
        if total_match:
          hours = int(total_match.group(1))
          minutes = int(total_match.group(2))
          seconds = float(total_match.group(3))
          total_seconds = hours * 3600 + minutes * 60 + seconds
          time_minute = total_seconds / 60.0
      if not conflict_match or not time_minute:
        continue
      cr = int(conflict_match.group(1))
      dd = int(conflict_match.group(2))
      da = int(conflict_match.group(3))
      tlv = int(conflict_match.group(4))
      total_conflicts = cr + dd + da + tlv
      conflicts.append(total_conflicts)
      times.append(time_minute)
    
    if len(times) == 0 or num_trains is None:
      continue
    df = pd.DataFrame({"time": times, "conflicts": conflicts})
    data.setdefault(num_trains, []).append(df)

  avg_data = {}
  for num_trains, dfs in data.items():
    max_minute = 30
    filled_dfs = []
    for df in dfs:
      minute_map = {}
      for t, c in zip(df["time"], df["conflicts"]):
        minute_map[int(t)] = c
      filled_minutes = []
      filled_conflicts = []
      current_value = df["conflicts"].iloc[0]
      for m in range(max_minute + 1):
        if m in minute_map:
          current_value = minute_map[m]
        filled_minutes.append(m)
        filled_conflicts.append(current_value)
      filled_dfs.append(pd.DataFrame({"time_min": filled_minutes, "conflicts": filled_conflicts}))

    combined = pd.concat(filled_dfs)
    avg = combined.groupby("time_min")["conflicts"].mean()
    avg_data[num_trains] = avg

  plt.figure()
  plt.xlim(0, 33)
  sorted_keys_ls = sorted(avg_data.keys())
  for i, num_trains in enumerate(sorted_keys_ls):
    avg = avg_data[num_trains]
    # Apply the same gradient color logic
    color = custom_blues(i / (len(sorted_keys_ls) - 1)) if len(sorted_keys_ls) > 1 else "#08519c"
    plt.plot(avg.index, avg.values, label=f"{num_trains} trains", color=color)

  name = "LS Discreet" if "discreet" in folder else "LS Continuous"
  plt.xlabel("Time (minutes)")
  plt.ylabel("Number of conflicts")
  plt.title(f"{name}: Conflicts vs Time")
  plt.legend()
  plt.grid()
  outname = "LS_discreet_conflicts_360.png" if "discreet" in folder else "LS_conflicts_360.png"
  plt.savefig(f"results/{outname}", dpi=300, bbox_inches="tight")