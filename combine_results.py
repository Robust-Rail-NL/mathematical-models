import os
import csv

input_folder = "results_types"
output_file = "results_types/combined_results.csv"

type_order = {
  "1": 0,
  "2": 1,
  "1/3": 2,
  "1/2": 3
}

all_rows = []
header = None

for filename in os.listdir(input_folder):
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
        all_rows.append(row)

def sort_key(row):
  num_trains = int(row[0])
  type_val = row[1]
  return (num_trains, type_order.get(type_val, 999))

all_rows.sort(key=sort_key)

with open(output_file, "w", newline="") as f:
  writer = csv.writer(f)
  writer.writerow(header)
  writer.writerows(all_rows)

print(f"Combined file written to {output_file}")