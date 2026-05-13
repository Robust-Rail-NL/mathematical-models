import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os


algo_colors = {
  "ADMM": {
    "color": "#1f77b4",  # blue
    "linestyle": "-",
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "#1f77b4",
    "markeredgecolor": "#1f77b4",
  },

  "ADMM Continuous": {
    "color": "#5fa6d9",  # lighter blue
    "linestyle": (0, (2, 2)),
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "none",
    "markeredgecolor": "#5fa6d9",
  },

  "LS Continuous": {
    "color": "#ff7f7f",  # lighter red
    "linestyle": (0, (1, 4)),
    "marker": "o",
    "markersize": 6,
    "markerfacecolor": "none",
    "markeredgecolor": "#ff7f7f",
  },

  "Discrete LS": {
    "color": "#d62728",  # red
    "linestyle": "-",
    "marker": "o",
    "markersize": 6,
    "markerfacecolor": "#d62728",
    "markeredgecolor": "#d62728",
  }
}

selected_algorithms = {
  "ADMM": "results_time_20_sp",
  "Discrete LS": "results_ls_discreet_time_20"
}

results_time_end = {}
results_solved_end = {}

# =========================
# COLLECT DATA PER ALGO (END TIME BASED)
# =========================
for algo_name, folder in selected_algorithms.items():
  df = pd.read_csv(f"{folder}/combined_results.csv")

  df["solution_found"] = df["solution_found"].astype(bool)
  
  # IMPORTANT: make sure this column exists in your CSV
  # rename if needed
  df["end_time"] = df["end_time"]

  # cap unsolved
  df.loc[~df["solution_found"], "time"] = 30*60

  # ---- TIME ----
  # ---- TIME (ONLY SOLVED INSTANCES) ----
  # df_time = df[df["solution_found"]].copy()   # filter solved only
  # df_time["time"] = df_time["time"] / 60

  df_time = df.copy()
  df_time["time"] = df_time["time"] / 60

  avg_time = df_time.groupby("end_time")["time"].mean()
  print(f"\nAverage time (minutes) for {algo_name}:")
  print(avg_time)
  results_time_end[algo_name] = avg_time

  # ---- SOLVED ----
  solved = df.groupby("end_time")["solution_found"].sum()
  results_solved_end[algo_name] = solved


# =========================
# SORT X-AXIS
# =========================
all_end_times = sorted(set().union(*[df.index for df in results_time_end.values()]))


# =========================
# PLOT 1: FEASIBLE SOLUTIONS
# =========================
plt.figure()

for algo_name, series in results_solved_end.items():
  x = series.index
  y = series.values

  plt.plot(
    x, y,
    label=algo_name,
    **algo_colors[algo_name]
  )

plt.xlabel("Time Window (seconds)")
plt.ylabel("Number of Feasible Solutions")
plt.xticks(all_end_times)
plt.ylim(0, 32)

plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.title("Feasible Solutions vs Time Window")

os.makedirs("results/end_time_sp", exist_ok=True)
plt.savefig("results/end_time_sp/feasible_vs_endtime.png", dpi=300, bbox_inches="tight")
plt.close()


# =========================
# PLOT 2: TIME TO SOLUTION
# =========================
plt.figure()

for algo_name, series in results_time_end.items():
  x = series.index
  y = series.values

  plt.plot(
    x, y,
    label=algo_name,
    **algo_colors[algo_name]
  )

plt.xlabel("Time Window (seconds)")
plt.ylabel("Average Computation Time (minutes)")  # ✅ explicit minutes
plt.xticks(all_end_times)

plt.yscale("log")

# same tick style as your original
minute_ticks = [0.5, 1, 2, 5, 10, 20, 30]
plt.yticks(minute_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.legend()
plt.title("Average Computation Time vs Time Window")

# 🔁 overwrite existing
plt.savefig("results/end_time_sp/time_vs_endtime.png", dpi=300, bbox_inches="tight")
plt.close()



# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
# import os


# algo_colors = {
#   "ADMM": {
#     "color": "#1f77b4",
#     "linestyle": "-",
#     "marker": "s",
#     "markersize": 6,
#     "markerfacecolor": "#1f77b4",
#     "markeredgecolor": "#1f77b4",
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

# selected_algorithms = {
#   "ADMM": "results_time_20_sp",
#   "LS Discrete": "results_ls_discreet_time_20"
# }

# dfs = {}

# # =========================
# # LOAD DATA
# # =========================
# for algo_name, folder in selected_algorithms.items():

#   df = pd.read_csv(f"{folder}/combined_results_2.csv")

#   # Standardize column names
#   df = df.rename(columns={
#     "found": "solution_found",
#     "endtime": "end_time"
#   })

#   # -------------------------
#   # HANDLE COMPUTATION TIME
#   # -------------------------
#   if algo_name == "ADMM":

#     # already in seconds
#     df["time_seconds"] = pd.to_numeric(
#       df["computation_time"]
#     )

#     # remove "scenario_" prefix
#     df["base_filename"] = (
#       df["filename"]
#       .str.replace("^scenario_", "", regex=True)
#     )

#   elif algo_name == "LS Discrete":

#     # convert hh:mm:ss.microseconds -> seconds
#     td = pd.to_timedelta(
#       df["total_computation_time"]
#     )

#     df["time_seconds"] = td.dt.total_seconds()

#     df["base_filename"] = df["filename"]

#   # -------------------------
#   # TYPES
#   # -------------------------
#   df["solution_found"] = (
#     df["solution_found"]
#     .astype(bool)
#   )

#   df["end_time"] = pd.to_numeric(
#     df["end_time"]
#   )

#   # unique instance identifier
#   df["instance_id"] = (
#     df["base_filename"].astype(str)
#     + "_"
#     + df["end_time"].astype(str)
#   )

#   dfs[algo_name] = df


# # =========================
# # FIND COMMON SOLVED INSTANCES
# # =========================
# common_instances = None

# for algo_name, df in dfs.items():

#   solved_instances = set(
#     df.loc[
#       df["solution_found"],
#       "instance_id"
#     ]
#   )

#   if common_instances is None:
#     common_instances = solved_instances
#   else:
#     common_instances = (
#       common_instances.intersection(
#         solved_instances
#       )
#     )

# print(
#   f"Instances solved by all algorithms: "
#   f"{len(common_instances)}"
# )


# # =========================
# # COMPUTE AVERAGE TIMES
# # =========================
# results_time_end = {}

# for algo_name, df in dfs.items():

#   df_filtered = df[
#     df["instance_id"].isin(common_instances)
#   ].copy()

#   # convert seconds -> minutes
#   df_filtered["time_minutes"] = (
#     df_filtered["time_seconds"] / 60
#   )

#   avg_time = (
#     df_filtered
#     .groupby("end_time")["time_minutes"]
#     .mean()
#   )

#   print(f"\nAverage time (minutes) for {algo_name}:")
#   print(avg_time)

#   results_time_end[algo_name] = avg_time


# # =========================
# # SORT X-AXIS
# # =========================
# all_end_times = sorted(
#   set().union(
#     *[
#       series.index
#       for series in results_time_end.values()
#     ]
#   )
# )


# # =========================
# # PLOT
# # =========================
# plt.figure()

# for algo_name, series in results_time_end.items():
#   if algo_name == "LS Discrete":
#     algo_name = "Discrete LS"
#   plt.plot(
#     series.index,
#     series.values,
#     label=algo_name,
#     **algo_colors[algo_name]
#   )

# plt.xlabel("Time Window (seconds)")
# plt.ylabel("Average Computation Time (minutes)")

# plt.xticks(all_end_times)

# plt.yscale("log")

# minute_ticks = [0.5, 1, 2, 5, 10, 20, 30]
# plt.yticks(
#   minute_ticks,
#   labels=minute_ticks
# )

# plt.grid(
#   True,
#   which="both",
#   linestyle="--",
#   linewidth=0.5
# )

# plt.legend()

# plt.title(
#   "Average Computation Time vs Time Window"
# )

# os.makedirs(
#   "results/end_time_sp",
#   exist_ok=True
# )

# plt.savefig(
#   "results/end_time_sp/time_vs_endtime_common.png",
#   dpi=300,
#   bbox_inches="tight"
# )

# plt.close()