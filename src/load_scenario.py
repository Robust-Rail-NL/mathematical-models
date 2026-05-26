from load_location import load_json
import math

# Represent the type as one long string of its attributes
def make_type_string(ty):
  return (
    f"{ty.get('displayName', '')}|"
    f"{ty.get('carriages', 0)}|"
    f"{ty.get('length', 0.0)}|"
    f"{ty.get('combineDuration', '0')}|"
    f"{ty.get('splitDuration', '0')}|"
    f"{ty.get('backNormTime', '0')}|"
    f"{ty.get('backAdditionTime', '0')}|"
    f"{ty.get('reversalDuration', '0')}"
  )

# Extract the necessary data for each in train
def load_in_trains(data):
  in_trains = []

  for train in data["in"]["trains"]:
    members = []

    for member in train["members"]:
      train_unit = member.get("trainUnit", {})
      ty = train_unit.get("type", {})

      members.append({
        "id": train_unit.get("id", ""),
        "type": make_type_string(ty)
      })

    in_trains.append({
      "id": train["id"],
      "entryTrackPart": train["entryTrackPart"],
      "arrival": train["arrival"],
      "departure": train["departure"],
      "firstParkingTrackPart": train["firstParkingTrackPart"],
      "members": members
    })

  return in_trains

# Extract the necessary data for each out train
def load_out_trains(data):
  out_trains = []

  for train in data["out"]["trainRequests"]:
    units = []

    for unit in train["trainUnits"]:
      ty = unit.get("type", {})

      units.append({
        "id": unit.get("id", ""),
        "type": make_type_string(ty)
      })

    out_trains.append({
      "id": train["displayName"],
      "leaveTrackPart": train["leaveTrackPart"],
      "arrival": train["arrival"],
      "departure": train["departure"],
      "lastParkingTrackPart": train["lastParkingTrackPart"],
      "standingIndex": float(train.get("standingIndex", 0.0)),
      "trainUnits": units
    })

  return out_trains

# Convert to final input format
def convert_to_input(scenario):
  start_time = math.ceil(int(scenario["startTime"]) / 60)
  end_time = math.ceil(int(scenario["endTime"]) / 60)

  agents = []
  start_nodes = {}
  arrival_time = {}
  departures = []
  train_types = {}

  for train in scenario["inTrains"]:
    train_id = train["id"]

    agents.append(train_id)
    start_nodes[train_id] = train["firstParkingTrackPart"]
    arrival_time[train_id] = int(train["arrival"]) // 60
    train_types[train_id] = train["members"][0]["type"]

  for out_train in scenario["outTrains"]:
    departures.append((
      out_train["lastParkingTrackPart"],
      out_train["trainUnits"][0]["type"],
      int(out_train["departure"]) // 60
    ))

  return (agents, start_nodes, arrival_time, departures, start_time, end_time, train_types)


def load_scenario(data):
  scenario = {
    "inTrains": load_in_trains(data),
    "outTrains": load_out_trains(data),
    "startTime": data["startTime"],
    "endTime": data["endTime"],
    "inStanding": data.get("inStanding", {}),
    "outStanding": data.get("outStanding", {})
  }

  return convert_to_input(scenario)


if __name__ == "__main__":
  data = load_json("scenarios/four_tracks/two_trains.json")
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = load_scenario(data)
  print("Agents:", agents)
  print("Start Nodes:", start_nodes)
  print("Arrival Time:", arrival_time)
  print("Departures:", departures)
  print("Start Time:", start_time)
  print("End Time:", end_time)
  print("Train Types:", train_types)