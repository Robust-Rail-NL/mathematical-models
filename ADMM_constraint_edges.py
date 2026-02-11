from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value, RangeSet
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict

# random.seed(41)

def objective_lagrangian(m):
  objective = 0
  for t in m.time_window:
    for e in m.edges:
      i, j = e
      if j <= i:
        continue
      # objective += (1 + m.mu_values[i,j,t] + m.rho * m.edge_admm[i,j,t] - m.rho/2) * (m.x[(i, j), t] + m.x[(j, i), t])
      objective += m.x[(i, j), t] + m.x[(j, i), t]
    for g in m.conflict_groups:
      objective += (m.mu_values[g,t] + m.rho * m.edge_admm[g,t] - m.rho/2) * sum(m.x[e,t] for e in m.conflict_edges[g])
    for i in m.nodes:
      objective += (m.lambda_values[i,t] + m.rho * m.node_admm[i,t]) * m.p[i,t]
  return objective
# note: if 1*z - m.rho/2 = 0 the solver does not assign values to certain x causing errors
# note: 1*z has to be bigger than -m.rho/2 because other wise moving decreases the cost i think

def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, conflict_edges, facilities = ll.load_location(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  
  lambda_values = {(i,t): 0.0 for i in nodes for t in time_window}
  # mu_values = {(i,j,t): 0.0 for (i, j) in edges for t in time_window}
  mu_values = {(g,t): 0.0 for g in range(1, len(conflict_edges)+1) for t in time_window}
  node_admm_values = {(a,i,t): 0.0 for a in agents for i in nodes for t in time_window}
  # edge_admm_values = {(a,i,j,t): 0.0 for a in agents for (i, j) in edges for t in time_window}
  edge_admm_values = {(a,g,t): 0.0 for a in agents for g in range(1, len(conflict_edges)+1) for t in time_window}
  rho = 1.99
  # r = {(i,j,t): random.uniform(0.99,1.01) for (i, j) in edges for t in time_window}
  # cost = {(i,j,t): 1.0 for (i, j) in edges for t in time_window}
  r = 0
  cost = 0
    
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho

def create_model(agents, a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, r, cost, rho):
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
  model.node_admm = Param(model.nodes, model.time_window, mutable=True, initialize=0)
  model.edge_admm = Param(model.conflict_groups, model.time_window, mutable=True, initialize=0)
  model.r = Param(model.edges, model.time_window, mutable=True, initialize=r)
  model.c = Param(model.edges, model.time_window, mutable=True, initialize=cost)
  # model.multiplyer = Param(initialize=0.01, mutable=True)
  
  # Objective
  model.cost = Objective(rule=objective_lagrangian, sense=minimize)

  # Constraint
  model.initial = Constraint(rule=c.inital_position_constraint)
  model.location = Constraint(model.time_window, rule=c.location_constraint)
  model.movement_departure = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_departure)
  model.movement_arrival = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_arrival)
  model.match_agent_destination = Constraint(rule=c.match_agent_destination)
  # model.train_presence = Constraint(model.departures, rule=c.train_presence_constraint)
  model.train_not_present = Constraint(model.departures, rule=c.train_not_present_constraint)
  model.train_presence_continuity = Constraint(model.time_window, rule=c.train_presence_continuity_constraint)
  
  return model

def solve_agent(k, a, m, nodes, edges, conflict_edges, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, cost):
  for t in time_window:  
    for l in nodes:
      m.lambda_values[l,t] = lambda_values[l,t]
      m.node_admm[l,t] = node_admm_values[a,l,t]
    # for i,j in edges:
    #   # m.r[(i,j),t] = random.uniform(0.9,1.1)
    #   # m.c[(i,j),t] = cost[i,j,t]
    #   if i < j:
    #     m.mu_values[i,j,t] = mu_values[i,j,t]
    #     m.edge_admm[i,j,t] = edge_admm_values[a,i,j,t]
    for g in m.conflict_groups:
      m.mu_values[g,t] = mu_values[g,t]
      m.edge_admm[g,t] = edge_admm_values[a,g,t]
  # if k%100 == 0 and k > 0:
  #   m.multiplyer = m.multiplyer.value/10
  # Solve
  solver = SolverFactory('gurobi')
  solver.solve(m, warmstart=True, keepfiles=False)
  x_values = {(i,j): { t: m.x[(i,j),t].value for t in m.time_window} for (i,j) in m.edges}
  p_values = {l: { t: m.p[l,t].value for t in m.time_window} for l in m.nodes}
  y_values = {t: m.y[t].value for t in m.time_window}
  objective_value = m.cost
  
  return x_values, p_values, y_values, value(objective_value)

#TODO optimize?
#TODO compare += vs = in update_admm_values on a lot of instances
#TODO compare 1/k+1 vs rho in penalty update on a lot of instances
#TODO compare 0.26 vs 0.5 on a lot of instances
def update_admm_values(agents, a, nodes, edges, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values):
  # for a1 in agents:
  #   if a == a1:
  #     continue
  #   for t in time_window:
  #     for l in nodes:
  #       node_admm_values[a,l,t] += p_values[a1][l][t]
  #     for (i,j) in edges:
  #       if i < j:
  #         edge_admm_values[a,i,j,t] += x_values[a1][(i,j)][t] + x_values[a1][(j,i)][t]
  # return node_admm_values, edge_admm_values
  for t in time_window:
    for l in nodes:
      node_admm_values[a,l,t] = sum(p_values[a1][l][t] for a1 in agents if a1 != a)
    # for (i,j) in edges:
    #   if i < j:
    #     edge_admm_values[a,i,j,t] = sum(x_values[a1][(i,j)][t] + x_values[a1][(j,i)][t] for a1 in agents if a1 != a)
    for g in range(1, len(conflict_edges)+1):
      edge_admm_values[a,g,t] = sum(x_values[a1][e][t] for a1 in agents if a1 != a for e in conflict_edges[g-1])
  return node_admm_values, edge_admm_values


def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho):
  n_iter = 50
  objectives = []
  models = {}
  obj = 0
  for a in agents:
    models[a] = create_model(agents, a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, r, cost, rho)
  start = time.time()
  x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  y_values = {}
  objective_values = {}
  for k in range(n_iter):
    # if __name__ == "__main__":
    print(k)
    
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(agents, a, nodes, edges, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values)
      x_values[a], p_values[a], y_values[a], objective_values[a]= solve_agent(k, a, models[a], nodes, edges, conflict_edges, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, cost)
      # print("objective value agent", a, ":", objective_values[a])
      # print("x[a,(i,j),t] values:")
      # for (i,j) in edges:
      #   for t in time_window:
      #     val = x_values[a][(i,j)][t]
      #     if val is not None and val > 0:
      #       print(f"x[{a},{i}->{j},{t}] = {val}")
      # print("\np[a,n,t] values:")
      # for n in nodes:
      #   for t in time_window:
      #     val = p_values[a][n][t]
      #     if val is not None and val > 0:
      #         print(f"p[{a},{n},{t}] = {val}")
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
    # obj = 0
    # for a in agents:
      # print("Objective agent", a, ":", objective_values[a])
      # obj += objective_values[a]
    # print("Sum of agent objectives:", obj)
    # obj -= sum(lambda_values['0',i,t] for i in nodes for t in time_window)
    # obj -= sum(mu_values['0',i,j,t] for (i,j) in edges for t in time_window)
    # obj += rho/2 * sum((node_admm_values[a,i,t]-1)**2 for a in agents for i in nodes for t in time_window)
    # obj += rho/2 * sum((edge_admm_values[a,i,j,t]-1)**2 for a in agents for (i,j) in edges for t in time_window)
    # print("Lagrangian Objective:", obj)
    # objectives.append(obj)
    
    conflicts = 0
    p_penalty = {(l, t): sum(p_values[a][l][t] for a in agents) for l in nodes for t in time_window}
    # x_penalty = {(i, j, t): sum(x_values[a][(i, j)][t] + x_values[a][(j, i)][t] for a in agents)
                #  for (i, j) in edges if i < j for t in time_window}
    x_penalty = {(g, t): sum(x_values[a][e][t] for a in agents for e in conflict_edges[g-1]) for g in range(1, len(conflict_edges)+1) for t in time_window}
    for l in nodes:
      for t in time_window:
        if p_penalty[l,t] > 1.0 and l == '15':
          print(f"p_penalty[{l},{t}] = {p_penalty[l,t]}")
    # for (i,j) in edges:
    #   if j <= i:
    #     continue
    #   for t in time_window:
    #     if x_penalty[i,j,t] > 1.0:
    #       print(f"x_penalty[{i},{j},{t}] = {x_penalty[i,j,t]}")
    # for a in agents:
    #   # print(f"node_admm_values[{a}] = {node_admm_values[a,'15','106']}")
    #   # print(f"node_admm_values[{a}] = {node_admm_values[a,'15','108']}")
    #   for i in nodes:
    #     for t in time_window:
    #       if node_admm_values[a,i,t] > 0 and i == '15':
    #         print(f"node_admm_values[{a},{i},{t}] = {node_admm_values[a,i,t]}")
    # for a in agents:
    for t in time_window:
      for l in nodes:
        # penalty = 1/(math.sqrt(k+1)) * (sum(p_values[a][l][t] for a in agents) - 1)
        penalty = 1/(k+1) * (p_penalty[l,t] - 1)
        # penalty = rho * (p_penalty[l,t] - 1)
        if penalty > 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
      # for (i,j) in edges:
      #   if j <= i:
      #     continue
      #   # penalty = 1/(math.sqrt(k+1)) * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
      #   penalty = 1/(k+1) * (x_penalty[i,j,t] - 1)
      #   # penalty = rho * (x_penalty[i,j,t] - 1)
      #   if penalty > 0:
      #     mu_values[i,j,t] = max(0.0, mu_values[i,j,t] + penalty)
      #     conflicts += 1
      #   elif penalty < 0:
      #     mu_values[i,j,t] = max(0.0, mu_values[i,j,t] + penalty)
      for g in range(1, len(conflict_edges)+1):
        penalty = 1/(k+1) * (x_penalty[g,t] - 1)
        if penalty > 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
    
    if __name__ == "__main__":
      if k%10 == 0:
        print("conflicts", conflicts)

      # if conflicts <= 2:
      #   print("x[a,(i,j),t] values:")
      #   for a in agents:
      #     for (i,j) in edges:
      #       for t in time_window:
      #         val = x_values[a][(i,j)][t]
      #         if val is not None and val > 0:
      #           print(f"x[{a},{i}->{j},{t}] = {val}")
      #   print("\np[a,n,t] values:")
      #   for a in agents:
      #     for n in nodes:
      #       for t in time_window:
      #         val = p_values[a][n][t]
      #         if val is not None and val > 0:
      #             print(f"p[{a},{n},{t}] = {val}")
      #   for i in nodes:
      #     for t in time_window:
      #       if lambda_values[i,t] > 0:
      #         print(f"Lambda[{i},{t}] = {lambda_values[i,t]}")
      #   print("\nmu[i,j,t] values:")
      #   for (i,j) in edges:
      #     if j <= i:
      #       continue
      #     for t in time_window:
      #       if mu_values[i,j,t] > 0:
      #         print(f"Mu[{i},{j},{t}] = {mu_values[i,j,t]}")              
      #   print("conflicts", conflicts)
    if conflicts < 1:
      print("NO MORE CONFLICT")
      break

  end_time = time.time()
  if __name__ == "__main__":
    # Output
    print("\np[a,n,t] values:")
    for a in agents:
      for n in nodes:
        for t in time_window:
          val = p_values[a][n][t]
          if val is not None and val > 0:
              print(f"p[{a},{n},{t}] = {val}")
    # for a in agents:
    #   for i in nodes:
    #     for t in time_window:
    #       if lambda_values[a,i,t] > 0:
    #         print(f"Lambda[{a},{i},{t}] = {lambda_values[a,i,t]}")
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
    # print("", objective_values)
    print("objectives:", objectives)
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

  # print(x_values_filtered)
  # print(p_values_filtered)
  
  return k, end_time - start, x_values_filtered, p_values_filtered

if __name__ == "__main__":
  # location = 'locations/circle_location_small.json'
  # scenario = 'scenarios/circle/three_trains.json'
  # location = 'locations/five_tracks_location.json'
  # scenario = 'scenarios/five_tracks/two_trains_easiest.json'
  location = 'locations/binckhorst.json'
  # scenario = '../robust-rail-solver/ServiceSiteScheduling/database/TUSS-Instance-Generator/scenario_settings/setting_A/scenario_solver.json'
  # scenario = 'scenarios/binckhorst3/20_trains.json'
  scenario = 'scenarios/binckhorst_matching_mixed_traffic_false/4_type/5_trains1.json'
  # location = 'locations/6_tracks_location.json'
  # scenario = 'scenarios/6_tracks/5_trains_difficult.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/nine_trains_more_time.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/ten_trains_more_time.json'
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho = setup(location, scenario)
  k, time, x_values_filtered, p_values_filtered = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho)
  