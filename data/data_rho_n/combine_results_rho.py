import os
import csv

input_folder = "rho_results/"
output_file = "rho_results.csv"

all_rows = []
header = None

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
                all_rows.append(row)

# Sort by rho (column 0, float)
def sort_key(row):
    return float(row[0])

all_rows.sort(key=sort_key)

with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"Combined file written to {output_file}")