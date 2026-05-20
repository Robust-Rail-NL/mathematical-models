import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# This code plots the number of feasible solutions and the 
# average compuation time for different time window

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
  "ADMM": "../../data/data_time_window/sp_results.csv",
  "Discrete LS": "../../data/data_time_window/results_ls_dsicreet/combined_results.csv"
}

results_time_end = {}
results_solved_end = {}

# COLLECT DATA PER ALGO (END TIME BASED)
for algo_name, file_path in selected_algorithms.items():
  df = pd.read_csv(file_path)

  df["solution_found"] = df["solution_found"].astype(bool)
  
  df["end_time"] = df["end_time"]

  # cap unsolved
  df.loc[~df["solution_found"], "time"] = 30*60

  df_time = df.copy()
  df_time["time"] = df_time["time"] / 60

  avg_time = df_time.groupby("end_time")["time"].mean()
  print(f"\nAverage time (minutes) for {algo_name}:")
  print(avg_time)
  results_time_end[algo_name] = avg_time

  # ---- SOLVED ----
  solved = df.groupby("end_time")["solution_found"].sum()
  results_solved_end[algo_name] = solved


# SORT X-AXIS
all_end_times = sorted(set().union(*[df.index for df in results_time_end.values()]))


# PLOT 1: FEASIBLE SOLUTIONS
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

os.makedirs("../plots/end_time_sp", exist_ok=True)
plt.savefig("../plots/end_time_sp/feasible_vs_endtime.png", dpi=300, bbox_inches="tight")
plt.close()


# PLOT 2: TIME TO SOLUTION
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
plt.ylabel("Average Computation Time (minutes)")
plt.xticks(all_end_times)

plt.yscale("log")

# same tick style as your original
minute_ticks = [0.5, 1, 2, 5, 10, 20, 30]
plt.yticks(minute_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.legend()
plt.title("Average Computation Time vs Time Window")

# overwrite existing
plt.savefig("../plots/end_time_sp/time_vs_endtime.png", dpi=300, bbox_inches="tight")
plt.close()