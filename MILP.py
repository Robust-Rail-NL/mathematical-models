from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory
import constraints as c
import load_location as ll
import load_scenario as ls
import time

def objective(m):
  return sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)

data = ll.load_json('locations/six_tracks_location.json')
nodes, edges, facilities = ll.load_location(data)
data = ll.load_json('scenarios/six_tracks/four_trains.json')
agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
time_window = range(start_time, end_time+1)

model = ConcreteModel()

# Sets
model.agents = Set(initialize=agents)
model.time_window = Set(initialize=time_window)
model.nodes = Set(initialize=nodes)
model.edges = Set(initialize=edges, dimen=2)
model.start_nodes = Param(model.agents, initialize=start_nodes)
model.arrival_time = Param(model.agents, initialize=arrival_time)
model.departures = Set(initialize=departures, dimen=3)
model.train_types = Param(model.agents, initialize=train_types)

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
model.match_agent_destination = Constraint(model.agents, rule=c.match_agent_destination)
model.train_presence = Constraint(model.agents, model.departures, rule=c.train_presence_constraint)
model.train_not_present = Constraint(model.agents, model.departures, rule=c.train_not_present_constraint)
model.train_presence_continuity = Constraint(model.agents, model.time_window, rule=c.train_presence_continuity_constraint)
# model.no_movement_when_not_present = Constraint(model.agents, model.edges, model.time_window, rule=c.no_movement_when_not_present_constraint)

# # Solve using Gurobi
solver = SolverFactory('gurobi')
start = time.time()
result = solver.solve(model, tee=True, keepfiles=True)
end = time.time()
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
print("Time taken (seconds):", end - start)


print("nodes:", nodes)
print("edges:", edges)
print("agents:", agents)
print("start_nodes:", start_nodes)
print("arrival_time:", arrival_time)
print("departures:", departures)
print("time_window:", time_window)
print("train_types:", train_types)