import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# This code plots the average computation time for each algorithm for
# the instances solved by all algorithms, for different time windows

algo_colors = {
  "ADMM": {
    "color": "#1f77b4",
    "linestyle": "-",
    "marker": "s",
    "markersize": 6,
    "markerfacecolor": "#1f77b4",
    "markeredgecolor": "#1f77b4",
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

selected_algorithms = {
  "ADMM": "../../data/data_time_window/sp_results_common.csv",
  "Discrete LS": "../../data/data_time_window/results_ls_dsicreet/combined_results_common.csv"
}

dfs = {}

# LOAD DATA
for algo_name, file_path in selected_algorithms.items():

  df = pd.read_csv(file_path)

  # Standardize column names
  df = df.rename(columns={
    "found": "solution_found",
    "endtime": "end_time"
  })


  # HANDLE COMPUTATION TIME

  if algo_name == "ADMM":

    # already in seconds
    df["time_seconds"] = pd.to_numeric(
      df["computation_time"]
    )

    # remove "scenario_" prefix
    df["base_filename"] = (
      df["filename"]
      .str.replace("^scenario_", "", regex=True)
    )

  elif algo_name == "LS Discrete":

    # convert hh:mm:ss.microseconds -> seconds
    td = pd.to_timedelta(
      df["total_computation_time"]
    )

    df["time_seconds"] = td.dt.total_seconds()

    df["base_filename"] = df["filename"]


  # TYPES

  df["solution_found"] = (
    df["solution_found"]
    .astype(bool)
  )

  df["end_time"] = pd.to_numeric(
    df["end_time"]
  )

  # unique instance identifier
  df["instance_id"] = (
    df["base_filename"].astype(str)
    + "_"
    + df["end_time"].astype(str)
  )

  dfs[algo_name] = df


# FIND COMMON SOLVED INSTANCES
common_instances = None

for algo_name, df in dfs.items():

  solved_instances = set(
    df.loc[
      df["solution_found"],
      "instance_id"
    ]
  )

  if common_instances is None:
    common_instances = solved_instances
  else:
    common_instances = (
      common_instances.intersection(
        solved_instances
      )
    )

print(
  f"Instances solved by all algorithms: "
  f"{len(common_instances)}"
)


# COMPUTE AVERAGE TIMES
results_time_end = {}

for algo_name, df in dfs.items():

  df_filtered = df[
    df["instance_id"].isin(common_instances)
  ].copy()

  # convert seconds -> minutes
  df_filtered["time_minutes"] = (
    df_filtered["time_seconds"] / 60
  )

  avg_time = (
    df_filtered
    .groupby("end_time")["time_minutes"]
    .mean()
  )

  print(f"\nAverage time (minutes) for {algo_name}:")
  print(avg_time)

  results_time_end[algo_name] = avg_time


# SORT X-AXIS
all_end_times = sorted(
  set().union(
    *[
      series.index
      for series in results_time_end.values()
    ]
  )
)


# PLOT
plt.figure()

for algo_name, series in results_time_end.items():
  if algo_name == "LS Discrete":
    algo_name = "Discrete LS"
  plt.plot(
    series.index,
    series.values,
    label=algo_name,
    **algo_colors[algo_name]
  )

plt.xlabel("Time Window (seconds)")
plt.ylabel("Average Computation Time (minutes)")

plt.xticks(all_end_times)

plt.yscale("log")

minute_ticks = [0.5, 1, 2, 5, 10, 20, 30]
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

plt.legend()

plt.title(
  "Average Computation Time vs Time Window"
)

os.makedirs(
  "results/end_time_sp",
  exist_ok=True
)

plt.savefig(
  "../plots/end_time_sp/time_vs_endtime_common.png",
  dpi=300,
  bbox_inches="tight"
)

plt.close()