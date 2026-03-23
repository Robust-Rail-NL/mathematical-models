import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results_types/combined_results.csv")

df["solution_found"] = df["solution_found"].astype(bool)

type_order = ["1", "2", "1/3", "1/2"]
df_success = df[df["solution_found"] == True]

avg_time = (
  df_success
  .groupby(["num_trains", "type"])["time"]
  .mean()
  .unstack()
)

plt.figure()




for t in type_order:
  if t in avg_time.columns:
    plt.plot(avg_time.index, avg_time[t], marker='o', label=f"Type {t}")

plt.xlabel("Number of trains")
plt.ylabel("Time (s)")
plt.yscale("log")
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.title("Average Time (successful runs only)")
plt.legend()
plt.grid()
plt.savefig("results/types.png", dpi=300, bbox_inches="tight")


solved_count = (
  df.groupby(["num_trains", "type"])["solution_found"]
  .sum()
  .unstack()
)

plt.figure()

for t in type_order:
  if t in solved_count.columns:
    plt.plot(solved_count.index, solved_count[t], marker='o', label=f"Type {t}")

plt.xlabel("Number of trains")
plt.ylabel("Solved instances (out of 20)")
plt.title("Number of solved instances")
plt.legend()
plt.grid()

plt.savefig("results/solutions_found.png", dpi=300, bbox_inches="tight")



avg_movements = (
  df[df["solution_found"] == True]
  .groupby("num_trains")["num_movements"]
  .mean()
)

min_movements = {
  5: 10,
  10: 22,
  15: 42,
  20: 66,
  25: 102,
  30: 134
}

min_x = list(min_movements.keys())
min_y = list(min_movements.values())

plt.figure()

plt.plot(avg_movements.index, avg_movements.values, marker='o', label="Average movements")
plt.plot(min_x, min_y, linestyle="--", marker='o', label="Minimum required movements")

plt.xlabel("Number of trains")
plt.ylabel("Number of movements")
plt.title("Average vs Minimum Movements")

plt.legend()
plt.grid()

plt.savefig("results/movements_plot.png", dpi=300, bbox_inches="tight")
