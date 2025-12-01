from load_location import load_json
from dataclasses import dataclass

@dataclass
class TrainUnitType:
  displayName: str
  carriages: int
  length: float
  combineDuration: str
  splitDuration: str
  backNormTime: str
  backAdditionTime: str
  reversalDuration: str

@dataclass
class TrainUnit:
  id: str
  type: TrainUnitType

@dataclass
class InTrain:
  id: str
  entryTrackPart: str
  arrival: str
  departure: str
  firstParkingTrackPart: str
  members: []
  
@dataclass
class OutTrain:
  id: str  # displayName
  leaveTrackPart: str
  arrival: str
  departure: str
  lastParkingTrackPart: str
  trainUnits: []
  standingIndex: float

@dataclass
class Scenario:
  inTrains: []
  outTrains: []
  startTime: str
  endTime: str
  inStanding: {}
  outStanding: {}

def loadInTrains(data):
  in_trains = []
  for train in data["in"]["trains"]:
    members = []
    for member in train["members"]:
      tu_type = TrainUnitType(
        displayName=member["trainUnit"]["type"]["displayName"],
        carriages=member["trainUnit"]["type"]["carriages"],
        length=member["trainUnit"]["type"]["length"],
        combineDuration=member["trainUnit"]["type"]["combineDuration"],
        splitDuration=member["trainUnit"]["type"]["splitDuration"],
        backNormTime=member["trainUnit"]["type"]["backNormTime"],
        backAdditionTime=member["trainUnit"]["type"]["backAdditionTime"],
        reversalDuration=member["trainUnit"]["type"]["reversalDuration"])
      members.append(TrainUnit(id=member["trainUnit"]["id"], type=tu_type))
    
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
  for train in data["out"]["trainRequests"]:
    units = []
    for unit in train["trainUnits"]:
      tu_type = TrainUnitType(
        displayName=unit["type"]["displayName"],
        carriages=unit["type"]["carriages"],
        length=unit["type"]["length"],
        combineDuration=unit["type"]["combineDuration"],
        splitDuration=unit["type"]["splitDuration"],
        backNormTime=unit["type"]["backNormTime"],
        backAdditionTime=unit["type"]["backAdditionTime"],
        reversalDuration=unit.get("reversalDuration", "0"))
      units.append(TrainUnit(id=unit.get("id", ""), type=tu_type))

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
  start_time = int(int(scenario.startTime)/60)
  end_time = int(int(scenario.endTime)/60)
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
  data = load_json('../scenario-planning-inputs/Scenario_settings/SimpleService/scenario_no-service_solver.json')
  agents, start_nodes, destination_nodes, start_time, end_time, arrival_time, departure_time = load_scenario(data)
  print("Agents:", agents)
  print("Start Nodes:", start_nodes)
  print("Destination Nodes:", destination_nodes)
  print("Start Time:", start_time)
  print("End Time:", end_time)
  print("Arrival Time:", arrival_time)
  print("Departure Time:", departure_time)