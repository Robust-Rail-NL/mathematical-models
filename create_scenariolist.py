import os
import sys

def generate_scenario_list(folder, output_file, local_prefix, cluster_prefix):
  if not os.path.isdir(folder):
    print(f"Error: folder '{folder}' does not exist")
    return

  files = os.listdir(folder)

  solver_files = [f for f in files if f.endswith(".json") and "solver" in f]

  solver_files.sort()

  with open(output_file, "w") as f:
    for file in solver_files:
      local_path = os.path.abspath(os.path.join(folder, file))
      cluster_path = local_path.replace(local_prefix, cluster_prefix)
      f.write(cluster_path + "\n")
  print(f"Written {len(solver_files)} scenarios to {output_file}")


if __name__ == "__main__":
  if len(sys.argv) != 5:
    print("Usage:")
    print("python generate_scenarios_list.py <folder> <output_file> <local_prefix> <cluster_prefix>")
    sys.exit(1)

  folder = sys.argv[1]
  output_file = sys.argv[2]
  local_prefix = sys.argv[3]
  cluster_prefix = sys.argv[4]

  generate_scenario_list(folder, output_file, local_prefix, cluster_prefix)