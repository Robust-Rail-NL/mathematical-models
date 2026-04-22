import pandas as pd
import matplotlib.pyplot as plt
import os

input_file = "results_rho_experiment/combined_results.csv"

df = pd.read_csv(input_file)

df["solution_found"] = df["solution_found"].astype(bool)
df["rho"] = df["rho"].astype(float)

# remove rho = 0.01
df = df[df["rho"] != 0.01]

# count solved per rho
solved = df.groupby("rho")["solution_found"].sum().sort_index()

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

plt.xlabel("rho")
plt.ylabel("Solved instances")
plt.xticks(x)

plt.ylim(0, 30)

plt.grid(True, linestyle="--", linewidth=0.5)
plt.title("Solved instances vs rho")

os.makedirs("results/rho", exist_ok=True)
plt.savefig("results/rho/solved_vs_rho.png", dpi=300, bbox_inches="tight")
plt.close()