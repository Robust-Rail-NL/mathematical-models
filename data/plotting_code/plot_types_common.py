# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# import numpy as np
# import math


# # This code plots the average computation time for each algorithm for
# # the instances solved by all algorithms, for different typexs and time
# # window of 7 hours

# algo_colors = {
#   "ADMM": {
#     "color": "#1f77b4",
#     "linestyle": "-",
#     "marker": "s",
#     "markersize": 6,
#     "markerfacecolor": "#1f77b4",
#     "markeredgecolor": "#1f77b4",
#   },

#   "Continuous ADMM": {
#     "color": "#5fa6d9",
#     "linestyle": (0, (2, 2)),
#     "marker": "s",
#     "markersize": 6,
#     "markerfacecolor": "none",
#     "markeredgecolor": "#5fa6d9",
#   },

#   "Continuous LS": {
#     "color": "#ff7f7f",
#     "linestyle": (0, (1, 4)),
#     "marker": "o",
#     "markersize": 6,
#     "markerfacecolor": "none",
#     "markeredgecolor": "#ff7f7f",
#   },

#   "Discrete LS": {
#     "color": "#d62728",
#     "linestyle": "-",
#     "marker": "o",
#     "markersize": 6,
#     "markerfacecolor": "#d62728",
#     "markeredgecolor": "#d62728",
#   }
# }

# algorithms = {
#   "Continuous ADMM": "../../data/data_types_7hours/sp_continuous_results_common.csv",
#   "ADMM": "../../data/data_types_7hours/sp_results_common.csv",
#   "Continuous LS": "../../data/data_types_7hours/results_ls_continuous/combined_results_common.csv",
#   "Discrete LS": "../../data/data_types_7hours/results_ls_discreet/combined_results_common.csv"
# }

# x_ticks = [5, 10, 15, 20, 25, 30]
# all_types = ["1", "5", "1/3", "num_trains"]

# results_time = {}

# # LOAD ALL DATAFRAMES
# dfs = {}

# for algo_name, file_path in algorithms.items():

#   df = pd.read_csv(file_path)

#   # NORMALIZE COLUMN NAMES
#   if "found" in df.columns:
#     df["solution_found"] = (
#       df["found"].astype(str) == "True"
#     )

#   # PARSE COMPUTATION TIME
#   if "computation_time" in df.columns:

#     # ADMM
#     df["time_seconds"] = pd.to_numeric(
#       df["computation_time"],
#       errors="coerce"
#     )

#   elif "total_computation_time" in df.columns:

#     # LS -> HH:MM:SS
#     df["time_seconds"] = pd.to_timedelta(
#       df["total_computation_time"]
#     ).dt.total_seconds()

#   # EXTRACT num_trains + type
#   extracted = df["filename"].str.extract(
#     r"solver_(\d+)_trains_(.+)_units\d+"
#   )

#   df["num_trains"] = extracted[0].astype(int)

#   raw_type = extracted[1]

#   # NORMALIZE TYPE
#   def normalize_type(type_value, num_trains):

#     type_int = int(type_value)

#     # n types
#     if type_int == num_trains:
#       return "num_trains"

#     # n/3 types
#     if type_int ==  math.ceil(num_trains / 3):
#       return "1/3"

#     return str(type_int)

#   df["type"] = [
#     normalize_type(t, n)
#     for t, n in zip(
#       raw_type,
#       df["num_trains"]
#     )
#   ]
#   print(sorted(df["type"].unique()))
#   # CREATE UNIQUE INSTANCE KEY
#   df["instance_key"] = (
#     df["filename"]
#   )

#   dfs[algo_name] = df


# # KEEP ONLY INSTANCES
# # SOLVED BY ALL ALGORITHMS
# common_instances = None

# for algo_name, df in dfs.items():

#   solved_instances = set(
#     df.loc[
#       df["solution_found"],
#       "instance_key"
#     ]
#   )

#   if common_instances is None:
#     common_instances = solved_instances
#   else:
#     common_instances &= solved_instances

# print(
#   f"Common solved instances across all "
#   f"algorithms: {len(common_instances)}"
# )

# # COMPUTE AVERAGE TIMES
# for algo_name, df in dfs.items():

#   df_filtered = df[
#     df["instance_key"].isin(common_instances)
#   ].copy()

#   # convert to minutes
#   df_filtered["time_minutes"] = (
#     df_filtered["time_seconds"] / 60
#   )

#   avg_time = (
#     df_filtered
#     .groupby(["num_trains", "type"])[
#       "time_minutes"
#     ]
#     .mean()
#     .unstack()
#   )

#   avg_time_filled = avg_time.copy()

#   # FILL MISSING EQUIVALENT TYPES
#   for n in avg_time.index:

#     t_static_val = n / 3
#     t_static = (
#       str(int(t_static_val))
#       if t_static_val.is_integer()
#       else None
#     )

#     t_n = str(n)

#     # ---- 1/3 <-> static equivalent ----
#     if (
#       t_static and
#       "1/3" in avg_time.columns and
#       t_static in avg_time.columns
#     ):

#       v_static = avg_time.loc[n, t_static]
#       v_n3 = avg_time.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "1/3"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_n3):
#         avg_time_filled.loc[n, t_static] = v_n3

#     # ---- num_trains <-> n equivalent ----
#     if (
#       "num_trains" in avg_time.columns and
#       t_n in avg_time.columns
#     ):

#       v_static = avg_time.loc[n, t_n]
#       v_nval = avg_time.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "num_trains"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_nval):
#         avg_time_filled.loc[n, t_n] = v_nval

#   results_time[algo_name] = avg_time_filled

# # GLOBAL Y SCALE
# all_times = []

# for df in results_time.values():

#   vals = df.values.flatten()
#   vals = vals[~pd.isna(vals)]
#   vals = vals[vals > 0]

#   all_times.extend(vals)

# all_times = np.array(all_times)

# nonzero_times = all_times[
#   all_times > 0
# ]

# y_min = (
#   nonzero_times.min() * 0.8
#   if len(nonzero_times) > 0
#   else 0.1
# )

# y_max = 35

# # PLOT TIME PER TYPE
# for t in all_types:

#   plt.figure()

#   for algo_name, df_algo in results_time.items():

#     if t not in df_algo.columns:
#       continue

#     x = df_algo.index
#     y = df_algo[t]

#     plt.plot(
#       x,
#       y,
#       label=algo_name,
#       **algo_colors[algo_name],
#     )

#   plt.xlabel("Number of Trains")
#   plt.ylabel("Time (minutes)")

#   plt.xticks(x_ticks)

#   plt.yscale("log")

#   minute_ticks = [1, 2, 5, 10, 20, 30]

#   plt.ylim(
#     0.007891121555555556,
#     y_max
#   )

#   plt.yticks(
#     minute_ticks,
#     labels=minute_ticks
#   )

#   plt.grid(
#     True,
#     which="both",
#     linestyle="--",
#     linewidth=0.5
#   )

#   if t == "1/3":
#     plt.title(
#       "n/3 Types: Average Time "
#       "(Common Solved Instances)"
#     )

#   elif t == "num_trains":
#     plt.title(
#       "n Types: Average Time "
#       "(Common Solved Instances)"
#     )

#   else:
#     plt.title(
#       f"{t} Types: Average Time "
#       "(Common Solved Instances)"
#     )

#   plt.legend()

#   os.makedirs(
#     "../plots/types_7hours",
#     exist_ok=True
#   )

#   filename_t = t.replace("/", "_")

#   plt.savefig(
#     f"../plots/types_7hours_continuous/"
#     f"time_type_{filename_t}_common.png",
#     dpi=300,
#     bbox_inches="tight"
#   )

#   plt.close()

import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import math

# This code plots the average computation time
# for instances solved by all algorithms,
# combined over all 120 instances.

algo_colors = {
  "ADMM": {
    "color": "#1f77b4",
    "linestyle": "-",
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "#1f77b4",
    "markeredgecolor": "#1f77b4",
  },

  "Continuous ADMM": {
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
  "Continuous ADMM": "../../data/data_types_7hours/sp_continuous_results_common.csv",
  "ADMM": "../../data/data_types_7hours/sp_results_common.csv",
  "Continuous LS": "../../data/data_types_7hours/results_ls_continuous/combined_results_common.csv",
  "Discrete LS": "../../data/data_types_7hours/results_ls_discreet/combined_results_common.csv"
}

x_ticks = [5, 10, 15, 20, 25, 30]

results_time = {}

# ============================================================
# LOAD ALL DATAFRAMES
# ============================================================

dfs = {}

for algo_name, file_path in algorithms.items():

  df = pd.read_csv(file_path)

  # ----------------------------------------------------------
  # NORMALIZE COLUMN NAMES
  # ----------------------------------------------------------

  if "found" in df.columns:

    df["solution_found"] = (
      df["found"].astype(str) == "True"
    )

  # ----------------------------------------------------------
  # PARSE COMPUTATION TIME
  # ----------------------------------------------------------

  if "computation_time" in df.columns:

    # ADMM
    df["time_seconds"] = pd.to_numeric(
      df["computation_time"],
      errors="coerce"
    )

  elif "total_computation_time" in df.columns:

    # LS -> HH:MM:SS
    df["time_seconds"] = pd.to_timedelta(
      df["total_computation_time"]
    ).dt.total_seconds()

  # ----------------------------------------------------------
  # EXTRACT num_trains + type
  # ----------------------------------------------------------

  extracted = df["filename"].str.extract(
    r"solver_(\d+)_trains_(.+)_units\d+"
  )

  df["num_trains"] = extracted[0].astype(int)

  raw_type = extracted[1]

  # ----------------------------------------------------------
  # NORMALIZE TYPE
  # ----------------------------------------------------------

  def normalize_type(type_value, num_trains):

    type_int = int(type_value)

    # n types
    if type_int == num_trains:
      return "num_trains"

    # n/3 types
    if type_int == math.ceil(num_trains / 3):
      return "1/3"

    return str(type_int)

  df["type"] = [
    normalize_type(t, n)
    for t, n in zip(
      raw_type,
      df["num_trains"]
    )
  ]

  # ----------------------------------------------------------
  # CREATE UNIQUE INSTANCE KEY
  # ----------------------------------------------------------

  df["instance_key"] = df["filename"]

  dfs[algo_name] = df

# ============================================================
# KEEP ONLY INSTANCES SOLVED BY ALL ALGORITHMS
# ============================================================

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

# ============================================================
# COMPUTE AVERAGE TIMES
# ============================================================

for algo_name, df in dfs.items():

  df_filtered = df[
    df["instance_key"].isin(common_instances)
  ].copy()

  # ----------------------------------------------------------
  # CONVERT TO MINUTES
  # ----------------------------------------------------------

  df_filtered["time_minutes"] = (
    df_filtered["time_seconds"] / 60
  )

  # ----------------------------------------------------------
  # GROUP BY TRAIN + TYPE
  # ----------------------------------------------------------

  avg_time = (
    df_filtered
    .groupby(["num_trains", "type"])[
      "time_minutes"
    ]
    .mean()
    .unstack()
  )

  avg_time_filled = avg_time.copy()

  # ----------------------------------------------------------
  # FILL EQUIVALENT TYPES
  # ----------------------------------------------------------

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

  # ----------------------------------------------------------
  # COMBINE ALL TYPES INTO ONE VALUE
  # ----------------------------------------------------------

  combined_time = avg_time_filled.mean(axis=1)

  results_time[algo_name] = combined_time

# ============================================================
# GLOBAL Y SCALE
# ============================================================

all_times = []

for series in results_time.values():

  vals = series.values
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

# ============================================================
# PLOT
# ============================================================

plt.figure()

for algo_name, series in results_time.items():

  plt.plot(
    series.index,
    series.values,
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

plt.title(
  "Average Time (Common Solved "
  "Instances)"
)

plt.legend()

os.makedirs(
  "../plots/types_7hours",
  exist_ok=True
)

plt.savefig(
  "../plots/types_7hours_continuous/"
  "time_all_instances_common.png",
  dpi=300,
  bbox_inches="tight"
)

plt.close()