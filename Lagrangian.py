from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory
import constraints as c
import load_location as ll
import load_scenario as ls

def objective_lagrangian(m):
  MILP_objective = sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)
  node_capacity_penalty = 0
  for l in m.nodes:
    for t in m.time_window:
      lambda_value = lambda_values[l,t]
      node_capacity_penalty += lambda_value * (sum(m.p[a,l,t] for a in m.agents) - 1)
  edge_capacity_penalty = 0
  for e in m.edges:
    i, j = e
    if i == j or j < i:
      continue
    for t in m.time_window:
      mu_value = mu_values[i,j,t]
      edge_capacity_penalty += mu_value * (sum(m.x[a,(i,j),t] + m.x[a, (j,i), t] for a in m.agents) - 1)
  return MILP_objective + node_capacity_penalty + edge_capacity_penalty

agents = [1,2]
t_max = 4
time_window = range(0, t_max)
nodes = [1, 2, 3, 4, 5]
edges = [(1, 3), (3, 1), (2, 3), (3, 2), (3, 4), (4, 3), (3, 5), (5, 3),
         (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
start_nodes = {1:1,2:2}
destination_nodes = {1:5,2:4}
data = ll.load_json('../robust-rail-generator/data/locations/simple_service_location_solver.json')
nodes, edges, facilities = ll.load_location(data)
data = ll.load_json('../scenario-planning-inputs/Scenario_settings/SimpleService/scenario_no-service_solver.json')
agents, start_nodes, destination_nodes, start_time, end_time = ls.load_scenario(data)
time_window = range(int(start_time), int(int(end_time)/8000) + 1)

model = ConcreteModel()

# Sets
model.agents = Set(initialize=agents)
model.time_window = Set(initialize=time_window)
model.nodes = Set(initialize=nodes)
model.edges = Set(initialize=edges, dimen=2)
model.start_nodes = Param(model.agents, initialize=start_nodes)
model.destination_nodes = Param(model.agents, initialize=destination_nodes)

model.x = Var(model.agents, model.edges, model.time_window, domain=Binary)
model.p = Var(model.agents, model.nodes, model.time_window, domain=Binary)

# Lagrangian Lambda and Mu variables
lambda_values = {(i, t): 1.0 for i in model.nodes for t in model.time_window}

mu_values = {(i, j, t): 1.0 for (i, j) in model.edges for t in model.time_window}


# Objective
model.cost = Objective(rule=objective_lagrangian, sense=minimize)


# Constraint
model.initial = Constraint(model.agents, rule=c.inital_position_constraint)
model.location = Constraint(model.agents, model.time_window, rule=c.location_constraint)
model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_departure)
model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_arrival)
model.destination_reached = Constraint(model.agents, rule=c.destination_reached_constraint)


# # Solve using Gurobi
solver = SolverFactory('gurobi')


#
n_iter = 100
for i in range(n_iter):
  result = solver.solve(model, tee=True, keepfiles=True)
  lambda_values = {(l,t): max(0, lambda_values[l,t] + 
                  0.1 * (sum(model.p[a,l,t].value for a in model.agents) - 1))
                  for l in model.nodes for t in model.time_window}
  mu_values = {(i,j,t): max(0, mu_values[i,j,t] + 
              0.1 * (sum(model.x[a,(i,j),t].value + model.x[a,(j,i),t].value for a in model.agents) - 1))
              for (i,j) in model.edges for t in model.time_window if i != j and i < j}
  model.cost = Objective(rule=objective_lagrangian, sense=minimize)

print(lambda_values)


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
print("Objective (cost):", model.cost())


