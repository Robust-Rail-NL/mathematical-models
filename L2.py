from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time

def objective_lagrangian(m):
  MILP_objective = sum(m.x[(i, j), t] for t in m.time_window
            for (i, j) in m.edges if i != j)
  node_capacity_penalty = 0
  for i in m.nodes:
    for t in m.time_window:
      lambda_value = m.lambda_values[i,t]
      node_capacity_penalty += lambda_value * m.p[i,t] 
  edge_capacity_penalty = 0
  for e in m.edges:
    i, j = e
    if j <= i:
      continue
    for t in m.time_window:
      mu_value = m.mu_values[i,j,t]
      edge_capacity_penalty += mu_value * (m.x[(i,j),t] + m.x[(j,i),t])
  return MILP_objective + node_capacity_penalty + edge_capacity_penalty

data = ll.load_json('locations/five_tracks_location.json')
nodes, edges, facilities = ll.load_location(data)
data = ll.load_json('scenarios/five_tracks/three_trains.json')
agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
time_window = range(start_time, end_time+1)

lambda_values = {(a,i,t): 0.0 for a in agents for i in nodes for t in time_window}
mu_values = {(a,i,j,t): 0.0 for a in agents for (i, j) in edges for t in time_window}

print("nodes:", nodes)
print("edges:", edges)
print("agents:", agents)
print("start_nodes:", start_nodes)
print("arrival_time:", arrival_time)
print("departures:", departures)
print("time_window:", time_window)
print("train_types:", train_types)


def create_model(a):
  model = ConcreteModel()
  
  model.time_window = Set(initialize=time_window)
  model.nodes = Set(initialize=nodes)
  model.edges = Set(initialize=edges, dimen=2)
  model.start_node = Param(initialize=start_nodes[a])
  model.arrival_time = Param(initialize=arrival_time[a])
  model.departures = Set(initialize=departures, dimen=3)
  model.train_type = Param(initialize=train_types[a])

  model.x = Var(model.edges, model.time_window, domain=Binary)
  model.p = Var(model.nodes, model.time_window, domain=Binary)
  model.y = Var(model.time_window, domain=Binary)

  model.lambda_values = Param(model.nodes, model.time_window, mutable=True, initialize=0.0)
  model.mu_values = Param(model.edges, model.time_window, mutable=True, initialize=0.0)
  
  # Objective
  model.cost = Objective(rule=objective_lagrangian, sense=minimize)

  # Constraint
  model.initial = Constraint(rule=c.inital_position_constraint)
  model.location = Constraint(model.time_window, rule=c.location_constraint)
  model.movement_departure = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_departure)
  model.movement_arrival = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_arrival)
  model.match_agent_destination = Constraint(rule=c.match_agent_destination)
  model.train_presence = Constraint(model.departures, rule=c.train_presence_constraint)
  model.train_not_present = Constraint(model.departures, rule=c.train_not_present_constraint)
  model.train_presence_continuity = Constraint(model.time_window, rule=c.train_presence_continuity_constraint)
  
  return model

def solve_agent(a, m):
  for l in nodes:
    for t in time_window: 
      m.lambda_values[l,t] = lambda_values[a,l,t]
  for i,j in edges:
    for t in time_window:
      m.mu_values[i,j,t] = mu_values[a,i,j,t]
  # m.lambda_values = lambda_values
  # m.mu_values = mu_values
  
  # Solve using Gurobi
  solver = SolverFactory('gurobi')
  solver.solve(m, warmstart=True, keepfiles=False)
  x_values = {(i,j): { t: (m.x[(i,j),t].value) for t in m.time_window} for (i,j) in m.edges }
  p_values = {l: { t: (m.p[l,t].value) for t in m.time_window} for l in m.nodes}
  y_values = {t: (m.y[t].value) for t in m.time_window}
  objective_value = m.cost
  
  return x_values, p_values, y_values, value(objective_value)

penalty_multiplier_lambda = {(l,t): 8 for l in nodes for t in time_window}
penalty_multiplier_mu = {(i,j,t): 10 for (i,j) in edges for t in time_window}
violation_counts_lambda = {(l,t): 0 for l in nodes for t in time_window}
violation_counts_mu = {(i,j,t): 0 for (i,j) in edges for t in time_window}

n_iter = 30
start = time.time()

models = {}
x_values, p_values, y_values, objective_values = {}, {}, {}, {}
for a in agents:
  models[a] = create_model(a)
for k in range(n_iter):
  x_values, p_values, y_values, objective_values = {}, {}, {}, {}
  for a in agents:
    x_values[a], p_values[a], y_values[a], objective_values[a]= solve_agent(a, models[a])
  #region print
  print(k)
  # print("x[a,(i,j),t] values:")
  # for a in agents:
  #     for (i,j) in edges:
  #         for t in time_window:
  #             val = x_values[a][(i,j)][t]
  #             if val is not None and val > 0:
  #                 print(f"x[{a},{i}->{j},{t}] = {val}")
  print("\np[a,n,t] values:")
  for a in agents:
      for n in nodes:
          for t in time_window:
              val = p_values[a][n][t]
              if val is not None and val > 0:
                  print(f"p[{a},{n},{t}] = {val}")
  for a in agents:
    for i in nodes:
      for t in time_window:
        if lambda_values[a,i,t] > 0:
          print(f"Lambda[{a},{i},{t}] = {lambda_values[a,i,t]}")
  # for (i,j) in edges:
  #   if j <= i:
  #     continue
  #   for t in time_window:
  #     if mu_values[i,j,t] > 0:
  #       print(f"Mu[{i},{j},{t}] = {mu_values[i,j,t]}")  
  #endregion  
  
  for l in nodes:
    for t in time_window:
      # if (sum(model.p[a2,l,t].value for a2 in model.agents) - 1) > 0:
      penalty_multiplier_lambda[l,t] *= 1/(violation_counts_lambda[l,t]/15+1)
  for (i,j) in edges:
    if j <= i:
      continue
    for t in time_window:
      # if (sum(model.x[a2,(i,j),t].value + model.x[a2,(j,i),t].value for a2 in model.agents) - 1) > 0:
      penalty_multiplier_mu[i,j,t] *= 1/(violation_counts_mu[i,j,t]/15+1)
  
  conflicts = 0
  updated = False
  for a1 in agents:
    for l in nodes:
      for t in time_window:
        r = random.uniform(0.8, 1.2)
        penalty = r*penalty_multiplier_lambda[l,t] * (sum(p_values[a][l][t] for a in agents)-1)
        violation = (sum(p_values[a][l][t] for a in agents) - 1)
        # penalty = penalty_multiplier_lambda[l,t] * (sum(p_values[a][l][t] for a in agents) - 1)
        if violation > 0 and p_values[a1][l][t] != 0:
          lambda_values[a1,l,t] = max(0.01, lambda_values[a1,l,t] + penalty)
          conflicts +=1
          if not updated:
            violation_counts_lambda[l,t] += 1
            updated = True
        elif violation <= 0 and lambda_values[a1,l,t] != 0:
          lambda_values[a1,l,t] = max(0.01, lambda_values[a1,l,t]/2)
  updated = False
  for a1 in agents:
    for (i,j) in edges:
      if j <= i:
        continue
      for t in time_window:
        r = random.uniform(0.8, 1.2)
        penalty = r*penalty_multiplier_mu[i,j,t] * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents)-1)
        violation = (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents)-1)
        # penalty = penalty_multiplier_mu[i,j,t] * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
        if violation > 0 and x_values[a1][(i,j)][t] + x_values[a1][(j,i)][t] != 0:
          mu_values[a1,i,j,t] = max(0.01, mu_values[a1,i,j,t] + penalty)
          conflicts +=1
          if not updated:
            violation_counts_mu[i,j,t] += 1
            updated = True
        elif violation <= 0 and mu_values[a1,i,j,t] != 0:
          mu_values[a1,i,j,t] = max(0.01, mu_values[a1,i,j,t]/2)     
    # penalty per var
  if conflicts < 1:
    print("NO MORE CONFLICT")
    break
end_time = time.time()

# Output
print("x[a,(i,j),t] values:")
for a in agents:
    for (i,j) in edges:
        for t in time_window:
            val = x_values[a][(i,j)][t]
            if val is not None and val > 0:
                print(f"x[{a},{i}->{j},{t}] = {val}")
print("\np[a,n,t] values:")
for a in agents:
    for n in nodes:
        for t in time_window:
            val = p_values[a][n][t]
            if val is not None and val > 0:
                print(f"p[{a},{n},{t}] = {val}")
# print("Total time (seconds):", end_time - start)
# # print("Objective (cost):", sum(objective_values[a] for a in agents) -
# #                           sum(lambda_values[l,t] for l in nodes for t in time_window) -
# #                           sum(mu_values[i,j,t] for i,j in edges for t in time_window))
# print("conflicts:", conflicts)
# print("nodes:", nodes)
# print("edges:", edges)
# print("agents:", agents)
# print("start_nodes:", start_nodes)
# print("arrival_time:", arrival_time)
# print("departures:", departures)
# print("time_window:", time_window)
# print("train_types:", train_types)
