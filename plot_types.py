import pandas as pd
import matplotlib.pyplot as plt
import os
import re

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
plt.ylabel("Time (minutes)")
plt.yscale("log")

# Set y-ticks at desired minute values (converted to seconds)
minute_ticks = [1,2,3,4,5, 10, 15, 20]
second_ticks = [m * 60 for m in minute_ticks]

plt.yticks(second_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.title("Average Time (successful runs only)")
plt.legend()

plt.savefig("results/types.png", dpi=300, bbox_inches="tight")



#with fails
df = pd.read_csv("results_types/combined_results.csv")

df["solution_found"] = df["solution_found"].astype(bool)

# Assign 1800 seconds (30 minutes) to runs where no solution was found
df.loc[~df["solution_found"], "time"] = 1800

type_order = ["1", "2", "1/3", "1/2"]

# Include all runs for averaging
avg_time = (
  df
  .groupby(["num_trains", "type"])["time"]
  .mean()
  .unstack()
)

plt.figure()

for t in type_order:
  if t in avg_time.columns:
    plt.plot(avg_time.index, avg_time[t], marker='o', label=f"Type {t}")

plt.xlabel("Number of trains")
plt.ylabel("Time (minutes)")
plt.yscale("log")

# Y-axis ticks in minutes
minute_ticks = [1, 2, 3, 4, 5, 10, 15, 20, 25]
second_ticks = [m * 60 for m in minute_ticks]
plt.yticks(second_ticks, labels=minute_ticks)

plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.title("Average Time (failures as 30 min)")
plt.legend()

plt.savefig("results/types_failures.png", dpi=300, bbox_inches="tight")


# solved_count = (
#   df.groupby(["num_trains", "type"])["solution_found"]
#   .sum()
#   .unstack()
# )

# plt.figure()

# for t in type_order:
#   if t in solved_count.columns:
#     plt.plot(solved_count.index, solved_count[t], marker='o', label=f"Type {t}")

# plt.xlabel("Number of trains")
# plt.ylabel("Solved instances (out of 20)")
# plt.title("Number of solved instances")
# plt.legend()
# plt.grid()

# plt.savefig("results/solutions_found.png", dpi=300, bbox_inches="tight")


# avg_movements = (
#   df[df["solution_found"] == True]
#   .groupby("num_trains")["num_movements"]
#   .mean()
# )

# min_movements = {
#   5: 10,
#   10: 22,
#   15: 42,
#   20: 66,
#   25: 102,
#   30: 134
# }

# min_x = list(min_movements.keys())
# min_y = list(min_movements.values())

# plt.figure()

# plt.plot(avg_movements.index, avg_movements.values, marker='o', label="Average movements")
# plt.plot(min_x, min_y, linestyle="--", marker='o', label="Minimum required movements")

# plt.xlabel("Number of trains")
# plt.ylabel("Number of movements")
# plt.title("Average vs Minimum Movements")

# plt.legend()
# plt.grid()

# plt.savefig("results/movements_plot.png", dpi=300, bbox_inches="tight")











# folder = "solutions_types"
# max_gap = 5

# pattern = re.compile(r"(\d+)_trains")

# results = []

# for filename in os.listdir(folder):
#   if not filename.endswith(".json"):
#     continue
  
#   match = pattern.search(filename)
#   if not match:
#     continue
  
#   num_trains = int(match.group(1))
#   filepath = os.path.join(folder, filename)
  
#   with open(filepath, "r") as f:
#     lines = f.readlines()
  
#   start_idx = None
#   for i, line in enumerate(lines):
#     if line.strip() == "agent,i,j,t":
#       start_idx = i + 1
#       break
  
#   if start_idx is None:
#     continue
  
#   movement_lines = []
#   for line in lines[start_idx:]:
#     line = line.strip()
#     if not line:
#       continue
#     if line in ["agent,n,t", "conflicts,time"]:
#       break
#     movement_lines.append(line)
  
#   if not movement_lines:
#     continue
  
#   data = [l.split(",") for l in movement_lines]
#   df = pd.DataFrame(data, columns=["agent","i","j","t"])
  
#   df["agent"] = df["agent"].astype(int)
#   df["t"] = df["t"].astype(int)
  
#   df = df[df["i"] != df["j"]]
  
#   total_sequences = 0
  
#   for agent, group in df.groupby("agent"):
#     times = sorted(group["t"].tolist())
    
#     if not times:
#       continue
    
#     sequences = 1
    
#     for prev, curr in zip(times, times[1:]):
#       if curr - prev > max_gap:
#         sequences += 1
    
#     total_sequences += sequences
  
#   results.append({
#     "num_trains": num_trains,
#     "num_movements": total_sequences
#   })

# df_results = pd.DataFrame(results)

# avg_movements = (
#   df_results
#   .groupby("num_trains")["num_movements"]
#   .mean()
# )

# print(avg_movements)

# min_movements = {
#   5: 10,
#   10: 20,
#   15: 30,
#   20: 40,
#   25: 50,
#   30: 60
# }

# min_x = list(min_movements.keys())
# min_y = list(min_movements.values())

# plt.figure()

# plt.plot(avg_movements.index, avg_movements.values, marker='o', label="Average movements")
# plt.plot(min_x, min_y, linestyle="--", marker='o', label="Minimum required movements")

# plt.xlabel("Number of trains")
# plt.ylabel("Number of movements")
# plt.title("Average vs Minimum Movements (continuous)")

# plt.legend()
# plt.grid()

# plt.savefig("results/movements_continues_plot.png", dpi=300, bbox_inches="tight")

