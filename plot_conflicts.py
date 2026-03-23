import os
import pandas as pd
import matplotlib.pyplot as plt
import re

folder = "solutions_types"

# Store data per number of trains
data = {}

# Regex to extract number of trains
pattern = re.compile(r"(\d+)_trains")

for filename in os.listdir(folder):
  match = pattern.search(filename)
  if not match:
    continue
  num_trains = int(match.group(1))
  filepath = os.path.join(folder, filename)
  
  with open(filepath, "r") as f:
    lines = f.readlines()

  start_idx = None
  for i, line in enumerate(lines):
    if line.strip() == "conflicts,time":
      start_idx = i + 1
      break
    if start_idx is None:
      continue
  
  conflicts = []
  for line in lines[start_idx:]:
    line = line.strip()
    if not line:
      continue
    parts = line.split(",")
    if len(parts) < 2:
      continue
    conflicts.append(float(parts[0]))
  df = pd.DataFrame({"iteration": range(len(conflicts)), "conflicts": conflicts})
  data.setdefault(num_trains, []).append(df)

avg_data = {}

for num_trains, dfs in data.items():
  combined = pd.concat(dfs)
  avg = (combined.groupby("iteration")["conflicts"].mean())
  counts = combined.groupby("iteration").size()
  avg = avg[counts >= 5]
  avg_data[num_trains] = avg
plt.figure()

for num_trains in sorted(avg_data.keys()):
  avg = avg_data[num_trains]
  plt.plot(avg.index, avg.values, label=f"{num_trains} trains", marker='o')

plt.xlabel("Iteration")
plt.ylabel("Number of conflicts")
plt.title("Conflicts vs Iteration (averaged per number of trains)")
plt.legend()
plt.grid()

plt.savefig("results/conflicts_vs_iteration.png", dpi=300, bbox_inches="tight")