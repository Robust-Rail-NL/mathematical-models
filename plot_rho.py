import pandas as pd
import matplotlib.pyplot as plt
import os

input_file = "results_n_experiment/combined_results.csv"

df = pd.read_csv(input_file)

df["solution_found"] = df["solution_found"].astype(bool)
df["n"] = df["n"].astype(float)

# remove n = 0.01
df = df[df["n"] != 0.01]

# count solved per n
solved = df.groupby("n")["solution_found"].sum().sort_index()
print(solved)
x = solved.index
y = solved.values

plt.figure()

plt.plot(
  x,
  y,
  color="black",
  marker="o",
  linestyle=":",
  linewidth=2
)

plt.xlabel("N")
plt.ylabel("Solved Instances")
plt.xticks(x)

plt.ylim(0, 100)

plt.grid(True, linestyle="--", linewidth=0.5)
plt.title("Solved Instances vs N")

os.makedirs("results/rho", exist_ok=True)
plt.savefig("results/rho/solved_vs_n.png", dpi=300, bbox_inches="tight")
plt.close()