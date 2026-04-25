import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Only keep the two algorithms you want
selected_algorithms = {
    "ALR": "results_time_20",
    "LS Discreet": "results_ls_discreet_time_20"
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
    df_time = df[df["solution_found"]].copy()   # filter solved only
    df_time["time"] = df_time["time"] / 60

    # df_time = df.copy()
    # df_time["time"] = df_time["time"] / 60

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
        marker='o',
        label=algo_name
    )

plt.xlabel("End time")
plt.ylabel("Number of feasible solutions")
plt.xticks(all_end_times)

plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.title("Feasible solutions vs End time")

os.makedirs("results/end_time", exist_ok=True)
plt.savefig("results/end_time/feasible_vs_endtime.png", dpi=300, bbox_inches="tight")
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
        marker='o',
        label=algo_name
    )

plt.xlabel("End time")
plt.ylabel("Time to solution (minutes)")  # ✅ explicit minutes
plt.xticks(all_end_times)

plt.yscale("log")

# same tick style as your original
minute_ticks = [0.1, 0.5, 1, 2, 5, 10, 20, 30]
plt.yticks(minute_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.legend()
plt.title("Time to solution vs End time")

# 🔁 overwrite existing
plt.savefig("results/end_time/time_vs_endtime.png", dpi=300, bbox_inches="tight")
plt.close()