# import pandas as pd
# import glob
# import matplotlib.pyplot as plt
# import numpy as np

# files = glob.glob("results_time_experiment/*.csv")

# dfs = []
# for f in files:
#   df = pd.read_csv(f)
#   df["file"] = f
#   dfs.append(df)

# data = pd.concat(dfs)

# metrics = [
#   "total_model_creation_time",
#   "solve_time_total",
#   "admm_update_time_total",
#   "lr_update_time_total"
# ]

# # -----------------------------
# # 1) GLOBAL AVERAGE (1 BAR)
# # -----------------------------
# avg = data[metrics].mean()

# plt.figure()

# bottom = 0
# for m in metrics:
#   plt.bar("average", avg[m], bottom=bottom, label=m)
#   bottom += avg[m]

# plt.ylabel("time (s)")
# plt.title("Average runtime breakdown (30 runs)")
# plt.legend()
# plt.tight_layout()
# plt.savefig("results/time/time_single_bar.png")


# # -----------------------------
# # 2) ALL 30 RUNS (NO AVERAGING)
# # -----------------------------
# plt.figure()

# x = np.arange(len(data))
# bottom = np.zeros(len(data))

# for m in metrics:
#   plt.bar(x, data[m].values, bottom=bottom, label=m)
#   bottom += data[m].values

# plt.xticks(x, [f"{i}" for i in range(len(data))], rotation=90)
# plt.ylabel("time (s)")
# plt.title("Runtime breakdown per run (30 scenarios)")
# plt.legend()
# plt.tight_layout()
# plt.savefig("results/time/time_multiple_file.png")

import pandas as pd
import glob

files = glob.glob("results_time_experiment/*.csv")

dfs = []
for f in files:
  df = pd.read_csv(f)
  dfs.append(df)

data = pd.concat(dfs)

metrics = [
  "total_model_creation_time",
  "solve_time_total",
  "admm_update_time_total",
  "lr_update_time_total"
]

# total time per run
data["total_time"] = data[metrics].sum(axis=1)

# compute per-run percentages
for m in metrics:
  data[m + "_pct"] = 100 * data[m] / data["total_time"]

pct_cols = [m + "_pct" for m in metrics]

# average percentages across all runs
avg_pct = data[pct_cols].mean()

# pretty output
result = pd.DataFrame({
  "component": [
    "model_creation",
    "solve",
    "admm_update",
    "lr_update"
  ],
  "avg_percentage": avg_pct.values
})

print(result)