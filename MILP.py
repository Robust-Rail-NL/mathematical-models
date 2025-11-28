from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory
import constraints as c
import load_location as ll
import load_scenario as ls

def objective(m):
  return sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)

agents = [1,2,3]
t_max = 8
time_window = range(0, t_max)
nodes = [1, 2, 3, 4, 5,6]
edges = [(1, 3), (3, 1), (2, 3), (3, 2), (3, 4), (4, 3), (3, 5), (5, 3), (3,6),(6,3),
         (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6,6)]
start_nodes = {1:1,2:2,3:4}
arrival_time = {1:1, 2:1,3:0}
# destination_nodes = {1:5,2:4}
# departure_time = {1:3, 2:2}
departures = [(5,4), (3,5),(6,5)]
# print("agents:", agents)
# print("start_nodes:", start_nodes)
# print("destination_nodes:", destination_nodes)
# print("start_time:", 0)
# print("end_time:", t_max)
# print("arrival_time:", arrival_time)
# print("departure_time:", departure_time)
# data = ll.load_json('../robust-rail-generator/data/locations/simple_service_location_solver.json')
# nodes, edges, facilities = ll.load_location(data)
# data = ll.load_json('../scenario-planning-inputs/Scenario_settings/SimpleService/scenario_no-service_solver.json')
# agents, start_nodes, destination_nodes, start_time, end_time, arrival_time, departure_time = ls.load_scenario(data)
# time_window = range(int(start_time), int(int(end_time)) + 1)

model = ConcreteModel()

# Sets
model.agents = Set(initialize=agents)
model.time_window = Set(initialize=time_window)
model.nodes = Set(initialize=nodes)
model.edges = Set(initialize=edges, dimen=2)
model.start_nodes = Param(model.agents, initialize=start_nodes)
model.arrival_time = Param(model.agents, initialize=arrival_time)
# model.destination_nodes = Param(model.agents, initialize=destination_nodes)
# model.departure_time = Param(model.agents, initialize=departure_time)
model.departures = Set(initialize=departures, dimen=2)

model.x = Var(model.agents, model.edges, model.time_window, domain=Binary)
model.p = Var(model.agents, model.nodes, model.time_window, domain=Binary)
model.y = Var(model.agents, model.time_window, domain=Binary)

# Objective
model.cost = Objective(rule=objective, sense=minimize)


# Constraint
model.initial = Constraint(model.agents, rule=c.inital_position_constraint)
model.location = Constraint(model.agents, model.time_window, rule=c.location_constraint)
model.node_capacity = Constraint(model.nodes, model.time_window, rule=c.node_capacity_constraint)
model.edge_capacity = Constraint(model.edges, model.time_window, rule=c.edge_capacity_constraint)
model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_departure)
model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_arrival)
# model.destination_reached = Constraint(model.agents, rule=c.destination_reached_constraint)
model.match_agent_destination = Constraint(model.agents, rule=c.match_agent_destination)
model.train_presence = Constraint(model.agents, model.departures, rule=c.train_presence_constraint)
model.train_not_present = Constraint(model.agents, model.departures, rule=c.train_not_present_constraint)
model.train_presence_continuity = Constraint(model.agents, model.time_window, rule=c.train_presence_continuity_constraint)
# model.no_movement_when_not_present = Constraint(model.agents, model.edges, model.time_window, rule=c.no_movement_when_not_present_constraint)

# # Solve using Gurobi
solver = SolverFactory('gurobi')
result = solver.solve(model, tee=True, keepfiles=True)
# # Output
print("x[a,(i,j),t] values:")
for a in model.agents:
    for (i,j) in model.edges:
        for t in model.time_window:
            val = model.x[a, (i,j), t].value
            if val is not None and val > 0:
                print(f"x[{a},{i}->{j},{t}] = {val}")
print("\np[a,n,t] values:")
for a in model.agents:
    for n in model.nodes:
        for t in model.time_window:
            val = model.p[a, n, t].value
            if val is not None and val > 0:
                print(f"p[{a},{n},{t}] = {val}")
print("\ny[a,t] values:")
for a in model.agents:
    for t in model.time_window:
        val = model.y[a, t].value
        if val is not None and val > 0:
            print(f"y[{a},{t}] = {val}")                
print("Objective (cost):", model.cost())


