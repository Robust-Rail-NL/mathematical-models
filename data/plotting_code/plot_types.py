import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# This code plots the number of feasible solutions found
# and the average computation time for each algorithm

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
  "Continuous ADMM": "../../data/data_types_7hours/sp_continuous_results.csv",
  "ADMM": "../../data/data_types_7hours/sp_results.csv",
  "Continuous LS": "../../data/data_types_7hours/results_ls_continuous/combined_results.csv",
  "Discrete LS": "../../data/data_types_7hours/results_ls_discreet/combined_results.csv"
}

x_ticks = [5,10,15,20,25,30]
all_types = ["1", "5", "1/3", "num_trains"]

results_time = {}
results_solved = {}

# COLLECT DATA PER ALGO
for algo_name, file_path in algorithms.items():
  df = pd.read_csv(file_path)
  df["solution_found"] = df["solution_found"].astype(bool)
  df["type"] = df["type"].astype(str)

  df.loc[~df["solution_found"], "time"] = 30*60

  # TIME
  df_time = df.copy()
  df_time["time"] = df_time["time"] / 60

  avg_time = df_time.groupby(["num_trains","type"])["time"].mean().unstack()
  avg_time_filled = avg_time.copy()

  for n in avg_time.index:
    t_static_val = n / 3
    t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
    t_n = str(n)

    if t_static and "1/3" in avg_time.columns and t_static in avg_time.columns:
      v_static = avg_time.loc[n, t_static]
      v_n3 = avg_time.loc[n, "1/3"]

      if pd.isna(v_n3) and not pd.isna(v_static):
        avg_time_filled.loc[n, "1/3"] = v_static
      if pd.isna(v_static) and not pd.isna(v_n3):
        avg_time_filled.loc[n, t_static] = v_n3

    if "num_trains" in avg_time.columns and t_n in avg_time.columns:
      v_static = avg_time.loc[n, t_n]
      v_nval = avg_time.loc[n, "num_trains"]

      if pd.isna(v_nval) and not pd.isna(v_static):
        avg_time_filled.loc[n, "num_trains"] = v_static
      if pd.isna(v_static) and not pd.isna(v_nval):
        avg_time_filled.loc[n, t_n] = v_nval

  results_time[algo_name] = avg_time_filled

  # ---- SOLVED ----
  solved_count = df.groupby(["num_trains", "type"])["solution_found"].sum().unstack()
  solved_count_filled = solved_count.copy()

  for n in solved_count.index:
    t_static_val = n / 3
    t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
    t_n = str(n)

    if t_static and "1/3" in solved_count.columns and t_static in solved_count.columns:
      v_static = solved_count.loc[n, t_static]
      v_n3 = solved_count.loc[n, "1/3"]

      if pd.isna(v_n3) and not pd.isna(v_static):
        solved_count_filled.loc[n, "1/3"] = v_static
      if pd.isna(v_static) and not pd.isna(v_n3):
        solved_count_filled.loc[n, t_static] = v_n3

    if "num_trains" in solved_count.columns and t_n in solved_count.columns:
      v_static = solved_count.loc[n, t_n]
      v_nval = solved_count.loc[n, "num_trains"]

      if pd.isna(v_nval) and not pd.isna(v_static):
        solved_count_filled.loc[n, "num_trains"] = v_static
      if pd.isna(v_static) and not pd.isna(v_nval):
        solved_count_filled.loc[n, t_n] = v_nval

  results_solved[algo_name] = solved_count_filled


# GLOBAL Y-SCALE (TIME)
all_times = []
for df in results_time.values():
  vals = df.values.flatten()
  vals = vals[~pd.isna(vals)]
  vals = vals[vals > 0]
  all_times.extend(vals)

y_min = min(all_times) * 0.8 if len(all_times) > 0 else 0.1
y_max = 35

for t in all_types:
  plt.figure()

  for algo_name, df_algo in results_time.items():
    if t in df_algo.columns:
      x = df_algo.index
      y = df_algo[t]

      plt.plot(
        x, y,
        label=algo_name,
        **algo_colors[algo_name],
      )

  plt.xlabel("Number of Trains")
  plt.ylabel("Time (minutes)")
  plt.xticks(x_ticks)
  plt.yscale("log")

  minute_ticks = [1,2,5,10,20,30]
  y_max = 35

  all_times = []
  for df in results_time.values():
    vals = df.values.flatten()
    vals = vals[~pd.isna(vals)]
    all_times.extend(vals)

  all_times = np.array(all_times)
  nonzero_times = all_times[all_times > 0]
  y_min = nonzero_times.min() * 0.8 if len(nonzero_times) > 0 else 0.1

  plt.ylim(0.007891121555555556, y_max)
  print(y_min)

  plt.yticks(minute_ticks, labels=minute_ticks)

  plt.grid(True, which="both", linestyle="--", linewidth=0.5)
  if t == "1/3":
    plt.title(f"n/3 Types: Average Time")
  elif t == "num_trains":
    plt.title(f"n Types: Average Time")
  else:
    plt.title(f"{t} Types: Average Time")
  plt.legend()

  filename_t = t.replace("/", "_")
  plt.savefig(f"../plots/types_7hours_continuous/time_type_{filename_t}.png", dpi=300, bbox_inches="tight")
  plt.close()


# SOLVED PLOTS PER TYPE
for t in all_types:
  plt.figure()

  for algo_name, df_algo in results_solved.items():
    if t in df_algo.columns:
      x = df_algo.index
      y = df_algo[t]

      plt.plot(x, y, label=algo_name, **algo_colors[algo_name])

  plt.xlabel("Number of Trains")
  plt.ylabel("Solved Instances")
  plt.xticks(x_ticks)
  plt.ylim(0, 32)

  plt.grid(True, linestyle="--", linewidth=0.5)
  if t == "1/3":
    plt.title(f"n/3 Types: Solved Instances")
  elif t == "num_trains":
    plt.title(f"n Types: Solved Instances")
  else:
    plt.title(f"{t} Types: Solved Instances")
  plt.legend()

  filename_t = t.replace("/", "_")
  plt.savefig(f"../plots/types_7hours_continuous/solved_type_{filename_t}.png", dpi=300, bbox_inches="tight")
  plt.close()


# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np

# # This code plots:
# #  average computation time over ALL 120 instances
# #  total solved instances over ALL 120 instances

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
#   "Continuous ADMM": "../../data/data_types_7hours/sp_continuous_results.csv",
#   "ADMM": "../../data/data_types_7hours/sp_results.csv",
#   "Continuous LS": "../../data/data_types_7hours/results_ls_continuous/combined_results.csv",
#   "Discrete LS": "../../data/data_types_7hours/results_ls_discreet/combined_results.csv"
# }

# x_ticks = [5, 10, 15, 20, 25, 30]

# results_time = {}
# results_solved = {}

# # ============================================================
# # COLLECT DATA PER ALGORITHM
# # ============================================================

# for algo_name, file_path in algorithms.items():

#   df = pd.read_csv(file_path)

#   df["solution_found"] = df["solution_found"].astype(bool)
#   df["type"] = df["type"].astype(str)

#   # failed instances count as timeout
#   df.loc[~df["solution_found"], "time"] = 30 * 60

#   # ==========================================================
#   # TIME
#   # ==========================================================

#   df_time = df.copy()
#   df_time["time"] = df_time["time"] / 60

#   avg_time = (
#     df_time
#     .groupby(["num_trains", "type"])["time"]
#     .mean()
#     .unstack()
#   )

#   avg_time_filled = avg_time.copy()

#   # ----------------------------------------------------------
#   # FILL EQUIVALENT CATEGORIES
#   # ----------------------------------------------------------

#   for n in avg_time.index:

#     t_static_val = n / 3
#     t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
#     t_n = str(n)

#     # n/3 <-> static type

#     if (
#       t_static
#       and "1/3" in avg_time.columns
#       and t_static in avg_time.columns
#     ):

#       v_static = avg_time.loc[n, t_static]
#       v_n3 = avg_time.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "1/3"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_n3):
#         avg_time_filled.loc[n, t_static] = v_n3

#     # num_trains <-> static n

#     if (
#       "num_trains" in avg_time.columns
#       and t_n in avg_time.columns
#     ):

#       v_static = avg_time.loc[n, t_n]
#       v_nval = avg_time.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         avg_time_filled.loc[n, "num_trains"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_nval):
#         avg_time_filled.loc[n, t_n] = v_nval

#   # ----------------------------------------------------------
#   # COMBINE ALL TYPES INTO ONE VALUE
#   # ----------------------------------------------------------

#   combined_time = avg_time_filled.mean(axis=1)

#   results_time[algo_name] = combined_time

#   # ==========================================================
#   # SOLVED
#   # ==========================================================

#   solved_count = (
#     df
#     .groupby(["num_trains", "type"])["solution_found"]
#     .sum()
#     .unstack()
#   )

#   solved_count_filled = solved_count.copy()

#   # ----------------------------------------------------------
#   # FILL EQUIVALENT CATEGORIES
#   # ----------------------------------------------------------

#   for n in solved_count.index:

#     t_static_val = n / 3
#     t_static = str(int(t_static_val)) if t_static_val.is_integer() else None
#     t_n = str(n)

#     # n/3 <-> static type

#     if (
#       t_static
#       and "1/3" in solved_count.columns
#       and t_static in solved_count.columns
#     ):

#       v_static = solved_count.loc[n, t_static]
#       v_n3 = solved_count.loc[n, "1/3"]

#       if pd.isna(v_n3) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "1/3"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_n3):
#         solved_count_filled.loc[n, t_static] = v_n3

#     # num_trains <-> static n

#     if (
#       "num_trains" in solved_count.columns
#       and t_n in solved_count.columns
#     ):

#       v_static = solved_count.loc[n, t_n]
#       v_nval = solved_count.loc[n, "num_trains"]

#       if pd.isna(v_nval) and not pd.isna(v_static):
#         solved_count_filled.loc[n, "num_trains"] = v_static

#       if pd.isna(v_static) and not pd.isna(v_nval):
#         solved_count_filled.loc[n, t_n] = v_nval

#   # ----------------------------------------------------------
#   # COMBINE ALL TYPES INTO TOTAL OUT OF 120
#   # ----------------------------------------------------------

#   combined_solved = solved_count_filled.sum(axis=1)

#   results_solved[algo_name] = combined_solved

# # ============================================================
# # GLOBAL Y-SCALE (TIME)
# # ============================================================

# all_times = []

# for series in results_time.values():

#   vals = series.values
#   vals = vals[vals > 0]

#   all_times.extend(vals)

# y_min = min(all_times) * 0.8 if len(all_times) > 0 else 0.1
# y_max = 35

# # ============================================================
# # TIME PLOT
# # ============================================================

# plt.figure()

# for algo_name, series in results_time.items():

#   plt.plot(
#     series.index,
#     series.values,
#     label=algo_name,
#     **algo_colors[algo_name],
#   )

# plt.xlabel("Number of Trains")
# plt.ylabel("Average Time (minutes)")

# plt.xticks(x_ticks)

# plt.yscale("log")

# minute_ticks = [1, 2, 5, 10, 20, 30]

# plt.yticks(minute_ticks, labels=minute_ticks)

# plt.ylim(0.007891121555555556, y_max)

# plt.grid(True, which="both", linestyle="--", linewidth=0.5)

# plt.title("Average Time")

# plt.legend()

# plt.savefig(
#   "../plots/types_7hours_continuous/time_all_instances.png",
#   dpi=300,
#   bbox_inches="tight"
# )

# plt.close()

# # ============================================================
# # SOLVED PLOT
# # ============================================================

# plt.figure()

# for algo_name, series in results_solved.items():

#   plt.plot(
#     series.index,
#     series.values,
#     label=algo_name,
#     **algo_colors[algo_name],
#   )

# plt.xlabel("Number of Trains")
# plt.ylabel("Solved Instances")

# plt.xticks(x_ticks)

# plt.ylim(0, 125)

# plt.grid(True, linestyle="--", linewidth=0.5)

# plt.title("Solved Instances")

# # plt.legend()
# plt.legend(loc="lower left")

# plt.savefig(
#   "../plots/types_7hours_continuous/solved_all_instances.png",
#   dpi=300,
#   bbox_inches="tight"
# )

# plt.close()