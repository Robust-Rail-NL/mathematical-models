import os
import csv
from collections import defaultdict

input_folder = "n_results/"
output_file = "n_results.csv"

all_rows = []
header = None

# Stats
true_counts = defaultdict(int)
total_counts = defaultdict(int)

time_sums = defaultdict(float)
time_counts = defaultdict(int)

success_time_sums = defaultdict(float)
success_time_counts = defaultdict(int)

for filename in os.listdir(input_folder):
    if filename.startswith("combined"):
        continue
    if filename.endswith(".csv"):
        filepath = os.path.join(input_folder, filename)
        with open(filepath, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

            if len(rows) <= 1:
                continue

            if header is None:
                header = rows[0]

            for row in rows[1:]:
                if row == header:
                    continue

                rho = float(row[0])
                time_val = float(row[3])
                solution_found = row[5].strip().lower() == "true"

                # Counts
                total_counts[rho] += 1
                if solution_found:
                    true_counts[rho] += 1

                # Time stats (all runs)
                time_sums[rho] += time_val
                time_counts[rho] += 1

                # Time stats (successful runs only)
                if solution_found:
                    success_time_sums[rho] += time_val
                    success_time_counts[rho] += 1

                all_rows.append(row)

# Sort by rho
all_rows.sort(key=lambda row: float(row[0]))

# Write combined file
with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"Combined file written to {output_file}")

# ---- RESULTS ----

print("\nSuccess count per n:")
for rho in sorted(total_counts.keys()):
    print(f"n={rho}: {true_counts[rho]}/{total_counts[rho]}")

print("\nAverage computation time per n (all runs):")
for rho in sorted(time_counts.keys()):
    avg_time = time_sums[rho] / time_counts[rho]
    print(f"n={rho}: {avg_time:.2f} s")

print("\nAverage computation time per n (successful runs only):")
for rho in sorted(success_time_counts.keys()):
    avg_time = success_time_sums[rho] / success_time_counts[rho]
    print(f"n={rho}: {avg_time:.2f} s")