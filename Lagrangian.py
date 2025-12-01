from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals
import constraints as c
import load_location as ll
import load_scenario as ls
import random
import time

def objective_lagrangian(m):
  MILP_objective = sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)
  node_capacity_penalty = 0
  for i in m.nodes:
    for t in m.time_window:
      lambda_value = m.lambda_values[i,t]
      node_capacity_penalty += lambda_value * (sum(m.p[a,i,t] for a in m.agents)-1)
  edge_capacity_penalty = 0
  for e in m.edges:
    i, j = e
    if j <= i:
      continue
    for t in m.time_window:
      mu_value = m.mu_values[i,j,t]
      edge_capacity_penalty += mu_value * (sum(m.x[a,(i,j),t] + m.x[a, (j,i), t] for a in m.agents)-1)
  return MILP_objective + node_capacity_penalty + edge_capacity_penalty

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

model.lambda_values = Param(model.nodes, model.time_window, mutable=True, initialize=0.0)
model.mu_values = Param(model.edges, model.time_window, mutable=True, initialize=0.0)

# Objective
model.cost = Objective(rule=objective_lagrangian, sense=minimize)

# Constraint
model.initial = Constraint(model.agents, rule=c.inital_position_constraint)
model.location = Constraint(model.agents, model.time_window, rule=c.location_constraint)
model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_departure)
model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_arrival)
model.match_agent_destination = Constraint(model.agents, rule=c.match_agent_destination)
model.train_presence = Constraint(model.agents, model.departures, rule=c.train_presence_constraint)
model.train_not_present = Constraint(model.agents, model.departures, rule=c.train_not_present_constraint)
model.train_presence_continuity = Constraint(model.agents, model.time_window, rule=c.train_presence_continuity_constraint)


# # Solve using Gurobi
solver = SolverFactory('gurobi')

penalty_multiplier_lambda = {(l,t): 1.6 for l in model.nodes for t in model.time_window}
penalty_multiplier_mu = {(i,j,t): 2 for (i,j) in model.edges for t in model.time_window}
#
n_iter = 1000
start = time.time()
for k in range(n_iter):
  result = solver.solve(model, warmstart=True, keepfiles=False)
  #region print
  print(k)
  # print("x[a,(i,j),t] values:")
  # for a in model.agents:
  #     for (i,j) in model.edges:
  #         for t in model.time_window:
  #             val = model.x[a, (i,j), t].value
  #             if val is not None and val > 0:
  #                 print(f"x[{a},{i}->{j},{t}] = {val}")
  # print("\np[a,n,t] values:")
  # for a in model.agents:
  #     for n in model.nodes:
  #         for t in model.time_window:
  #             val = model.p[a, n, t].value
  #             if val is not None and val > 0:
  #                 print(f"p[{a},{n},{t}] = {val}")
  # print("Objective (cost):", model.cost())
  # for i in model.nodes:
  #   for t in model.time_window:
  #     if lambda_values[i,t] > 0:
  #       print(f"Lambda[{i},{t}] = {lambda_values[i,t]}")
  # for (i,j) in model.edges:
  #   if j <= i:
  #     continue
  #   for t in model.time_window:
  #     if mu_values[i,j,t] > 0:
  #       print(f"Mu[{i},{j},{t}] = {mu_values[i,j,t]}")   
  # print("Objective (cost):", model.cost())   
  #endregion  
  for l in model.nodes:
    for t in model.time_window:
      # if (sum(model.p[a2,l,t].value for a2 in model.agents) - 1) > 0:
      penalty_multiplier_lambda[l,t] *= 1/(k+1)
  for (i,j) in model.edges:
    if j <= i:
      continue
    for t in model.time_window:
      # if (sum(model.x[a2,(i,j),t].value + model.x[a2,(j,i),t].value for a2 in model.agents) - 1) > 0:
      penalty_multiplier_mu[i,j,t] *= 1/(k+1)
  conflicts = 0
  for l in model.nodes:
    for t in model.time_window:
      r = random.uniform(0.9, 1.1)
      penalty = r*penalty_multiplier_lambda[l,t] * (sum(model.p[a2,l,t].value for a2 in model.agents) - 1)
      # penalty = penalty_multiplier_lambda[l,t] * (sum(model.p[a,l,t].value for a in model.agents) - 1)
      penalty = max(0.01, penalty)
      # if k >=170:
      #   print("huh",sum(model.p[a,l,t].value for a in model.agents))
      if penalty > 0:
        model.lambda_values[l,t] = max(0, model.lambda_values[l,t].value + penalty)
        conflicts +=1
      # elif penalty <= 0:
      #   model.lambda_values[l,t] = max(0, model.lambda_values[l,t].value + penalty/2)
  for (i,j) in model.edges:
    if j <= i:
      continue
    for t in model.time_window:
      r = random.uniform(0.9, 1.1)
      penalty = r*penalty_multiplier_mu[i,j,t] * (sum(model.x[a2,(i,j),t].value + model.x[a2,(j,i),t].value for a2 in model.agents) - 1)
      # penalty = penalty_multiplier_mu[i,j,t] * (sum(model.x[a,(i,j),t].value + model.x[a,(j,i),t].value for a in model.agents) - 1)
      penalty = max(0.01, penalty)
      if penalty > 0:
        model.mu_values[i,j,t] = max(0, model.mu_values[i,j,t].value + penalty)
        conflicts +=1
      # elif penalty <= 0:
      #   model.mu_values[i,j,t] = max(0, model.mu_values[i,j,t].value + penalty/2)     
  # penalty per var
  if conflicts < 1:
    print("NO MORE CONFLICT")
    break
end_time = time.time()
# Output
# print("x[a,(i,j),t] values:")
# for a in model.agents:
#     for (i,j) in model.edges:
#         for t in model.time_window:
#             val = model.x[a, (i,j), t].value
#             if val is not None and val > 0:
#                 print(f"x[{a},{i}->{j},{t}] = {val}")
print("\np[a,n,t] values:")
for a in model.agents:
    for n in model.nodes:
        for t in model.time_window:
            val = model.p[a, n, t].value
            if val is not None and val > 0:
                print(f"p[{a},{n},{t}] = {val}")

print("Total time (seconds):", end_time - start)
print("Objective (cost):", model.cost())

print("nodes:", nodes)
print("edges:", edges)
print("agents:", agents)
print("start_nodes:", start_nodes)
print("arrival_time:", arrival_time)
print("departures:", departures)
print("time_window:", time_window)
print("train_types:", train_types)
