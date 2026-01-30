from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time
import math

# random.seed(41)

def objective_lagrangian(m):
  # MILP_objective = sum(m.c[(i,j),t]*m.r[(i,j),t]*m.x[(i, j), t] for t in m.time_window
  #           for (i, j) in m.edges if i != j)
  # MILP_objective = sum(m.r[(i,j),t]*m.x[(i, j), t] for t in m.time_window
            # for (i, j) in m.edges if i != j)
  MILP_objective = sum(m.x[(i, j), t] for t in m.time_window
            for (i, j) in m.edges if i != j)
  # MILP_objective *= m.multiplyer
  node_capacity_penalty = 0
  node_admm_penalty = 0
  for i in m.nodes:
    for t in m.time_window:
      node_capacity_penalty += m.lambda_values[m.a,i,t] * m.p[i,t] 
      node_admm_penalty += (m.rho * m.node_admm[i,t] - m.rho/2) * m.p[i,t]
  edge_capacity_penalty = 0
  edge_admm_penalty = 0
  for e in m.edges:
    i, j = e
    if j <= i:
      continue
    for t in m.time_window:
      edge_capacity_penalty += m.mu_values[m.a,i,j,t] * (m.x[(i,j),t] + m.x[(j,i),t])
      edge_admm_penalty += (m.rho * m.edge_admm[i,j,t] - m.rho/2) * (m.x[(i,j),t] + m.x[(j,i),t])
  return MILP_objective + node_capacity_penalty + edge_capacity_penalty + node_admm_penalty + edge_admm_penalty

def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, facilities = ll.load_location(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  
  lambda_values = {(a,i,t): 0.0 for a in agents for i in nodes for t in time_window}
  mu_values = {(a,i,j,t): 0.0 for a in agents for (i, j) in edges for t in time_window}
  node_admm_values = {(a,i,t): 0.0 for a in agents for i in nodes for t in time_window}
  edge_admm_values = {(a,i,j,t): 0.0 for a in agents for (i, j) in edges for t in time_window}
  rho = 0.5
  r = {(i,j,t): random.uniform(0.99,1.01) for (i, j) in edges for t in time_window}
  cost = {(i,j,t): 1.0 for (i, j) in edges for t in time_window} 
    
  return nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho

def create_model(agents, a, nodes, edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho):
  model = ConcreteModel()
  
  model.a = Param(initialize=a)
  model.rho = Param(initialize=rho)
  
  model.time_window = Set(initialize=time_window)
  model.nodes = Set(initialize=nodes)
  model.edges = Set(initialize=edges, dimen=2)
  model.start_node = Param(initialize=start_nodes[a])
  model.arrival_time = Param(initialize=arrival_time[a])
  model.departures = Set(initialize=departures, dimen=3)
  model.train_type = Param(initialize=train_types[a])
  model.agents = Set(initialize=agents)

  model.x = Var(model.edges, model.time_window, domain=Binary)
  model.p = Var(model.nodes, model.time_window, domain=Binary)
  model.y = Var(model.time_window, domain=Binary)

  model.lambda_values = Param(model.agents, model.nodes, model.time_window, mutable=True, initialize=lambda_values)
  model.mu_values = Param(model.agents, model.edges, model.time_window, mutable=True, initialize=mu_values)
  model.node_admm = Param(model.nodes, model.time_window, mutable=True, initialize=0)
  model.edge_admm = Param(model.edges, model.time_window, mutable=True, initialize=0)
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

def solve_agent(k, a, m, nodes, edges, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, cost):
  for t in time_window:  
    for l in nodes:
      m.lambda_values[a,l,t] = lambda_values[a,l,t]
      m.node_admm[l,t] = node_admm_values[a,l,t]
    for i,j in edges:
      # m.r[(i,j),t] = random.uniform(0.9,1.1)
      # m.c[(i,j),t] = cost[i,j,t]
      if i < j:
        m.mu_values[a,i,j,t] = mu_values[a,i,j,t]
        m.edge_admm[i,j,t] = edge_admm_values[a,i,j,t]
  # if k%100 == 0 and k > 0:
  #   m.multiplyer = m.multiplyer.value/10
  # Solve
  solver = SolverFactory('gurobi')
  solver.solve(m, warmstart=True, keepfiles=False)
  x_values = {(i,j): { t: (m.x[(i,j),t].value) for t in m.time_window} for (i,j) in m.edges}
  p_values = {l: { t: (m.p[l,t].value) for t in m.time_window} for l in m.nodes}
  y_values = {t: (m.y[t].value) for t in m.time_window}
  objective_value = m.cost
  
  return x_values, p_values, y_values, value(objective_value)

def update_admm_values(agents, a, nodes, edges, time_window, x_values, p_values, node_admm_values, edge_admm_values):
  # print(a)
  for a1 in agents:
    if a == a1:
      continue
    for t in time_window:
      for l in nodes:
        node_admm_values[a,l,t] += p_values[a1][l][t]
        # node_admm_values[a,l,t] += p_values[a1,l,t]
      for (i,j) in edges:
        if i < j:
          edge_admm_values[a,i,j,t] += x_values[a1][(i,j)][t] + x_values[a1][(j,i)][t]
        
  return node_admm_values, edge_admm_values


def Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho):
  n_iter = 1000
  objectives = []
  models = {}
  obj = 0
  n_agents = len(agents)
  for a in agents:
    models[a] = create_model(agents, a, nodes, edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho)
  
  # p_values = {(a,l,t): 0.0 for a in agents for l in nodes for t in time_window}
  # x_values = {(a,(i,j),t): 0.0 for a in agents for (i,j) in edges for t in time_window}
  # y_values = {(a,t): 0.0 for a in agents for t in time_window}
  # objective_values = {a: 0.0 for a in agents}
  # print(p_values)
  # x_values, p_values, y_values, objective_values = {}, {}, {}, {}
  # # for a in agents:
  # #   p_values[a] = {}
  # #   x_values[a] = {}
  # #   for n in nodes:
  # #     p_values[a][n] = {}
  # #     for t in time_window:
  # #       print("a,n,t", a, n, t)
  # #       p_values[a][n][t] = 0
  # #   for (i, j) in edges:
  # #     x_values[a][(i,j)] = {}
  # #     for t in time_window:
  # #       x_values[a][(i,j)][t] = 0
  # # print(p_values)
  # # print(p_values['33333', '1', 0])
  start = time.time()
  for k in range(n_iter):
    x_values, p_values, y_values, objective_values = {}, {}, {}, {}
    for a in agents:
      p_values[a] = {}
      x_values[a] = {}
      for n in nodes:
        p_values[a][n] = {}
        for t in time_window:
          p_values[a][n][t] = 0
      for (i, j) in edges:
        x_values[a][(i,j)] = {}
        x_values[a][(j,i)] = {}
        for t in time_window:
          x_values[a][(i,j)][t] = 0
          x_values[a][(j,i)][t] = 0
    if __name__ == "__main__":
      print(k)
    
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(agents, a, nodes, edges, time_window, x_values, p_values, node_admm_values, edge_admm_values)
      x_values[a], p_values[a], y_values[a], objective_values[a]= solve_agent(k,a, models[a], nodes, edges, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, cost)
    #region print
    # if __name__ == "__main__":
      # print("x[a,(i,j),t] values:")
      # for a in agents:
      #     for (i,j) in edges:
      #         for t in time_window:
      #             val = x_values[a][(i,j)][t]
      #             if val is not None and val > 0:
      #                 print(f"x[{a},{i}->{j},{t}] = {val}")
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
    obj = 0
    for a in agents:
      obj += objective_values[a]
    # obj -= sum(lambda_values[a,l,t] for l in nodes for t in time_window) - sum(mu_values[i,j,t] for i,j in edges for t in time_window)
    objectives.append(obj)   
    
    conflicts = 0
    for a in agents:
      for l in nodes:
        for t in time_window:
          # penalty = 1/(math.sqrt(k+1)) * (sum(p_values[a][l][t] for a in agents) - 1)
          # penalty = 1/(k+1) * (sum(p_values[a][l][t] for a in agents) - 1)
          penalty = rho * (sum(p_values[a][l][t] for a in agents) - 1)
          if penalty > 0:
            lambda_values[a,l,t] = max(0.0, lambda_values[a,l,t] + penalty)
            conflicts += 1
          elif penalty < 0:
            lambda_values[a,l,t] = max(0.0, lambda_values[a,l,t] + penalty)

    for a in agents:
      for (i,j) in edges:
        if j <= i:
          continue
        for t in time_window:
          # penalty = 1/(math.sqrt(k+1)) * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
          # penalty = 1/(k+1) * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
          penalty = rho * (sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents) - 1)
          if penalty > 0:
            mu_values[a,i,j,t] = max(0.0, mu_values[a,i,j,t] + penalty)
            conflicts += 1
          elif penalty < 0:
            mu_values[a,i,j,t] = max(0.0, mu_values[a,i,j,t] + penalty)
    
    # for (i,j) in edges:
    #   if i == j:
    #     continue
    #   for t in time_window:
    #     penalty = sum(x_values[a][(i,j)][t] + x_values[a][(j,i)][t] for a in agents)
    #     if penalty == 0:
    #       cost[i,j,t] = max(0, cost[i,j,t] - random.uniform(0.09, 0.11))
    #     elif penalty > 1:
    #       cost[i,j,t] += random.uniform(0.09,0.11)
    #     else:
    #       cost[i,j,t] += random.uniform(0.09,0.11)
    
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
    print(objectives)
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
    print("conflicts:", conflicts)
    print("nodes:", nodes)
    print("edges:", edges)
    print("agents:", agents)
    print("start_nodes:", start_nodes)
    print("arrival_time:", arrival_time)
    print("departures:", departures)
    print("time_window:", time_window)
    print("train_types:", train_types)
    print("", objective_values)
  print("Total time (seconds):", end_time - start)
  print(k)
  return k, end_time - start

if __name__ == "__main__":
  # location = 'locations/six_tracks_location.json'
  # scenario = 'scenarios/six_tracks/four_trains.json'
  location = 'locations/binckhorst.json'
  # scenario = '../robust-rail-solver/ServiceSiteScheduling/database/TUSS-Instance-Generator/scenario_settings/setting_A/scenario_solver.json'
  scenario = 'scenarios/binckhorst3/20_trains.json'
  # location = 'locations/6_tracks_location.json'
  # scenario = 'scenarios/6_tracks/5_trains_difficult.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/nine_trains_more_time.json'
  # location = 'locations/ten_tracks_location.json'
  # scenario = 'scenarios/ten_tracks/ten_trains_more_time.json'
  nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho = setup(location, scenario)
  k, time = Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho)
  