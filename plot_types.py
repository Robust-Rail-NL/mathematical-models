# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# import numpy as np

# type_colors = {
#   "1": "#bdd7e7",
#   "5": "#6baed6",
#   "1/3": "#3182bd",
#   "num_trains": "#08519c"
# }

# algo_colors = {
#   "ADMM": {
#     "color": "#1f77b4",  # blue
#     "linestyle": "-",
#     "marker": "s",
#     "markersize": 6,
#     "markerfacecolor": "#1f77b4",
#     "markeredgecolor": "#1f77b4",
#   },

#   "ADMM Continuous": {
#     "color": "#5fa6d9",  # lighter blue
#     "linestyle": (0, (2, 2)),
#     "marker": "s",
#     "markersize": 6,
#     "markerfacecolor": "none",
#     "markeredgecolor": "#5fa6d9",
#   },

#   "Continuous LS": {
#     "color": "#ff7f7f",  # lighter red
#     "linestyle": (0, (1, 4)),
#     "marker": "o",
#     "markersize": 6,
#     "markerfacecolor": "none",
#     "markeredgecolor": "#ff7f7f",
#   },

#   "Discrete LS": {
#     "color": "#d62728",  # red
#     "linestyle": "-",
#     "marker": "o",
#     "markersize": 6,
#     "markerfacecolor": "#d62728",
#     "markeredgecolor": "#d62728",
#   }
# }

# algorithms = {
#   # "ADMM": "data_types_360/results_types_360",
#   "ADMM Continuous": "results_360_sp_c",
#   "ADMM": "results_360_sp",
#   "Continuous LS": "data_types_360/results_ls",
#   "Discrete LS": "data_types_360/results_ls_discreet"
# }

# x_ticks = [5,10,15,20,25,30]
# all_types = ["1", "5", "1/3", "num_trains"]

# results_time = {}
# results_solved = {}

# # =========================
# # COLLECT DATA PER ALGO
# # =========================
# for algo_name, folder in algorithms.items():
#   df = pd.read_csv(f"{folder}/combined_results.csv")
#   df["solution_found"] = df["solution_found"].astype(bool)
#   df["type"] = df["type"].astype(str)

#   df.loc[~df["solution_found"], "time"] = 30*60

#   # ---- TIME ----
#   df_time = df.copy()
#   df_time["time"] = df_time["time"] / 60

#   avg_time = df_time.groupby(["num_trains","type"])["time"].mean().unstack()
#   avg_time_filled = avg_time.copy()

#   for n in avg_time.index:
#     # t_static = str(int(n / 3))
#     t_static_val = n / 3
#     t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
#     t_n = str(n)

#     if t_static and "1/3" in avg_time.columns and t_static in avg_time.columns:
#       v_static = avg_time.loc[n, t_static]
#       v_n3 = avg_time.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "1/3"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_n3):
#         avg_time_filled.loc[n, t_static] = v_n3

#     if "num_trains" in avg_time.columns and t_n in avg_time.columns:
#       v_static = avg_time.loc[n, t_n]
#       v_nval = avg_time.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "num_trains"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_nval):
#         avg_time_filled.loc[n, t_n] = v_nval

#   results_time[algo_name] = avg_time_filled

#   # ---- SOLVED ----
#   solved_count = df.groupby(["num_trains", "type"])["solution_found"].sum().unstack()
#   solved_count_filled = solved_count.copy()

#   for n in solved_count.index:
#     t_static_val = n / 3
#     t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
#     # t_static = str(int(n / 3))
#     t_n = str(n)

#     if t_static and "1/3" in solved_count.columns and t_static in solved_count.columns:
#       v_static = solved_count.loc[n, t_static]
#       v_n3 = solved_count.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "1/3"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_n3):
#         solved_count_filled.loc[n, t_static] = v_n3

#     if "num_trains" in solved_count.columns and t_n in solved_count.columns:
#       v_static = solved_count.loc[n, t_n]
#       v_nval = solved_count.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "num_trains"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_nval):
#         solved_count_filled.loc[n, t_n] = v_nval

#   results_solved[algo_name] = solved_count_filled


# # =========================
# # GLOBAL Y-SCALE (TIME)
# # =========================
# all_times = []
# for df in results_time.values():
#   vals = df.values.flatten()
#   vals = vals[~pd.isna(vals)]
#   vals = vals[vals > 0]
#   all_times.extend(vals)

# y_min = min(all_times) * 0.8 if len(all_times) > 0 else 0.1
# y_max = 35

# for t in all_types:
#   plt.figure()

#   for algo_name, df_algo in results_time.items():
#     if t in df_algo.columns:
#       x = df_algo.index
#       y = df_algo[t]

#       plt.plot(
#         x, y,
#         # marker='o',
#         label=algo_name,
#         **algo_colors[algo_name],
#       )

#   plt.xlabel("Number of Trains")
#   plt.ylabel("Time (minutes)")
#   plt.xticks(x_ticks)
#   plt.yscale("log")

#   # ---- EXACTLY your original scaling ----
#   minute_ticks = [1,2,5,10,20,30]
#   y_max = 35

#   all_times = []
#   for df in results_time.values():
#     vals = df.values.flatten()
#     vals = vals[~pd.isna(vals)]
#     all_times.extend(vals)

#   all_times = np.array(all_times)
#   nonzero_times = all_times[all_times > 0]
#   y_min = nonzero_times.min() * 0.8 if len(nonzero_times) > 0 else 0.1

#   plt.ylim(0.007891121555555556, y_max)
#   print(y_min)

#   plt.yticks(minute_ticks, labels=minute_ticks)

#   plt.grid(True, which="both", linestyle="--", linewidth=0.5)
#   if t == "1/3":
#     plt.title(f"n/3 Types: Average Time")
#   elif t == "num_trains":
#     plt.title(f"n Types: Average Time")
#   else:
#     plt.title(f"{t} Types: Average Time")
#   plt.legend()

#   filename_t = t.replace("/", "_")
#   plt.savefig(f"results/360_c/time_type_{filename_t}.png", dpi=300, bbox_inches="tight")
#   plt.close()


# # =========================
# # SOLVED PLOTS PER TYPE
# # =========================
# for t in all_types:
#   plt.figure()

#   for algo_name, df_algo in results_solved.items():
#     if t in df_algo.columns:
#       x = df_algo.index
#       y = df_algo[t]

#       plt.plot(x, y, label=algo_name, **algo_colors[algo_name])

#   plt.xlabel("Number of Trains")
#   plt.ylabel("Solved Instances")
#   plt.xticks(x_ticks)
#   plt.ylim(0, 32)

#   plt.grid(True, linestyle="--", linewidth=0.5)
#   if t == "1/3":
#     plt.title(f"n/3 Types: Solved Instances")
#   elif t == "num_trains":
#     plt.title(f"n Types: Solved Instances")
#   else:
#     plt.title(f"{t} Types: Solved Instances")
#   plt.legend()

#   filename_t = t.replace("/", "_")
#   plt.savefig(f"results/360_c/solved_type_{filename_t}.png", dpi=300, bbox_inches="tight")
#   plt.close()



# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# import re
# import math
# import numpy as np

# type_colors = {
#   "1": "#bdd7e7",
#   "5": "#6baed6",
#   "1/3": "#3182bd",
#   "num_trains": "#08519c"
# }

# algorithms = {
#   "ADMM": "results_types_360",
#   "LS Continuous": "data_types_360/results_ls",
#   "LS Discreet": "data_types_360/results_ls_discreet"
# }

# static_types = ["1", "5"]
# x_ticks = [5,10,15,20,25,30]


# for algo_name, folder in algorithms.items():
#   df = pd.read_csv(f"{folder}/combined_results.csv")
#   df["solution_found"] = df["solution_found"].astype(bool)
#   df["type"] = df["type"].astype(str)

#   df.loc[~df["solution_found"], "time"] = 30*60

#   # ---- TIME PLOT ----
#   df_time = df.copy()
#   # df_time = df[df["solution_found"]].copy()
#   df_time["time"] = df_time["time"]/60

#   avg_time = df_time.groupby(["num_trains","type"])["time"].mean().unstack()
#   avg_time_filled = avg_time.copy()

#   for n in avg_time.index:
#     t_static = str(int(n / 3))
#     t_n = str(n)

#     # ---- n/3 <-> static (e.g. 15 <-> 5)
#     if "1/3" in avg_time.columns and t_static in avg_time.columns:
#       v_static = avg_time.loc[n, t_static] if t_static in avg_time.columns else None
#       v_n3 = avg_time.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "1/3"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_n3):
#         avg_time_filled.loc[n, t_static] = v_n3

#     # ---- n <-> static (e.g. 5 <-> 5)
#     if "num_trains" in avg_time.columns and t_n in avg_time.columns:
#       v_static = avg_time.loc[n, t_n]
#       v_nval = avg_time.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "num_trains"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_nval):
#         avg_time_filled.loc[n, t_n] = v_nval
#   plt.figure()
  
#   for t in static_types:
#     if t in avg_time_filled.columns:
#       x = avg_time_filled.index
#       y = avg_time_filled[t]

#       plt.plot(x, y,
#               marker='o',
#               color=type_colors[t],
#               label=f"Type {t}")

#   if "1/3" in avg_time_filled.columns:
#     x = avg_time_filled.index
#     y = avg_time_filled["1/3"]

#     plt.plot(x, y,
#             marker='o',
#             linestyle='-.',
#             color=type_colors["1/3"],
#             label="Type n/3")

#   if "num_trains" in avg_time_filled.columns:
#     x = avg_time_filled.index
#     y = avg_time_filled["num_trains"]

#     plt.plot(x, y,
#             marker='o',
#             linestyle='--',
#             color=type_colors["num_trains"],
#             label="Type n")

#   plt.xlabel("Number of trains")
#   plt.ylabel("Time (minutes)")
#   plt.xticks(x_ticks)
#   plt.yscale("log")

#   minute_ticks = [1,2,5,10,20,30]
#   y_max = 35
#   all_times = avg_time.values.flatten()
#   all_times = all_times[~pd.isna(all_times)]
#   nonzero_times = all_times[all_times > 0]
#   y_min = nonzero_times.min() * 0.8 if len(nonzero_times) > 0 else 0.1
#   plt.ylim(0.007891121555555556, y_max)
#   print(y_min)

#   plt.yticks(minute_ticks, labels=minute_ticks)

#   plt.grid(True, which="both", linestyle="--", linewidth=0.5)
#   plt.title(f"{algo_name}: Average Time")
#   plt.legend()

#   os.makedirs("results", exist_ok=True)
#   plt.savefig(f"results/360/{algo_name}_time_360.png", dpi=300, bbox_inches="tight")
#   plt.close()

#   # ---- SOLUTIONS FOUND PLOT ----
#   solved_count = (
#     df.groupby(["num_trains", "type"])["solution_found"].sum().unstack())
#   solved_count_filled = solved_count.copy()

#   solved_count_filled = solved_count.copy()

#   for n in solved_count.index:
#     t_static = str(int(n / 3))
#     t_n = str(n)

#     # ---- n/3 <-> static (e.g. 15 <-> 5)
#     if "1/3" in solved_count.columns and t_static in solved_count.columns:
#       v_static = solved_count.loc[n, t_static] if t_static in solved_count.columns else None
#       v_n3 = solved_count.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "1/3"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_n3):
#         solved_count_filled.loc[n, t_static] = v_n3

#     # ---- n <-> static (e.g. 5 <-> 5)
#     if "num_trains" in solved_count.columns and t_n in solved_count.columns:
#       v_static = solved_count.loc[n, t_n]
#       v_nval = solved_count.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "num_trains"] = v_static
#       if pd.isna(v_static) and not pd.isna(v_nval):
#         solved_count_filled.loc[n, t_n] = v_nval
#   plt.figure()

#   for t in static_types:
#     if t in solved_count_filled.columns:
#       x = solved_count_filled.index
#       y = solved_count_filled[t]

#       print(f"{algo_name} SOLVED Type {t}:")
#       for xi, yi in zip(x, y):
#         print(f"  trains={xi}, value={yi}")

#       plt.plot(x, y,
#               marker='o',
#               color=type_colors[t],
#               label=f"Type {t}")

#   if "1/3" in solved_count_filled.columns:
#     x = solved_count_filled.index
#     y = solved_count_filled["1/3"]

#     print(f"{algo_name} SOLVED Type n/3:")
#     for xi, yi in zip(x, y):
#       print(f"  trains={xi}, value={yi}")

#     plt.plot(x, y,
#             marker='o',
#             linestyle='-.',
#             color=type_colors["1/3"],
#             label="Type n/3")

#   if "num_trains" in solved_count_filled.columns:
#     x = solved_count_filled.index
#     y = solved_count_filled["num_trains"]

#     print(f"{algo_name} SOLVED Type n:")
#     for xi, yi in zip(x, y):
#       print(f"  trains={xi}, value={yi}")

#     plt.plot(x, y,
#             marker='o',
#             linestyle='--',
#             color=type_colors["num_trains"],
#             label="Type n")

#   plt.ylim(0, 32)
#   plt.xlabel("Number of trains")
#   plt.ylabel("Solved instances")
#   plt.xticks(x_ticks)

#   plt.grid(True, linestyle="--", linewidth=0.5)
#   plt.title(f"{algo_name}: Number of solved instances")
#   plt.legend()

#   plt.savefig(f"results/360/{algo_name}_solutions_360.png", dpi=300, bbox_inches="tight")
#   plt.close()


import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math

type_colors = {
  "1": "#bdd7e7",
  "5": "#6baed6",
  "1/3": "#3182bd",
  "num_trains": "#08519c"
}

algo_colors = {
  "ADMM": {
    "color": "#1f77b4",
    "linestyle": "-",
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "#1f77b4",
    "markeredgecolor": "#1f77b4",
  },

  "ADMM Continuous": {
    "color": "#5fa6d9",
    "linestyle": (0, (2, 2)),
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "none",
    "markeredgecolor": "#5fa6d9",
  },

  "Continuous LS": {
    "color": "#ff7f7f",
    "linestyle": (0, (1, 4)),
    "marker": "o",
    "markersize": 6,
    "markerfacecolor": "none",
    "markeredgecolor": "#ff7f7f",
  },

  "Discrete LS": {
    "color": "#d62728",
    "linestyle": "-",
    "marker": "o",
    "markersize": 6,
    "markerfacecolor": "#d62728",
    "markeredgecolor": "#d62728",
  }
}

algorithms = {
  "ADMM Continuous": "results_360_sp_c",
  "ADMM": "results_360_sp",
  "Continuous LS": "data_types_360/results_ls",
  "Discrete LS": "data_types_360/results_ls_discreet"
}

x_ticks = [5, 10, 15, 20, 25, 30]
all_types = ["1", "5", "1/3", "num_trains"]

results_time = {}

# =========================
# LOAD ALL DATAFRAMES
# =========================
dfs = {}

for algo_name, folder in algorithms.items():

  df = pd.read_csv(
    f"{folder}/combined_results_2.csv"
  )

  # =========================
  # NORMALIZE COLUMN NAMES
  # =========================
  if "found" in df.columns:
    df["solution_found"] = (
      df["found"].astype(str) == "True"
    )

  # =========================
  # PARSE COMPUTATION TIME
  # =========================
  if "computation_time" in df.columns:

    # ADMM -> already seconds
    df["time_seconds"] = pd.to_numeric(
      df["computation_time"],
      errors="coerce"
    )

  elif "total_computation_time" in df.columns:

    # LS -> HH:MM:SS
    df["time_seconds"] = pd.to_timedelta(
      df["total_computation_time"]
    ).dt.total_seconds()

  # # =========================
  # # EXTRACT num_trains + type
  # # from filename:
  # # scenario_solver_10_trains_10_units1
  # # =========================
  # extracted = df["filename"].str.extract(
  #   r"solver_(\d+)_trains_(.+)"
  # )

  # df["num_trains"] = extracted[0].astype(int)
  # df["type"] = extracted[1].astype(str)
  
  # =========================
  # EXTRACT num_trains + type
  # =========================
  extracted = df["filename"].str.extract(
    r"solver_(\d+)_trains_(.+)_units\d+"
  )

  df["num_trains"] = extracted[0].astype(int)

  raw_type = extracted[1]

  # =========================
  # NORMALIZE TYPE
  # =========================
  def normalize_type(type_value, num_trains):

    type_int = int(type_value)

    # n types
    if type_int == num_trains:
      return "num_trains"

    # n/3 types
    if type_int ==  math.ceil(num_trains / 3):
      return "1/3"

    return str(type_int)

  df["type"] = [
    normalize_type(t, n)
    for t, n in zip(
      raw_type,
      df["num_trains"]
    )
  ]
  print(sorted(df["type"].unique()))
  # =========================
  # CREATE UNIQUE INSTANCE KEY
  # =========================
  df["instance_key"] = (
    df["filename"]
  )

  dfs[algo_name] = df


# =========================
# KEEP ONLY INSTANCES
# SOLVED BY ALL 4 ALGORITHMS
# =========================
common_instances = None

for algo_name, df in dfs.items():

  solved_instances = set(
    df.loc[
      df["solution_found"],
      "instance_key"
    ]
  )

  if common_instances is None:
    common_instances = solved_instances
  else:
    common_instances &= solved_instances

print(
  f"Common solved instances across all "
  f"algorithms: {len(common_instances)}"
)

# =========================
# COMPUTE AVERAGE TIMES
# =========================
for algo_name, df in dfs.items():

  df_filtered = df[
    df["instance_key"].isin(common_instances)
  ].copy()

  # convert to minutes
  df_filtered["time_minutes"] = (
    df_filtered["time_seconds"] / 60
  )

  avg_time = (
    df_filtered
    .groupby(["num_trains", "type"])[
      "time_minutes"
    ]
    .mean()
    .unstack()
  )

  avg_time_filled = avg_time.copy()

  # =========================
  # FILL MISSING EQUIVALENT TYPES
  # =========================
  for n in avg_time.index:

    t_static_val = n / 3
    t_static = (
      str(int(t_static_val))
      if t_static_val.is_integer()
      else None
    )

    t_n = str(n)

    # ---- 1/3 <-> static equivalent ----
    if (
      t_static and
      "1/3" in avg_time.columns and
      t_static in avg_time.columns
    ):

      v_static = avg_time.loc[n, t_static]
      v_n3 = avg_time.loc[n, "1/3"]

      if pd.isna(v_n3) and not pd.isna(v_static):
        avg_time_filled.loc[n, "1/3"] = v_static

      if pd.isna(v_static) and not pd.isna(v_n3):
        avg_time_filled.loc[n, t_static] = v_n3

    # ---- num_trains <-> n equivalent ----
    if (
      "num_trains" in avg_time.columns and
      t_n in avg_time.columns
    ):

      v_static = avg_time.loc[n, t_n]
      v_nval = avg_time.loc[n, "num_trains"]

      if pd.isna(v_nval) and not pd.isna(v_static):
        avg_time_filled.loc[n, "num_trains"] = v_static

      if pd.isna(v_static) and not pd.isna(v_nval):
        avg_time_filled.loc[n, t_n] = v_nval

  results_time[algo_name] = avg_time_filled


# =========================
# GLOBAL Y SCALE
# =========================
all_times = []

for df in results_time.values():

  vals = df.values.flatten()
  vals = vals[~pd.isna(vals)]
  vals = vals[vals > 0]

  all_times.extend(vals)

all_times = np.array(all_times)

nonzero_times = all_times[
  all_times > 0
]

y_min = (
  nonzero_times.min() * 0.8
  if len(nonzero_times) > 0
  else 0.1
)

y_max = 35


# =========================
# PLOT TIME PER TYPE
# =========================
for t in all_types:

  plt.figure()

  for algo_name, df_algo in results_time.items():

    if t not in df_algo.columns:
      continue

    x = df_algo.index
    y = df_algo[t]

    plt.plot(
      x,
      y,
      label=algo_name,
      **algo_colors[algo_name],
    )

  plt.xlabel("Number of Trains")
  plt.ylabel("Time (minutes)")

  plt.xticks(x_ticks)

  plt.yscale("log")

  minute_ticks = [1, 2, 5, 10, 20, 30]

  plt.ylim(
    0.007891121555555556,
    y_max
  )

  plt.yticks(
    minute_ticks,
    labels=minute_ticks
  )

  plt.grid(
    True,
    which="both",
    linestyle="--",
    linewidth=0.5
  )

  if t == "1/3":
    plt.title(
      "n/3 Types: Average Time "
      "(Common Solved Instances)"
    )

  elif t == "num_trains":
    plt.title(
      "n Types: Average Time "
      "(Common Solved Instances)"
    )

  else:
    plt.title(
      f"{t} Types: Average Time "
      "(Common Solved Instances)"
    )

  plt.legend()

  os.makedirs(
    "results/360_c",
    exist_ok=True
  )

  filename_t = t.replace("/", "_")

  plt.savefig(
    f"results/360_c/"
    f"time_type_{filename_t}_common.png",
    dpi=300,
    bbox_inches="tight"
  )

  plt.close()