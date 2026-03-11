from load_location import load_json
from dataclasses import dataclass
import math

@dataclass
class TrainUnitType:
  displayName: str = ""
  carriages: int = 0
  length: float = 0.0
  combineDuration: str = "0"
  splitDuration: str = "0"
  backNormTime: str = "0"
  backAdditionTime: str = "0"
  reversalDuration: str = "0"

@dataclass
class TrainUnit:
  type: TrainUnitType
  id: str = "" 

@dataclass
class InTrain:
  members: []
  id: str = ""
  entryTrackPart: str = ""
  arrival: str = "0"
  departure: str = "0"
  firstParkingTrackPart: str = ""
  
@dataclass
class OutTrain:
  trainUnits: []
  id: str = ""  # displayName
  leaveTrackPart: str = ""
  arrival: str = "0"
  departure: str = "0"
  lastParkingTrackPart: str = ""
  standingIndex: float = 0.0

@dataclass
class Scenario:
  inTrains: []
  outTrains: []
  inStanding: {}
  outStanding: {}
  startTime: str = "0"
  endTime: str = "0"

def loadInTrains(data):
  in_trains = []
  i = 0
  for train in data["in"]["trains"]:
    members = []
    for member in train["members"]:
      t = member.get("trainUnit", {})
      ty = t.get("type", {})

      tu_type = TrainUnitType(
          displayName=ty.get("displayName", ""),
          carriages=ty.get("carriages", 0),
          length=ty.get("length", 0.0),
          combineDuration=ty.get("combineDuration", "0"),
          splitDuration=ty.get("splitDuration", "0"),
          backNormTime=ty.get("backNormTime", "0"),
          backAdditionTime=ty.get("backAdditionTime", "0"),
          reversalDuration=ty.get("reversalDuration", "0"),
      )
      tu_type.displayName = (
        # f"{i}"
        f"{tu_type.displayName}|"
        f"{tu_type.carriages}|"
        f"{tu_type.length}|"
        f"{tu_type.combineDuration}|"
        f"{tu_type.splitDuration}|"
        f"{tu_type.backNormTime}|"
        f"{tu_type.backAdditionTime}|"
        f"{tu_type.reversalDuration}"
      )
      members.append(TrainUnit(id=t.get("id", ""), type=tu_type))
      i += 1
      # tu_type = TrainUnitType(
      #   displayName=member["trainUnit"]["type"]["displayName"],
      #   carriages=member["trainUnit"]["type"]["carriages"],
      #   length=member["trainUnit"]["type"]["length"],
      #   combineDuration=member["trainUnit"]["type"]["combineDuration"],
      #   splitDuration=member["trainUnit"]["type"]["splitDuration"],
      #   backNormTime=member["trainUnit"]["type"]["backNormTime"],
      #   backAdditionTime=member["trainUnit"]["type"]["backAdditionTime"],
      #   reversalDuration=member["trainUnit"]["type"]["reversalDuration"])
      # members.append(TrainUnit(id=member["trainUnit"]["id"], type=tu_type))
    
    in_trains.append(
      InTrain(
        id=train["id"], 
        entryTrackPart=train["entryTrackPart"],
        arrival=train["arrival"],
        departure=train["departure"],
        firstParkingTrackPart=train["firstParkingTrackPart"],
        members=members)
    )
  return in_trains

def loadOutTrains(data):
  out_trains = []
  i = 0
  for train in data["out"]["trainRequests"]:
    units = []
    for unit in train["trainUnits"]:
      ty = unit.get("type", {})

      tu_type = TrainUnitType(
          displayName=ty.get("displayName", ""),
          carriages=ty.get("carriages", 0),
          length=ty.get("length", 0.0),
          combineDuration=ty.get("combineDuration", "0"),
          splitDuration=ty.get("splitDuration", "0"),
          backNormTime=ty.get("backNormTime", "0"),
          backAdditionTime=ty.get("backAdditionTime", "0"),
          reversalDuration=ty.get("reversalDuration", "0"),
      )
      tu_type.displayName = (
        # f"{i}"
        f"{tu_type.displayName}|"
        f"{tu_type.carriages}|"
        f"{tu_type.length}|"
        f"{tu_type.combineDuration}|"
        f"{tu_type.splitDuration}|"
        f"{tu_type.backNormTime}|"
        f"{tu_type.backAdditionTime}|"
        f"{tu_type.reversalDuration}"
      )

      units.append(TrainUnit(id=unit.get("id", ""), type=tu_type))
      i += 1
      # tu_type = TrainUnitType(
      #   displayName=unit["type"]["displayName"],
      #   carriages=unit["type"]["carriages"],
      #   length=unit["type"]["length"],
      #   combineDuration=unit["type"]["combineDuration"],
      #   splitDuration=unit["type"]["splitDuration"],
      #   backNormTime=unit["type"]["backNormTime"],
      #   backAdditionTime=unit["type"]["backAdditionTime"],
      #   reversalDuration=unit.get("reversalDuration", "0"))
      # units.append(TrainUnit(id=unit.get("id", ""), type=tu_type))

    out_trains.append(
      OutTrain(
        id=train["displayName"],
        leaveTrackPart=train["leaveTrackPart"],
        arrival=train["arrival"],
        departure=train["departure"],
        lastParkingTrackPart=train["lastParkingTrackPart"],
        trainUnits=units,
        standingIndex=float(train.get("standingIndex", 0.0))
      )
    )
  return out_trains

def convert_to_input(scenario):
  start_time = int(math.ceil(int(scenario.startTime)/60))
  end_time = int(math.ceil(int(scenario.endTime)/60))
  agents = []
  start_nodes = {}
  arrival_time = {}
  departures = []
  train_types = {}
  for train in scenario.inTrains:
    agents.append(train.id)
    start_nodes[train.id] = train.firstParkingTrackPart
    arrival_time[train.id] = int(int(train.arrival)/60)
    train_types[train.id] = train.members[0].type.displayName

  for out_train in scenario.outTrains:
    departures.append((out_train.lastParkingTrackPart, out_train.trainUnits[0].type.displayName, int(int(out_train.departure)/60)))
     
  return agents, start_nodes, arrival_time, departures, start_time, end_time, train_types

def load_scenario(data):
    in_trains = loadInTrains(data)
    out_trains = loadOutTrains(data)
    scenario = Scenario(
      inTrains=in_trains,
      outTrains=out_trains,
      startTime=data["startTime"],
      endTime=data["endTime"],
      inStanding=data.get("inStanding", {}),
      outStanding=data.get("outStanding", {}))
    agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = convert_to_input(scenario)
    return agents, start_nodes, arrival_time, departures, start_time, end_time, train_types



if __name__ == "__main__":
  # data = load_json('../scenario-planning-inputs/Scenario_settings/SimpleService/scenario_no-service_solver.json')
  data = load_json('scenarios/four_tracks/two_trains.json')
  # data = load_json('scenarios/kleinebinckhorst/test.json')
  agents, start_nodes, destination_nodes, start_time, end_time, arrival_time, departure_time = load_scenario(data)
  print("Agents:", agents)
  print("Start Nodes:", start_nodes)
  print("Destination Nodes:", destination_nodes)
  print("Start Time:", start_time)
  print("End Time:", end_time)
  print("Arrival Time:", arrival_time)
  print("Departure Time:", departure_time)