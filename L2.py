from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals
import constraints as c
import load_location as ll
import load_scenario as ls
import random
import time as time

def objective_lagrangian(m):
  MILP_objective = sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)
  node_capacity_penalty = 0
  for i in m.nodes:
    for t in m.time_window:
      lambda_value = lambda_values[i,t]
      node_capacity_penalty += lambda_value * m.node_violation[i,t]
  edge_capacity_penalty = 0
  for e in m.edges:
    i, j = e
    if j <= i:
      continue
    for t in m.time_window:
      mu_value = mu_values[i,j,t]
      edge_capacity_penalty += mu_value * m.edge_violation[i,j,t]
  return MILP_objective + node_capacity_penalty + edge_capacity_penalty

data = ll.load_json('locations/six_tracks_location.json')
nodes, edges, facilities = ll.load_location(data)
data = ll.load_json('scenarios/six_tracks/four_trains_difficult.json')
agents, start_nodes, arrival_time, departures, start_time, end_time, arrival_time, train_types = ls.load_scenario(data)
time_window = range(start_time, end_time+1)

#region print
print("nodes:", nodes)
print("edges:", edges)
print("agents:", agents)
print("start_nodes:", start_nodes)
print("arrival_time:", arrival_time)
print("departures:", departures)
print("time_window:", time_window)
print("train_types:", train_types)
# agents = [1,2,3,4,5]
# t_max = 7
# time_window = range(0, t_max)
# nodes = [1, 2, 3, 4, 5, 6, 7,8,9,10,11]
# edges = [(1, 3), (3, 1), (2, 3), (3, 2), (3, 4), (4, 3), (3, 5), (5, 3), (3,6), (6,3), (3,7), (7,3), (3,8), (8,3),(3,9), (9,3),(3,10), (10,3),(3,11), (11,3),
#          (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6,6), (7,7), (8,8), (9,9), (10,10), (11,11)]
# start_nodes = {1:1,2:2, 3:6,4:8,5:10}
# destination_nodes = {1:5,2:4,3:7,4:9,5:11}
#endregion

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

lambda_values = {(i, t): 0.0 for i in model.nodes for t in model.time_window}
mu_values = {(i, j, t): 0.0 for (i, j) in model.edges for t in model.time_window}

model.node_violation = Var(model.nodes, model.time_window, domain=NonNegativeReals)
model.edge_violation = Var(model.edges, model.time_window, domain=NonNegativeReals)

def node_violation_rule(m, i, t):
    return m.node_violation[i,t] >= sum(m.p[a,i,t] for a in m.agents) - 1
model.node_violation_constraint = Constraint(model.nodes, model.time_window, rule=node_violation_rule)

def edge_violation_rule(m, i, j, t):
    if j <= i:
        return Constraint.Skip
    return m.edge_violation[i,j,t] >= sum(m.x[a,(i,j),t] + m.x[a,(j,i),t] for a in m.agents) - 1
model.edge_violation_constraint = Constraint(model.edges, model.time_window, rule=edge_violation_rule)

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

penalty_multiplier_lambda = {(l,t): 0.5 for l in model.nodes for t in model.time_window}
penalty_multiplier_mu = {(i,j,t): 0.4 for (i,j) in model.edges for t in model.time_window}
#
n_iter = 1000
start = time.time()
for k in range(n_iter):
  result = solver.solve(model, tee=True, keepfiles=True)
  #region print
  # print(k)
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
  #endregion  
  conflicts = 0
  for l in model.nodes:
    for t in model.time_window:
      # r = random.uniform(0.9, 1.1)
      # penalty = r*penalty_multiplier_lambda[l,t] * (sum(model.p[a2,l,t].value for a2 in model.agents) - 1)
      penalty = penalty_multiplier_lambda[l,t] * (sum(model.p[a,l,t].value for a in model.agents) - 1)
      if penalty > 0.01:
        lambda_values[l,t] = max(0, lambda_values[l,t] + penalty)
        conflicts +=1
      # elif penalty < 0:
      #   lambda_values[a1,l,t] = max(0, lambda_values[a1,l,t] + penalty/2)
  for (i,j) in model.edges:
    if j <= i:
      continue
    for t in model.time_window:
      # r = random.uniform(0.9, 1.1)
      # penalty = r*penalty_multiplier_mu[i,j,t] * (sum(model.x[a2,(i,j),t].value + model.x[a2,(j,i),t].value for a2 in model.agents) - 1)
      penalty = penalty_multiplier_mu[i,j,t] * (sum(model.x[a,(i,j),t].value + model.x[a,(j,i),t].value for a in model.agents) - 1)
      if penalty > 0.01:
        mu_values[i,j,t] = max(0, mu_values[i,j,t] + penalty)
        conflicts +=1
      # elif penalty < 0:
      #   mu_values[a1,i,j,t] = max(0, mu_values[a1,i,j,t] + penalty/2)

  model.cost = Objective(rule=objective_lagrangian, sense=minimize)
  # for a in model.agents:
  #   for (i,j) in model.edges:
  #     if j <= i:
  #       continue
  #     for t in model.time_window:
  #       if model.mu_values[a,i,j,t].value > 0:
  #         print(f"Mu[{a},{i},{j},{t}] = {model.mu_values[a,i,j,t].value}")          
  # for l in model.nodes:
  #   for t in model.time_window:
  #     if (sum(model.p[a2,l,t].value for a2 in model.agents) - 1) > 0:
  #       penalty_multiplier_lambda[l,t] *= 1/(k+1)
  # for (i,j) in model.edges:
  #   if j <= i:
  #     continue
  #   for t in model.time_window:
  #     if (sum(model.x[a2,(i,j),t].value + model.x[a2,(j,i),t].value for a2 in model.agents) - 1) > 0:
  #       penalty_multiplier_mu[i,j,t] *= 1/(k+1)
  # penalty per var
  if conflicts < 1:
    print("NO MORE CONFLICT")
    break
end_time = time.time()
print("Total time (seconds):", end_time - start)
# Output
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


