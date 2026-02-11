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
    exit()
  except json.JSONDecodeError:
    print(f"Error: File '{file_path}' is not a valid JSON.")
    exit()

def convert_to_graph(track_parts):
  nodes = []
  edges = []
  names_id_map = {}
  
  conflict_edges = [] 

  for track_part in track_parts:
    if track_part.type == "RailRoad":
      nodes.append(track_part.id)
      names_id_map[track_part.name] = track_part.id
      if getattr(track_part, "parkingAllowed", False):
        edges.append((track_part.id, track_part.id))  # Add self-loop if parking allowed
    elif track_part.type == "Switch":
      switch_edges = set()
      for i in track_part.aSide:
        for j in track_part.bSide:
          edges.append((i, j))  # Forward direction
          edges.append((j, i))  # Reverse direction
          
          switch_edges.add((i, j))
          switch_edges.add((j, i))
      if switch_edges:
        conflict_edges.append(switch_edges)
  return nodes, edges, conflict_edges

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
  nodes, edges, conflict_edges = convert_to_graph(track_Parts)
  return nodes, edges, conflict_edges, facilities
  
if __name__ == "__main__":
  # data = load_json('locations/ten_tracks_location.json')
  # data = load_json('../robust-rail-generator/data/locations/kleineBinckhorst_solver.json')
  data = load_json('locations/binckhorst.json')
  nodes, edges, conflict_edges, facilities = load_location(data)
  print("Nodes:", nodes)
  print("Edges:", edges)
  print("Conflict Edges:", conflict_edges)
  print("Facilities:", facilities)
