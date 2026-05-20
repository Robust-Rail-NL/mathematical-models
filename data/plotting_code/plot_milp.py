import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# This code plots the feasible solutions found and 
# the average computation time for MILP

# LOAD DATA
df = pd.read_csv("../../data/data_milp/milp_results.csv")

df["solution_found"] = df["solution_found"].astype(bool)

# Penalize unsolved runs (same as before: 30 min)
df.loc[~df["solution_found"], "time"] = 30 * 60

# TIME (AVERAGE)
df_time = df.copy()
df_time["time"] = df_time["time"] / 60  # seconds → minutes

avg_time = df_time.groupby("num_trains")["time"].mean()

# SOLVED COUNT
solved_count = df.groupby("num_trains")["solution_found"].sum()

# TIME PLOT
plt.figure()

plt.plot(
    avg_time.index,
    avg_time.values,
    color="0.0",
    linestyle=(0, (2, 2)),
    marker="o",
    markersize=6,
    label="MILP"
)

plt.xlabel("Number of Trains")
plt.ylabel("Time (minutes)")
plt.xticks([5, 10, 15, 20])
plt.yscale("log")

# same scaling style as your original
minute_ticks = [1, 2, 5, 10, 20, 30]
plt.ylim(0.007891121555555556, 35)
plt.yticks(minute_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.title("Average Time (MILP)")
plt.legend()

plt.savefig("../plots/milp/time_milp.png", dpi=300, bbox_inches="tight")
plt.close()


# SOLVED PLOT
plt.figure()

plt.plot(
    solved_count.index,
    solved_count.values,
    color="0.0",
    linestyle=(0, (2, 2)),
    marker="o",
    markersize=6,
    label="MILP"
)

plt.xlabel("Number of Trains")
plt.ylabel("Feasible Solutions Found")
plt.xticks([5, 10, 15, 20])
plt.ylim(0, 22)  # as requested

plt.grid(True, linestyle="--", linewidth=0.5)
plt.title("Feasible Solutions Found (MILP)")
plt.legend()

plt.savefig("../plots/milp/solved_milp.png", dpi=300, bbox_inches="tight")
plt.close()