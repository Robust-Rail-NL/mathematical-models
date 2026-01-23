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
  edges_start = []
  names_id_map = {}
  for track_part in track_parts:
    # print(track_part.type, track_part.id, track_part.aSide, track_part.bSide)
    if track_part.type == "RailRoad":
      nodes.append(track_part.id)
      names_id_map[track_part.name] = track_part.id
    if track_part.type == "Switch":
      for i in track_part.aSide:
        for j in track_part.bSide:
          edges_start.append((i, j))
  edges = edges_start.copy()
  for edge in edges_start:
    edges.append((edge[1], edge[0]))  # Add reverse direction
  for node in nodes:
    edges.append((node, node))  # Add self-loop
  # print("Names to IDs:", names_id_map)
  return nodes, edges

# from collections import defaultdict, deque

# def _to_int(x):
#     """Normalize ids that might be int or string like '51'."""
#     if isinstance(x, int):
#         return x
#     if isinstance(x, str):
#         x = x.strip()
#         if x == "":
#             raise ValueError("Empty id string")
#         return int(x)
#     raise TypeError(f"Unsupported id type: {type(x)}")


# def convert_to_graph(track_parts):
#     """
#     Nodes = RailRoad ids with length > 0
#     Directed edges = allowed transitions between railroads induced by switches
#     Zero-length railroads are removed by shortcutting through them.
#     """

#     # --- Collect railroads and build base adjacency including zero-length ---
#     rail_len = {}            # rr_id -> length
#     adj = defaultdict(set)   # rr_id -> set(rr_id)

#     # 1) read railroads
#     for tp in track_parts:
#         if tp.type == "RailRoad":
#             rr_id = _to_int(tp.id)
#             rail_len[rr_id] = tp.length

#     # 2) add edges induced by all switch-like parts
#     # (Switch, EnglishSwitch, Intersection, Bumper etc.)
#     for tp in track_parts:
#         if tp.type != "RailRoad":
#             # tp.aSide and tp.bSide are railroad IDs (strings in your print)
#             a_list = [_to_int(x) for x in (tp.aSide or [])]
#             b_list = [_to_int(x) for x in (tp.bSide or [])]

#             # Directed edges: aSide -> bSide (your stated semantics)
#             for a in a_list:
#                 for b in b_list:
#                     # Only connect if both endpoints are railroads we know about
#                     if a in rail_len and b in rail_len:
#                         adj[a].add(b)

#     # --- Contract away zero-length railroad nodes ---
#     zero_nodes = {rr for rr, L in rail_len.items() if L == 0}
#     nonzero_nodes = {rr for rr, L in rail_len.items() if L != 0}

#     # Precompute for speed: adjacency from each node
#     # We will build contracted edges between nonzero nodes only.
#     contracted_edges = set()

#     # BFS from each nonzero node, but only traverse through zero nodes.
#     # When we reach a nonzero node v, we add edge (u, v) and STOP that branch.
#     for u in nonzero_nodes:
#         q = deque()
#         seen_zero = set()

#         # seed with direct successors of u
#         for nxt in adj.get(u, ()):
#             if nxt in zero_nodes:
#                 q.append(nxt)
#                 seen_zero.add(nxt)
#             elif nxt in nonzero_nodes:
#                 contracted_edges.add((u, nxt))

#         # traverse through zero-length nodes
#         while q:
#             z = q.popleft()
#             for nxt in adj.get(z, ()):
#                 if nxt in zero_nodes:
#                     if nxt not in seen_zero:
#                         seen_zero.add(nxt)
#                         q.append(nxt)
#                 elif nxt in nonzero_nodes:
#                     contracted_edges.add((u, nxt))
#                 # if nxt is unknown, ignore

#     nodes = sorted(nonzero_nodes)
#     edges = sorted(contracted_edges)

#     return nodes, edges


# def convert_to_graph(track_parts):
#   nodes = []
#   edges_start = []
#   switches = []
#   for track_part in track_parts:
#       if track_part.type == "RailRoad":
#           nodes.append(track_part.id)
#       if track_part.type == "Switch":
#         nodes.append(track_part.id)
#         switches.append(track_part.id)
#         for i in track_part.aSide:
#           edges_start.append((track_part.id, i))
#         for i in track_part.bSide:
#           edges_start.append((track_part.id, i))
#   edges = edges_start.copy()
#   for edge in edges_start:
#     edges.append((edge[1], edge[0]))  # Add reverse direction
#   for node in nodes:
#     if node not in switches:
#       edges.append((node, node))  # Add self-loop, TODO remove self loop for switches
#   return nodes, edges

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
  data = load_json('locations/ten_tracks_location.json')
  data = load_json('../robust-rail-generator/data/locations/kleineBinckhorst_solver.json')
  data = load_json('locations/binckhorst.json')
  nodes, edges, facilities = load_location(data)
  print("Nodes:", nodes)
  print("Edges:", edges)
  print("Facilities:", facilities)
