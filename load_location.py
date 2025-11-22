import json

def load_json(file_path):
  try:
      with open(file_path, 'r') as f:
          data = json.load(f)
      return data
  except FileNotFoundError:
      print(f"Error: File '{file_path}' not found.")
  except json.JSONDecodeError:
      print(f"Error: File '{file_path}' is not a valid JSON.")

def load_location(data):
  trackParts = data['trackParts']
  facilities = data['facilities']
  nodes = []
  edges_start = []
  for part in trackParts:
    if part['type'] == "RailRoad":
      nodes.append(part['id'])
    if part['type'] == "Switch":
      for i in part['aSide']:
        for j in part['bSide']:
          edges_start.append((i, j))
  edges = edges_start.copy()
  for edge in edges_start:
    edges.append((edge[1], edge[0]))  # Add reverse direction
  for node in nodes:
    edges.append((node, node))  # Add self-loop
  return nodes, edges, facilities
  
if __name__ == "__main__":
  data = load_json('../robust-rail-generator/data/locations/simple_service_location_solver.json')
  # data = load_json('../robust-rail-generator/data/locations/kleineBinckhorst_solver.json')
  nodes, edges, facilities = load_location(data)
  print("Nodes:", nodes)
  print("Edges:", edges)
  print("Facilities:", facilities)
