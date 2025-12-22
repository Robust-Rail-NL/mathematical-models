from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time
import math

# random.seed(45)

def objective_lagrangian(m):
  MILP_objective = sum(m.c[(i,j),t]*m.r[(i,j),t]*m.x[(i, j), t] for t in m.time_window
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

lambda_values = {(i,t): 0.0 for i in nodes for t in time_window}
mu_values = {(i,j,t): 0.0 for (i, j) in edges for t in time_window}   
r = {(i,j,t): random.uniform(0.99,1.01) for (i, j) in edges for t in time_window} 
cost = {(i,j,t): 1.0 for (i, j) in edges for t in time_window} 

# print("nodes:", nodes)
# print("edges:", edges)
# print("agents:", agents)
# print("start_nodes:", start_nodes)
# print("arrival_time:", arrival_time)
# print("departures:", departures)
# print("time_window:", time_window)
# print("train_types:", train_types)

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
  model.r = Param(model.edges, model.time_window, mutable=True, initialize=r)
  model.c = Param(model.edges, model.time_window, mutable=True, initialize=cost)
  
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

def solve_agent(a, m, k):
  diff = 1/(k+1)
  for t in time_window:   
    for l in nodes:
      m.lambda_values[l,t] = lambda_values[l,t]
    for i,j in edges:
      # m.r[(i,j),t] = random.uniform(1-diff,1+diff)
      m.r[(i,j),t] = random.uniform(0.9,1.1)
      m.c[(i,j),t] = cost[i,j,t]
      if i < j:
        m.mu_values[i,j,t] = mu_values[i,j,t]
  # Solve
  solver = SolverFactory('gurobi')
  solver.solve(m, warmstart=True, keepfiles=False)
  x_values = {(i,j): { t: (m.x[(i,j),t].value) for t in m.time_window} for (i,j) in m.edges}
  p_values = {l: { t: (m.p[l,t].value) for t in m.time_window} for l in m.nodes}
  y_values = {t: (m.y[t].value) for t in m.time_window}
  objective_value = m.cost
  return x_values, p_values, y_values, value(objective_value)

n_iter = 1000
start = time.time()
objectives = []
models = {}
for a in agents:
  models[a] = create_model(a)

x_values, p_values, y_values, objective_values = {}, {}, {}, {}
for k in range(n_iter):
  x_values, p_values, y_values, objective_values = {}, {}, {}, {}
  print(k)
  for a in agents:
    x_values[a], p_values[a], y_values[a], objective_values[a]= solve_agent(a, models[a], k)
  #region print
  # print("x[a,(i,j),t] values:")
  # for a in agents:
  #   for (i,j) in edges:
  #     for t in time_window:
  #       val = x_values[a][(i,j)][t]
  #       if val is not None and val > 0:
  #         print(f"x[{a},{i}->{j},{t}] = {val}")
  # print("\np[a,n,t] values:")
  # for a in agents:
  #   for n in nodes:
  #     for t in time_window:
  #       val = p_values[a][n][t]
  #       if val is not None and val > 0:
  #           print(f"p[{a},{n},{t}] = {val}")
  # for i in nodes:
  #   for t in time_window:
  #     if lambda_values[i,t] > 0:
  #       print(f"Lambda[{i},{t}] = {lambda_values[i,t]}")
          
  # for (i,j) in edges:
  #   if j <= i:
  #     continue
  #   for t in time_window:
  #     if mu_values[i,j,t] > 0:
  #       print(f"Mu[{i},{j},{t}] = {mu_values[i,j,t]}")  
  obj = 0
  for a in agents:
    # print(objective_values[a])
    obj += objective_values[a]
  # print("neg obj", -sum(lambda_values[l,t] for l in nodes for t in time_window) - sum(mu_values[i,j,t] for i,j in edges for t in time_window))
  obj -= sum(lambda_values[l,t] for l in nodes for t in time_window) - sum(mu_values[i,j,t] for i,j in edges for t in time_window)
  objectives.append(obj)     
  # print("objective", obj)     
  #endregion
  
  conflicts = 0
  for l in nodes:
    for t in time_window:
      # penalty = 1/(math.sqrt(k+1)) * (sum(p_values[a][l][t] for a in agents) - 1)
      penalty = 1/(k+1) * (sum(p_values[a][l][t] for a in agents) - 1)
      if penalty > 0:
        lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
        conflicts += 1
      elif penalty < 0:
        lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)

  for (i,j) in edges:
    if j <= i:
      continue
    for t in time_window:
      # penalty = 1/(math.sqrt(k+1)) * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
      penalty = 1/(k+1) * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
      if penalty > 0:
        mu_values[i,j,t] = max(0.0, mu_values[i,j,t] + penalty)
        conflicts += 1
      elif penalty < 0:
        mu_values[i,j,t] = max(0.0, mu_values[i,j,t] + penalty)    
  
  for (i,j) in edges:
    if i == j:
      continue
    for t in time_window:
      penalty = sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents)
      if penalty == 0:
        cost[i,j,t] = max(0, cost[i,j,t] - random.uniform(0.09, 0.11))
      elif penalty > 1:
        cost[i,j,t] = 1
      else:
        cost[i,j,t] += random.uniform(0.09,0.11)
  if k%10 == 0:
    print("conflcits", conflicts)
  if conflicts < 1:
    print("NO MORE CONFLICT")
    break


end_time = time.time()
print(objectives)
# Output

print("\np[a,n,t] values:")
for a in agents:
  for n in nodes:
    for t in time_window:
      val = p_values[a][n][t]
      if val is not None and val > 0:
          print(f"p[{a},{n},{t}] = {val}")
for i in nodes:
  for t in time_window:
    if lambda_values[i,t] > 0:
      print(f"Lambda[{i},{t}] = {lambda_values[i,t]}")
print("x[a,(i,j),t] values:")
for a in agents:
    for (i,j) in edges:
        for t in time_window:
            val = x_values[a][(i,j)][t]
            if val is not None and val > 0:
                print(f"x[{a},{i}->{j},{t}] = {val}")
# print("\np[a,n,t] values:")
# for a in agents:
#     for n in nodes:
#         for t in time_window:
#             val = p_values[a][n][t]
#             if val is not None and val > 0:
#                 print(f"p[{a},{n},{t}] = {val}")
print("conflicts:", conflicts)
print("Total time (seconds):", end_time - start)
print("nodes:", nodes)
print("edges:", edges)
print("agents:", agents)
print("start_nodes:", start_nodes)
print("arrival_time:", arrival_time)
print("departures:", departures)
print("time_window:", time_window)
print("train_types:", train_types)
# print("cost", cost)
print(k)