import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

type_colors = {
  "1": "#bdd7e7",
  "5": "#6baed6",
  "1/3": "#3182bd",
  "num_trains": "#08519c"
}

algo_colors = {
  "ALR": "#1f77b4",
  "LS Continuous": "#ff7f0e",
  "LS Discreet": "#2ca02c"
}

algorithms = {
  "ALR": "results_types_360",
  "LS Continuous": "data_types_360/results_ls",
  "LS Discreet": "data_types_360/results_ls_discreet"
}

x_ticks = [5,10,15,20,25,30]
all_types = ["1", "5", "1/3", "num_trains"]

results_time = {}
results_solved = {}

# =========================
# COLLECT DATA PER ALGO
# =========================
for algo_name, folder in algorithms.items():
  df = pd.read_csv(f"{folder}/combined_results.csv")
  df["solution_found"] = df["solution_found"].astype(bool)
  df["type"] = df["type"].astype(str)

  df.loc[~df["solution_found"], "time"] = 30*60

  # ---- TIME ----
  df_time = df.copy()
  df_time["time"] = df_time["time"] / 60

  avg_time = df_time.groupby(["num_trains","type"])["time"].mean().unstack()
  avg_time_filled = avg_time.copy()

  for n in avg_time.index:
    # t_static = str(int(n / 3))
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
    # t_static = str(int(n / 3))
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


# =========================
# GLOBAL Y-SCALE (TIME)
# =========================
all_times = []
for df in results_time.values():
  vals = df.values.flatten()
  vals = vals[~pd.isna(vals)]
  vals = vals[vals > 0]
  all_times.extend(vals)

y_min = min(all_times) * 0.8 if len(all_times) > 0 else 0.1
y_max = 35


# =========================
# TIME PLOTS PER TYPE
# =========================
# for t in all_types:
#   plt.figure()

#   for algo_name, df_algo in results_time.items():
#     if t in df_algo.columns:
#       x = df_algo.index
#       y = df_algo[t]

#       plt.plot(
#         x, y,
#         marker='o',
#         color=type_colors[t],
#         label=algo_name
#       )

#   plt.xlabel("Number of trains")
#   plt.ylabel("Time (minutes)")
#   plt.xticks(x_ticks)
#   plt.yscale("log")

#   plt.ylim(y_min, y_max)
#   plt.yticks([1,2,5,10,20,30])

#   plt.grid(True, which="both", linestyle="--", linewidth=0.5)
#   plt.title(f"Type {t}: Average Time")
#   plt.legend()

#   filename_t = t.replace("/", "_")
#   os.makedirs("results/360", exist_ok=True)
#   plt.savefig(f"results/360/time_type_{filename_t}.png", dpi=300, bbox_inches="tight")
#   plt.close()
for t in all_types:
  plt.figure()

  for algo_name, df_algo in results_time.items():
    if t in df_algo.columns:
      x = df_algo.index
      y = df_algo[t]

      plt.plot(
        x, y,
        marker='o',
        color=algo_colors[algo_name],
        label=algo_name
      )

  plt.xlabel("Number of trains")
  plt.ylabel("Time (minutes)")
  plt.xticks(x_ticks)
  plt.yscale("log")

  # ---- EXACTLY your original scaling ----
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
  plt.title(f"Type {t}: Average Time")
  plt.legend()

  filename_t = t.replace("/", "_")
  plt.savefig(f"results/360/time_type_{filename_t}.png", dpi=300, bbox_inches="tight")
  plt.close()


# =========================
# SOLVED PLOTS PER TYPE
# =========================
for t in all_types:
  plt.figure()

  for algo_name, df_algo in results_solved.items():
    if t in df_algo.columns:
      x = df_algo.index
      y = df_algo[t]

      plt.plot(x, y, marker='o', color=algo_colors[algo_name], label=algo_name)

  plt.xlabel("Number of trains")
  plt.ylabel("Solved instances")
  plt.xticks(x_ticks)
  plt.ylim(0, 32)

  plt.grid(True, linestyle="--", linewidth=0.5)
  plt.title(f"Type {t}: Solved instances")
  plt.legend()

  filename_t = t.replace("/", "_")
  plt.savefig(f"results/360/solved_type_{filename_t}.png", dpi=300, bbox_inches="tight")
  plt.close()

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
#   "ALR": "results_types_360",
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
