from load_location import load_json

def load_scenario(data):
  start_time = data['startTime']
  end_time = data['endTime']
  agents = []
  start_nodes = {}
  destination_nodes = {}
  for train in data['in']['trains']:
    agents.append(train['id'])
    start_nodes[train['id']] = train['firstParkingTrackPart']
    destination_nodes[train['id']] = None
  for out_train in data['out']['trainRequests']:
    for in_train in data['in']['trains']:
      if destination_nodes[in_train['id']] is None:
        if out_train['trainUnits'][0]['type']['displayName'] == in_train['members'][0]['trainUnit']['type']['displayName']:
          destination_nodes[in_train['id']] = out_train['lastParkingTrackPart']
  return agents, start_nodes, destination_nodes, start_time, end_time

if __name__ == "__main__":
  data = load_json('../scenario-planning-inputs/Scenario_settings/SimpleService/scenario_no-service_solver.json')
  agents, start_nodes, destination_nodes, start_time, end_time = load_scenario(data)
  print("Agents:", agents)
  print("Start Nodes:", start_nodes)
  print("Destination Nodes:", destination_nodes)
  print("Start Time:", start_time)
  print("End Time:", end_time)