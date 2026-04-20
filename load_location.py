import json
import math

from dataclasses import dataclass
from collections import defaultdict, deque

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

# Convert track parts to graph representation including all parts
# only use edges from aside
# also compute main_nodes, which are the nodes that represent actual track parts with length > 0
# also compute self loops for parking allowed track for later
def convert_to_graph(track_parts):
  nodes = []
  self_loop_edges = []
  edges_aSide = []
  edges_bSide = []
  artificial_switch_id_counter = 99
  
  split_map = {}
  main_nodes = set()
  
  for track_part in track_parts:
    if track_part.type == "RailRoad":
      # If the track part is long and allows parking,
      # split it into segments of 100m to allow parking in multiple places,
      # Otherwise, just add the track part as a node
      if track_part.length >= 200 and getattr(track_part, "parkingAllowed", False):
        num_segments = int(track_part.length // 100)
        split_ids = [f"{track_part.id}_{i+1}" for i in range(num_segments)]
        nodes.extend(split_ids)
        split_map[track_part.id] = split_ids
        for i in range(num_segments-1):
          artificial_switch_id_counter += 1
          edges_aSide.append((split_ids[i], split_ids[i+1], artificial_switch_id_counter))
          edges_bSide.append((split_ids[i+1], split_ids[i], artificial_switch_id_counter))
        for split_id in split_ids:
          self_loop_edges.append((split_id, split_id))
          main_nodes.add(split_id)
      else:
        nodes.append(track_part.id)
        if track_part.length > 0:
          main_nodes.add(track_part.id)
        if getattr(track_part, "parkingAllowed", False):
          self_loop_edges.append((track_part.id, track_part.id))  # Add self-loop if parking allowed
    else:
      for i in track_part.aSide:
        for j in track_part.bSide:
          src = split_map.get(i, [i])[-1]
          dst = split_map.get(j, [j])[0]
          edges_aSide.append((src, dst, track_part.id))
          edges_bSide.append((dst, src, track_part.id))
  return nodes, edges_aSide, self_loop_edges, main_nodes

# Compress graph to only include main_nodes and edges between them, 
# also compute which track parts are used in each edge for conflict computation
def convert_to_compressed_graph(track_parts, edges_aSide, main_nodes):
  adj = defaultdict(list)
  for a, b, track_id in edges_aSide:
    adj[a].append((b, track_id))
  
  new_edges = set()
  track_parts_used = {}
  for start in main_nodes:
    queue = deque([(start, [start])])
    visited = set()

    while queue:
      cur, used_tracks = queue.popleft()
      for nxt, track_id in adj[cur]:
        if (cur, nxt) in visited:
          continue
        visited.add((cur, nxt))
        new_used = used_tracks + [track_id, nxt]
        if nxt in main_nodes and nxt != start:
          new_edges.add((start, nxt))
          if (start, nxt) not in track_parts_used:
            new_used = [x for x in new_used if x not in [start, nxt]]  # Remove start points from used track_parts in edge
            track_parts_used[(start, nxt)] = new_used
        else:
          queue.append((nxt, new_used))
  return list(main_nodes), list(new_edges), track_parts_used

def compute_conflicts(edges, track_parts_used):
  # Map each track part to edges that use it
  part_to_edges = defaultdict(set)
  for edge in edges:
    if edge[0] == edge[1]:  # Skip self-loops
      continue
    for track in track_parts_used[edge]:
      part_to_edges[track].add(edge)
  
  # Build conflict sets: each track part generates a set of edges using it
  conflict_sets = []
  seen_sets = set()  # to avoid duplicates
  for edge_set in part_to_edges.values():
    if len(edge_set) > 1:
      frozen = frozenset(edge_set)
      if frozen not in seen_sets:
        conflict_sets.append(set(edge_set))
        seen_sets.add(frozen)

  edges_in_conflicts = set()
  for cs in conflict_sets:
    edges_in_conflicts.update(cs)
  
  for edge in edges:
    if edge[0] == edge[1]:  # Skip self-loops
      continue
    if edge not in edges_in_conflicts:
      conflict_sets.append({edge})
  return conflict_sets

# Check if two sets of edges should be merged based on shared track parts
# if every edge in A shares a track part with every edge in B, then they should be merged
def sets_should_merge(A, B, track_parts_used):
  for eA in A:
    partsA = set(track_parts_used[eA])
    for eB in B:
      partsB = set(track_parts_used[eB])
      if partsA.isdisjoint(partsB):
        return False
  return True

# Merge conflict sets if they share track parts
def merge_conflict_sets(conflict_sets, track_parts_used):
  changed = True
  while changed:
    changed = False
    new_sets = []
    used = [False] * len(conflict_sets)

    for i in range(len(conflict_sets)):
      if used[i]:
        continue
      merged = set(conflict_sets[i])
      used[i] = True
      for j in range(i + 1, len(conflict_sets)):
        if used[j]:
          continue
        if sets_should_merge(merged, conflict_sets[j], track_parts_used):
          merged |= conflict_sets[j]
          used[j] = True
          changed = True
      new_sets.append(merged)
    conflict_sets = new_sets
  return conflict_sets
  
# Add reverse edges to ensure undirected graph representation
def add_reverse_edges(edges):
  reverse_edges = set()
  for a, b in edges:
    if a == b:
      continue
    reverse_edges.add((b, a))
  return list(edges) + list(reverse_edges)

# Add reverse edges to conflict sets to ensure undirected graph representation in conflicts
def add_reverse_edges_to_conflicts(conflict_sets):
  new_conflicts = []
  for cs in conflict_sets:
    cs_with_reverse = set()
    for edge in cs:
      cs_with_reverse.add(edge)
      cs_with_reverse.add((edge[1], edge[0]))  # Add reversed edge
    new_conflicts.append(cs_with_reverse)
  return new_conflicts

# Sort conflict sets for consistent printing
def sort_conflict_sets(conflict_sets):
  sorted_inner = [sorted(cs) for cs in conflict_sets]
  sorted_outer = sorted(sorted_inner, key=lambda s: s[0] if s else ("", ""))
  return sorted_outer

def traversal_time(edges, track_parts_used, track_Parts):
  traversal_time_edges = {}
  for i,j in edges:
    traversal_time_edges[(i,j)] = 0
    traversal_time_edges[(j,i)] = 0
    for tp in track_parts_used[(i,j)]:
      for tp2 in track_Parts:
        if tp == tp2.id:
          if tp2.type == 'EnglishSwitch' or tp2.type == 'Switch' or tp2.type == 'Intersection':
            traversal_time_edges[(i,j)] += 1
            traversal_time_edges[(j,i)] += 1
    # if 0 then its an edge between nodes orignating from the same track, which takes 1 minute/timestep
    if traversal_time_edges[(i,j)] == 0:
      traversal_time_edges[(i,j)] = 1
    # divide by 2 since one switch takes 30 seconds/half of a timestep and add 2
    # because its between two tracks so 2 minutes
    else:
      traversal_time_edges[(i,j)] = 2+math.ceil(traversal_time_edges[(i,j)]/2)
      traversal_time_edges[(j,i)] = 2+math.ceil(traversal_time_edges[(j,i)]/2)
  return traversal_time_edges


def pre_load_location(data):
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

  # Compute full graph including all track paths, compute main_nodes, 
  # which are the nodes that represent actual track parts with length > 0, and self loops for parking allowed tracks
  # then compress graph to only include main_nodes and edges between them, which represent the actual track parts used in the solution,
  # and compute which track parts are used in each edge for conflict computation
  nodes, edges, self_loop_edges, main_nodes = convert_to_graph(track_Parts)
  nodes, edges, track_parts_used = convert_to_compressed_graph(track_Parts, edges, main_nodes)
  
  traversal_time_edges = traversal_time(edges, track_parts_used, track_Parts)
  
  # Add self loops to edges
  edges += self_loop_edges
  # Compute edge conflcits based on shared track parts, then merge conflict set
  conflict_edges = compute_conflicts(edges, track_parts_used)
  conflict_edges = merge_conflict_sets(conflict_edges, track_parts_used)
  # Add reverse edges to ensure undirected graph representation
  edges = add_reverse_edges(edges)
  
  conflict_edges = add_reverse_edges_to_conflicts(conflict_edges)
  # Sort for printing
  conflict_edges = sort_conflict_sets(conflict_edges)
  return nodes, edges, conflict_edges, traversal_time_edges

def load_location(data):
  nodes, edges, conflict_edges, traversal_time_edges = pre_load_location(data)
  return nodes, edges, conflict_edges

def load_location_time(data):
  nodes, edges, conflict_edges, traversal_time_edges = pre_load_location(data)
  print(traversal_time_edges)
  return nodes, edges, conflict_edges, traversal_time_edges

if __name__ == "__main__":
  data = load_json('locations/location_solver.json')
  # data = load_json('locations/detour_location.json')
  # nodes, edges, conflict_edges = load_location(data)
  nodes, edges, conflict_edges,traversal_time_edges  = load_location_time(data)
  print("Nodes:", sorted(nodes))
  print("Edges:", sorted(edges))
  conflict_edges = sort_conflict_sets(conflict_edges)
  for conflict in conflict_edges:
    print("Conflict set:", conflict)
  
