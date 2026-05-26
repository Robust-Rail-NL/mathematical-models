from copy import deepcopy
import json
from pathlib import Path
import load_location as ll
import load_scenario as ls
import csv
from collections import defaultdict

# load location
def pre_load_location(data):
  track_Parts = []
  facilities = []
  for trackPart in data['trackParts']:
    track_Parts.append(ll.TrackPart(
      id=trackPart.get('id', ''),
      type=trackPart.get('type', ''),
      aSide=trackPart.get('aSide', []),
      bSide=trackPart.get('bSide', []),
      length=trackPart.get('length', 0.0),
      sawMovementAllowed=trackPart.get('sawMovementAllowed', False),
      parkingAllowed=trackPart.get('parkingAllowed', False),
      name=trackPart.get('name', '')))
  for facility in data['facilities']:
    facilities.append(ll.Facility(
      id=facility.get('id', ''),
      type=facility.get('type', ''),
      relatedTrackParts=facility.get('relatedTrackParts', []),
      taskTypes=facility.get('taskTypes', []),
      simultaneousUsageCount=facility.get('simultaneousUsageCount', 0)))
  
  nodes, edges, self_loop_edges, main_nodes = ll.convert_to_graph(track_Parts)
  nodes, edges, track_parts_used = ll.convert_to_compressed_graph(track_Parts, edges, main_nodes)
  
  # Add self loops to edges
  edges += self_loop_edges
  # Compute edge conflcits based on shared track parts, then merge conflict set
  conflict_edges =ll.compute_conflicts(edges, track_parts_used)
  conflict_edges = ll.merge_conflict_sets(conflict_edges, track_parts_used)
  
  # for shortest path with continuous tracks we need extra data structures
  # create dictionary of equivalent nodes based on naming convention and 
  # build macro edges between them. Also adds edges like 15 -> 1_2 if 15 -> 1_1 is an edge
  equivalent_nodes = ll.build_equivalent_nodes(nodes)
  expanded_edges, macro_edge_nodes = ll.build_macro_edges(edges, equivalent_nodes)
  macro_edge_nodes = ll.add_reverse_macro_edges(macro_edge_nodes)
  expanded_edges = ll.add_reverse_edges(expanded_edges)
  
  
  # Add reverse edges to ensure undirected graph representation
  edges = ll.add_reverse_edges(edges)
  expanded_edges = ll.add_reverse_edges(expanded_edges)  
  
  conflict_edges = ll.add_reverse_edges_to_conflicts(conflict_edges)
  # Sort for printing
  conflict_edges = ll.sort_conflict_sets(conflict_edges)
  return nodes, edges, conflict_edges, expanded_edges, macro_edge_nodes, track_parts_used

# load plan
def load_data(filepath):
  movements = []
  positions = []
  found = False

  section = None

  with open(filepath, "r", newline="") as f:
    for raw_line in f:
      line = raw_line.strip()
      if not line:
        continue
      # Detect section headers
      if line == "agent,i,j,t":
        section = "movements"
        continue
      elif line == "agent,n,t":
        section = "positions"
        continue
      elif line == "conflicts,time":
        section = "conflicts"
        continue
      elif line == "found":
        section = "found"
        continue
      # Parse content
      if section == "movements":
        row = next(csv.reader([line]))
        agent, i, j, t = row
        if i == j:
          continue
        movements.append((int(agent), i, j, int(t)))
      elif section == "positions":
        row = next(csv.reader([line]))
        agent, i, t = row
        positions.append((int(agent), i, int(t)))
      elif section == "conflicts":
        continue
      elif section == "found":
        found = line.lower() == "true"

  return movements, positions, found

# mapping to fix correct ids of train units
def map_train_id_to_trainunit_id(data):
  return {train["id"]: train["members"][0]["trainUnit"]["id"] for train in data["in"]["trains"]}

# Assign new agent IDs based on arrival times (earliest arrival gets ID 0, etc.)
def assign_agent_ids(arrival_times):
  ordered_agents = sorted(arrival_times, key=arrival_times.get)
  return {agent: str(new_id) for new_id, agent in enumerate(ordered_agents)}

# name nodes originating from the same track as 1 instead of 1_1, 1_2, etc
def normalize_node(node):
  return node.split("_")[0]

# parse train type string into dict
def parse_type_string(s):
  parts = s.split("|")
  return {
    "displayName": parts[0],
    "carriages": int(parts[1]),
    "length": float(parts[2]),
    "combineDuration": parts[3],
    "splitDuration": parts[4],
    "backNormTime": parts[5],
    "backAdditionTime": parts[6],
    "reversalDuration": parts[7],
  }

# create plan movements based on movements from solution, using track part
# info to determine resources used. Also remove movements between nodes
# from the same track (e.g. 1_1 -> 1_2)
def create_movements(movements, track_parts_used, train_types, agent_ids):
  plan_movements = []
  for agent, i, j, t in movements:
    if (i, j) in track_parts_used:
      track_parts = track_parts_used[(i, j)]
    elif (j, i) in track_parts_used:
      track_parts = list(reversed(track_parts_used[(j, i)]))
    else:
      print(f"Error: No track part found for movement from {i} to {j}")
      exit()
    if normalize_node(i) == normalize_node(j):
      # skip movements between nodes from the same track
      continue
    resources = [{"name": str(r), "trackPartId": str(r)} for r in track_parts]

    resources.append({"name": normalize_node(j),"trackPartId": normalize_node(j)})
    type = train_types.get(str(agent))
    if type is None:
      print(f"Error: No train type found for agent {agent}")
      exit()
    type = parse_type_string(type)
    task = {
      "startTime": str(t*60),
      "endTime": str((t + 1)*60),
      "taskType": {
        "predefined": "Move"
      },
      "shuntingUnit": {
          "id": agent_ids.get(str(agent), str(agent)),
          "members": [
              {
                  "id": str(agent),
                  "type": type,
              }
          ],
          "parentIDs": [],
          "childIDs": [],
          "standingType": "",
      },
      "location": normalize_node(i),
      "resources": resources,
      "trainUnitIds": [],
    }
    plan_movements.append(task)

  return plan_movements

# check that all arrivals in positions match the scenario's start nodes and arrival times
def check_arrivals(positions, arrival_times, start_nodes, agents):
  valid_arrivals = 0
  for agent, i, t in positions:
    if str(i) == start_nodes[str(agent)] and t == arrival_times[str(agent)]:
      valid_arrivals += 1
  return valid_arrivals == len(agents)

# create plan arrivals based on positions from solution, matching them to 
# scenario's start nodes and arrival times
def create_arrivals(positions, arrival_times, start_nodes, train_types, agents, agent_ids):
  plan_arrivals = []
  if not check_arrivals(positions, arrival_times, start_nodes, agents):
    print("Error: Invalid arrival found")
    exit()
  for agent, i, t in positions:
    if str(i) == start_nodes[str(agent)] and t == arrival_times[str(agent)]:
      type = train_types.get(str(agent))
      if type is None:
        print(f"Error: No train type found for agent {agent}")
        exit()
      type = parse_type_string(type)
      task = {
        "startTime": str(t*60),
        "endTime": str(t*60),
        "taskType": {
          "predefined": "Arrive"
        },
        "shuntingUnit": {
            "id": agent_ids.get(str(agent), str(agent)),
            "members": [
                {
                    "id": str(agent),
                    "type": type,
                }
            ],
            "parentIDs": [],
            "childIDs": [],
            "standingType": "",
        },
        "location": normalize_node(i),
        "resources": [{"name": normalize_node(i), "trackPartId": normalize_node(i)}],
        "trainUnitIds": [],
      }
      plan_arrivals.append(task)
  return plan_arrivals

# check that all exits in positions match the scenario's departures (node, time, train type)
def check_exits(positions, departures, train_types, agents):
  valid_exits = 0
  for agent, i, t in positions:
    for departure in departures:
      if str(i) == departure[0] and t == departure[2] and train_types.get(str(agent)) == departure[1]:
        valid_exits += 1
  return valid_exits == len(agents)

# create plan exits based on positions from solution, matching them to
# scenario's departures (node, time, train type)
def create_exits(positions, departures, train_types, agents, agent_ids):
  plan_exits = []
  if not check_exits(positions, departures, train_types, agents):
    print("Error: Invalid exit found")
    exit()
  for agent, i, t in positions:
    for departure in departures:
      if str(i) == departure[0] and t == departure[2] and train_types.get(str(agent)) == departure[1]:
        type = train_types.get(str(agent))
        if type is None:
          print(f"Error: No train type found for agent {agent}")
          exit()
        type = parse_type_string(type)
        task = {
          "startTime": str(t*60),
          "endTime": str(t*60),
          "taskType": {
            "predefined": "Exit"
          },
          "shuntingUnit": {
              "id": agent_ids.get(str(agent), str(agent)),
              "members": [
                  {
                      "id": str(agent),
                      "type": type,
                  }
              ],
              "parentIDs": [],
              "childIDs": [],
              "standingType": "",
          },
          "location": normalize_node(i),
          "resources": [{"name": normalize_node(i), "trackPartId": normalize_node(i)}],
          "trainUnitIds": [],
        }
        plan_exits.append(task)
  return plan_exits

# combine movements, arrivals and exits into a single plan, sorted by time.
# Also add wait actions between consecutive actions of the same train if
# there is a gap in time
def combine_actions(plan_movements, plan_arrivals, plan_exits):
  task_order = {"Move": 0, "Arrive": 1, "Exit": 2}

  actions = plan_movements + plan_arrivals + plan_exits

  actions.sort(key=lambda a: (int(a["startTime"]), task_order.get(a["taskType"]["predefined"], 99),))
  # Only these actions define occupation intervals
  timing_actions = {"Move", "Exit"}

  by_train = defaultdict(list)

  for action in actions:
    if action["taskType"]["predefined"] in timing_actions:
      train_id = action["shuntingUnit"]["id"]
      by_train[train_id].append(action)

  wait_actions = []

  for train_actions in by_train.values():
    train_actions.sort(key=lambda a: int(a["startTime"]))

    for prev, nxt in zip(train_actions, train_actions[1:]):
      prev_end = int(prev["endTime"])
      next_start = int(nxt["startTime"])

      if prev_end < next_start:
        wait_actions.append({
          "startTime": str(prev_end),
          "endTime": str(next_start),
          "taskType": {
            "predefined": "Wait"
          },
          "shuntingUnit": prev["shuntingUnit"],
          "location": nxt["location"],
          "resources": [],
          "trainUnitIds": [],
        })

  actions.extend(wait_actions)

  actions.sort(
    key=lambda a: (
      int(a["startTime"]),
      task_order.get(a["taskType"]["predefined"], 99),
    )
  )

  return {
    "actions": actions,
    "trackParts": [],
  }

# rename train unit IDs in final plan based on mapping from scenario, 
# so they match the IDs expected by the evaluator. 
def remap_train_unit_ids(final_plan, mapping):
  shunting_to_new_member = {}
  for action in final_plan["actions"]:
    su = action["shuntingUnit"]
    su_id = su["id"]
    if su_id not in shunting_to_new_member:
      original = su["members"][0]["id"]
      shunting_to_new_member[su_id] = mapping.get(original, original)
    new_id = shunting_to_new_member[su_id]
    for member in su["members"]:
      member["id"] = new_id
  return final_plan

# combine consecutive move actions of the same train into a single move, 
# if they are directly consecutive in time. 
# This is needed because the solver may output two consecutive moves
# of which the first ends on a non parking track.
def combine_consecutive_moves(final_plan):
  actions = deepcopy(final_plan["actions"])

  # Sort so moves for the same shunting unit are adjacent in time
  actions.sort(key=lambda a: (a["shuntingUnit"]["id"], int(a["startTime"]), int(a["endTime"]),))
  combined = []
  i = 0
  while i < len(actions):
    current = deepcopy(actions[i])

    while (
      i + 1 < len(actions)
      and current["taskType"]["predefined"] == "Move"
      and actions[i + 1]["taskType"]["predefined"] == "Move"
      and current["shuntingUnit"]["id"]
      == actions[i + 1]["shuntingUnit"]["id"]
      and current["endTime"] == actions[i + 1]["startTime"]
    ):
      nxt = actions[i + 1]

      # Extend end time
      current["endTime"] = nxt["endTime"]
      existing = {r["trackPartId"] for r in current["resources"]}
      for resource in nxt["resources"]:
        current["resources"].append(resource)
        existing.add(resource["trackPartId"])

      i += 1

    combined.append(current)
    i += 1

  # Optional: restore chronological order afterwards
  combined.sort(key=lambda a: int(a["startTime"]))

  final_plan["actions"] = combined
  return final_plan

# for testing with a single file  
# data = ll.load_json("../data/locations/location_solver.json")
# nodes, edges, conflict_edges, expanded_edges, macro_edge_nodes, track_parts_used = pre_load_location(data)
# movements, positions, found = load_data("../data/data_types_7hours/solutions_sp/sp_rho0.5_task278_scenario_solver_33_trains_5_units19.json")
# data_scenario = ll.load_json("../data/data_types_7hours/scenarios_solver/scenario_solver_33_trains_5_units19.json")
# agents, start_nodes, arrival_times, departures, start_time, end_time, train_types = ls.load_scenario(data_scenario)
# agent_ids = assign_agent_ids(arrival_times)
# mapping = map_train_id_to_trainunit_id(data_scenario)
# plan_movements = create_movements(movements, track_parts_used, train_types, agent_ids)
# plan_arrivals = create_arrivals(positions, arrival_times, start_nodes, train_types, agents, agent_ids)
# plan_exits = create_exits(positions, departures, train_types, agents, agent_ids)
# final_plan = combine_actions(plan_movements, plan_arrivals, plan_exits)
# final_plan = remap_train_unit_ids(final_plan, mapping)
# final_plan = combine_consecutive_moves(final_plan)

# with open("final_plan_2.json", "w") as f: json.dump(final_plan, f, indent=2)

# process all solution files in the solutions directory,
# convert them to plans and save in output directory
data = ll.load_json("../data/locations/location_solver.json")
nodes, edges, conflict_edges, expanded_edges, macro_edge_nodes, track_parts_used = pre_load_location(data)

solutions_dir = Path("../data/data_types_7hours/solutions_sp")
scenarios_dir = Path("../data/data_types_7hours/scenarios_solver")
output_dir = Path("../data/data_types_7hours/plans_eval_sp")

output_dir.mkdir(exist_ok=True)

for solution_file in solutions_dir.glob("*.json"):
  try:
    print(f"Processing {solution_file.name}")

    idx = solution_file.name.find("scenario_solver")
    if idx == -1:
      print("  Skipped (no scenario match)")
      continue

    scenario_name = solution_file.name[idx:]
    scenario_path = scenarios_dir / scenario_name

    if not scenario_path.exists():
      print(f"  Missing scenario: {scenario_name}")
      continue

    movements, positions, found = load_data(str(solution_file))
    data_scenario = ll.load_json(str(scenario_path))

    agents, start_nodes, arrival_times, departures, start_time, end_time, train_types = ls.load_scenario(data_scenario)

    agent_ids = assign_agent_ids(arrival_times)
    mapping = map_train_id_to_trainunit_id(data_scenario)

    plan_movements = create_movements(movements, track_parts_used, train_types, agent_ids)
    plan_arrivals = create_arrivals(positions, arrival_times, start_nodes, train_types, agents, agent_ids)
    plan_exits = create_exits(positions, departures, train_types, agents, agent_ids)

    final_plan = combine_actions(plan_movements, plan_arrivals, plan_exits)
    final_plan = remap_train_unit_ids(final_plan, mapping)
    final_plan = combine_consecutive_moves(final_plan)

    suffix = scenario_name.replace("scenario_solver_", "")
    output_file = output_dir / f"plan_{suffix}"

    with open(output_file, "w") as f:
      json.dump(final_plan, f, indent=2)

    print(f"  Saved → {output_file.name}")

  except Exception as e:
    print(f"  Failed: {solution_file.name}")
    print(e)