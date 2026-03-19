from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value, RangeSet
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict

random.seed(1)

def objective_lagrangian(m):
  objective = 0
  for t in m.time_window:
    for e in m.edges:
      i, j = e
      if j <= i:
        continue
      objective += 0.01*(m.x[(i, j), t] + m.x[(j, i), t])
    for g in m.conflict_groups:
      objective += (m.mu_values[g,t] + m.edge_admm[g,t,1]) * sum(m.x[e,t] for e in m.conflict_edges[g]) + (1 - sum(m.x[e,t] for e in m.conflict_edges[g])) * m.edge_admm[g,t,0]
    for i in m.nodes:
      objective += (m.lambda_values[i,t] + m.node_admm[i,t,1]) * m.p[i,t] + (1 - m.p[i,t]) * m.node_admm[i,t,0]
  return objective

def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, conflict_edges = ll.load_location(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  
  nodes = sorted(nodes)
  edges = sorted(edges)
  conflict_edges = sorted(conflict_edges)
  agents = sorted(agents)
  
  lambda_values = {(i,t): 0.0 for i in nodes for t in time_window}
  mu_values = {(g,t): 0.0 for g in range(1, len(conflict_edges)+1) for t in time_window}
  node_admm_values = {(a,i,t,z): 0.0 for a in agents for i in nodes for t in time_window for z in range(2)}
  edge_admm_values = {(a,g,t,z): 0.0 for a in agents for g in range(1, len(conflict_edges)+1) for t in time_window for z in range(2)}
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values

def create_model(agents, a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, rho):
  model = ConcreteModel()
  
  model.a = Param(initialize=a)
  model.rho = Param(initialize=rho)
  model.time_window = Set(initialize=time_window)
  model.nodes = Set(initialize=nodes)
  model.edges = Set(initialize=edges, dimen=2)
  
  model.conflict_groups = RangeSet(len(conflict_edges))
  model.conflict_edges = Set(model.conflict_groups, initialize=lambda m, g: conflict_edges[g-1], dimen=2)
  
  model.start_node = Param(initialize=start_nodes[a])
  model.arrival_time = Param(initialize=arrival_time[a])
  model.departures = Set(initialize=departures, dimen=3)
  model.train_type = Param(initialize=train_types[a])
  model.agents = Set(initialize=agents)

  model.x = Var(model.edges, model.time_window, domain=Binary)
  model.p = Var(model.nodes, model.time_window, domain=Binary)
  model.y = Var(model.time_window, domain=Binary)

  model.lambda_values = Param(model.nodes, model.time_window, mutable=True, initialize=lambda_values)
  model.mu_values = Param(model.conflict_groups, model.time_window, mutable=True, initialize=mu_values)
  model.node_admm = Param(model.nodes, model.time_window, range(2), mutable=True, initialize=0)
  model.edge_admm = Param(model.conflict_groups, model.time_window, range(2), mutable=True, initialize=0)
  
  # Objective
  model.cost = Objective(rule=objective_lagrangian, sense=minimize)

  # Constraint
  model.initial = Constraint(rule=c.inital_position_constraint)
  model.location = Constraint(model.time_window, rule=c.location_constraint)
  model.movement_departure = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_departure)
  model.movement_arrival = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_arrival)
  model.match_agent_destination = Constraint(rule=c.match_agent_destination)
  model.train_not_present = Constraint(model.departures, rule=c.train_not_present_constraint)
  model.train_presence_continuity = Constraint(model.time_window, rule=c.train_presence_continuity_constraint)
  
  return model

def solve_agent(a, m, nodes, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values):
  for t in time_window:  
    for l in nodes:
      m.lambda_values[l,t] = lambda_values[l,t]
      for z in range(2):
        m.node_admm[l,t,z] = node_admm_values[a,l,t,z]
    for g in m.conflict_groups:
      m.mu_values[g,t] = mu_values[g,t]
      for z in range(2):
        m.edge_admm[g,t,z] = edge_admm_values[a,g,t,z]
  # Solve
  solver = SolverFactory('gurobi')
  solver.options['Seed'] = 1
  solver.solve(m, warmstart=True, keepfiles=False)
  x_values = {(i,j): { t: m.x[(i,j),t].value for t in m.time_window} for (i,j) in m.edges}
  p_values = {l: { t: m.p[l,t].value for t in m.time_window} for l in m.nodes}
  y_values = {t: m.y[t].value for t in m.time_window}
  
  return x_values, p_values, y_values

def update_admm_values(agents, a, nodes, edges, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho):
  for t in time_window:
    for l in nodes:
      node_admm_values[a,l,t,0] = math.pow(max(0, rho/2*(0 + sum(p_values[a1][l][t] for a1 in agents if a1 != a) - 1)), 2)
      node_admm_values[a,l,t,1] = math.pow(max(0, rho/2*(1 + sum(p_values[a1][l][t] for a1 in agents if a1 != a) - 1)), 2)
    for g in range(1, len(conflict_edges)+1):
      edge_admm_values[a,g,t,0] = math.pow(max(0, rho/2*(0 + sum(x_values[a1][e][t] for a1 in agents if a1 != a for e in conflict_edges[g-1]) - 1)), 2)
      edge_admm_values[a,g,t,1] = math.pow(max(0, rho/2*(1 + sum(x_values[a1][e][t] for a1 in agents if a1 != a for e in conflict_edges[g-1]) - 1)), 2)
  return node_admm_values, edge_admm_values


def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out):
  n_iter = 100000
  solution_found = False
  models = {}
  conflict_list = []
  for a in agents:
    models[a] = create_model(agents, a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, rho)
  
  start = time.time()
  x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  y_values = {}
  for k in range(n_iter):
    print(k)
    
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(agents, a, nodes, edges, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho)
      x_values[a], p_values[a], y_values[a] = solve_agent(a, models[a], nodes, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values)
    #region print
    # if __name__ == "__main__":
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
    # for a in agents:
    #   for i in nodes:
    #     for t in time_window:
    #       if lambda_values[a,i,t] > 0:
    #         print(f"Lambda[{a},{i},{t}] = {lambda_values[a,i,t]}")
    # for (i,j) in edges:
    #   if j <= i:
    #     continue
    #   for t in time_window:
    #     if mu_values[i,j,t] > 0:
    #       print(f"Mu[{i},{j},{t}] = {mu_values[i,j,t]}")    
    # print("objective", obj)     
    #endregion
    
    conflicts = 0
    p_penalty = {(l, t): round(sum(p_values[a][l][t] for a in agents)) for l in nodes for t in time_window}
    x_penalty = {(g, t): round(sum(x_values[a][e][t] for a in agents for e in conflict_edges[g-1])) for g in range(1, len(conflict_edges)+1) for t in time_window}
    for l in nodes:
      for t in time_window:
        if p_penalty[l,t] > 1.0:
          print(f"p_penalty[{l},{t}] = {p_penalty[l,t]}")
    for t in time_window:
      for g in range(1, len(conflict_edges)+1):
        if x_penalty[g,t] > 1.0:
          print(f"Conflict group {conflict_edges[g-1]} at time {t} has penalty {x_penalty[g,t]}")
    for t in time_window:
      for l in nodes:
        penalty = 1/(k+1) * (p_penalty[l,t] - 1)
        if penalty > 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
      for g in range(1, len(conflict_edges)+1):
        penalty = 1/(k+1) * (x_penalty[g,t] - 1)
        if penalty > 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
      conflict_list.append((conflicts, time.time() - start))
    if __name__ == "__main__":
      print("conflicts", conflicts)
    if conflicts < 1:
      print("NO MORE CONFLICT")
      solution_found = True
      break
    if time.time() - start > time_out:
      print("TIME LIMIT REACHED")
      break
  if __name__ == "__main__":
    pass
    # Output
    # print("\np[a,n,t] values:")
    # for a in agents:
    #   for n in nodes:
    #     for t in time_window:
    #       val = p_values[a][n][t]
    #       if val is not None and val > 0:
    #         print(f"p[{a},{n},{t}] = {val}")
    # for a in agents:
    #   for i in nodes:
    #     for t in time_window:
    #       if lambda_values[a,i,t] > 0:
    #         print(f"Lambda[{a},{i},{t}] = {lambda_values[a,i,t]}")
    # print("x[a,(i,j),t] values:")
    # for a in agents:
    #   for (i,j) in edges:
    #     for t in time_window:
    #       val = x_values[a][(i,j)][t]
    #       if val is not None and val > 0:
    #         print(f"x[{a},{i}->{j},{t}] = {val}")
    # print("\np[a,n,t] values:")
    # for a in agents:
    #     for n in nodes:
    #         for t in time_window:
    #             val = p_values[a][n][t]
    #             if val is not None and val > 0:
    #                 print(f"p[{a},{n},{t}] = {val}")
  
  end_time = time.time()
  print("Total time (seconds):", end_time - start)
  print(k)
  p_values_filtered = []
  for agent in agents:
    for node in nodes:
      for t in time_window:
        if p_values[agent][node][t] == 1:
          p_values_filtered.append((agent, node, t))

  x_values_filtered = []
  for agent in agents:
    for edge in edges:
      i, j = edge
      for t in time_window:
        val = x_values[agent][edge][t]
        if val == 1:
          x_values_filtered.append((agent, i, j, t))
  return k, end_time - start, x_values_filtered, p_values_filtered, solution_found, conflict_list

if __name__ == "__main__":
  # location = 'locations/circle_location_small.json'
  # scenario = 'scenarios/circle/three_trains.json'
  # location = 'locations/five_tracks_location.json'
  # scenario = 'scenarios/five_tracks/three_trains_difficult.json'
  # location = 'locations/9_tracks_location.json'
  # scenario = 'scenarios/9_tracks/7_trains_matching.json'
  # location = 'locations/binckhorst.json'
  location = 'locations/location_solver.json'
  scenario = 'scenarios/binckhorst_matching_mixed_traffic_false/4_type/25_trains2.json'
  # scenario = 'scenarios/binckhorst_matching_mixed_traffic_false/4_type/30_trains1.json'
  
  # location = 'locations/6_tracks_location.json'
  # scenario = 'scenarios/6_tracks/5_trains_difficult.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/nine_trains_more_time.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/ten_trains_more_time.json'
  time_out = 600
  rho = 2
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = setup(location, scenario)
  print("ADMM_constraint_edges", scenario, rho)
  k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)
