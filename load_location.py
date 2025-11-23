import json

from dataclasses import dataclass

@dataclass
class TrackPart:
    id: str
    type: str
    aSide: []
    bSide: []
    length: float
    sawMovementAllowed: bool
    parkingAllowed: bool
    name: str

@dataclass
class Facility:
    id: str
    type: str
    relatedTrackParts: []
    taskTypes: [[]]
    simultaneousUsageCount: int


def load_json(file_path):
  try:
      with open(file_path, 'r') as f:
          data = json.load(f)
      return data
  except FileNotFoundError:
      print(f"Error: File '{file_path}' not found.")
  except json.JSONDecodeError:
      print(f"Error: File '{file_path}' is not a valid JSON.")
      
def convert_to_graph(track_parts):
  nodes = []
  edges_start = []
  for track_part in track_parts:
      if track_part.type == "RailRoad":
          nodes.append(track_part.id)
      if track_part.type == "Switch":
          for i in track_part.aSide:
              for j in track_part.bSide:
                  edges_start.append((i, j))
  edges = edges_start.copy()
  for edge in edges_start:
    edges.append((edge[1], edge[0]))  # Add reverse direction
  for node in nodes:
    edges.append((node, node))  # Add self-loop
  return nodes, edges

def load_location(data):
  track_Parts = []
  facilities = []
  for trackPart in data['trackParts']:
    track_Parts.append(TrackPart(
      id=trackPart.get('id', ''),
      type=trackPart.get('type', ''),
      aSide=trackPart.get('aSide', []),
      bSide=trackPart.get('bSide', []),
      length=trackPart.get('length', 0.0),
      sawMovementAllowed=trackPart.get('sawMovementAllowed', False),
      parkingAllowed=trackPart.get('parkingAllowed', False),
      name=trackPart.get('name', '')))
  for facility in data['facilities']:
    facilities.append(Facility(
      id=facility.get('id', ''),
      type=facility.get('type', ''),
      relatedTrackParts=facility.get('relatedTrackParts', []),
      taskTypes=facility.get('taskTypes', []),
      simultaneousUsageCount=facility.get('simultaneousUsageCount', 0)))
  nodes, edges = convert_to_graph(track_Parts)
  return nodes, edges, facilities
  
if __name__ == "__main__":
  data = load_json('../robust-rail-generator/data/locations/simple_service_location_solver.json')
  # data = load_json('../robust-rail-generator/data/locations/kleineBinckhorst_solver.json')
  nodes, edges, facilities = load_location(data)
  print("Nodes:", nodes)
  print("Edges:", edges)
  print("Facilities:", facilities)
