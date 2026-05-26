from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, NonNegativeReals, value, RangeSet
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import constraints_lagrangian as c
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict

random.seed(1)

# Objective function for each train/agent
def objective_lagrangian(m):
  objective = 0
  for t in m.time_window:
    for e in m.edges:
      i, j = e
      if j <= i:
        continue
      objective += 0.01*(m.x[(i, j), t] + m.x[(j, i), t])
    for g in m.conflict_groups:
      used = sum(m.x[e,t] for e in m.conflict_edges[g])
      objective += (m.mu_values[g,t] + m.edge_admm[g,t,1]) * used + (1 - used) * m.edge_admm[g,t,0]
    for i in m.nodes:
      objective += (m.lambda_values[i,t] + m.node_admm[i,t,1]) * m.p[i,t] + (1 - m.p[i,t]) * m.node_admm[i,t,0]
  return objective

# Load all data and initalize penalty data structures
def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, conflict_edges = ll.load_location(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  
  nodes = sorted(nodes)
  edges = sorted(edges)
  agents = sorted(agents)
  # Add all non self edges to conflict edges such that no two trains can move at the same time
  conflict_edges = []
  all_conflcit_edges = []
  for edge in edges:
    i, j = edge
    if i != j:
      all_conflcit_edges.append(edge)
  conflict_edges.append(all_conflcit_edges)
  lambda_values = {(i,t): 0.0 for i in nodes for t in time_window}
  mu_values = {(g,t): 0.0 for g in range(1, len(conflict_edges)+1) for t in time_window}
  node_admm_values = {(a,i,t,z): 0.0 for a in agents for i in nodes for t in time_window for z in range(2)}
  edge_admm_values = {(a,g,t,z): 0.0 for a in agents for g in range(1, len(conflict_edges)+1) for t in time_window for z in range(2)}
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values

# Create pyomo model per agent
def create_model(a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, rho):
  model = ConcreteModel()
  
  # Input
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

  # Decision variables
  model.x = Var(model.edges, model.time_window, domain=Binary)
  model.p = Var(model.nodes, model.time_window, domain=Binary)
  model.y = Var(model.time_window, domain=Binary)

  # Penalties
  model.lambda_values = Param(model.nodes, model.time_window, mutable=True, initialize=lambda_values)
  model.mu_values = Param(model.conflict_groups, model.time_window, mutable=True, initialize=mu_values)
  model.node_admm = Param(model.nodes, model.time_window, range(2), mutable=True, initialize=0)
  model.edge_admm = Param(model.conflict_groups, model.time_window, range(2), mutable=True, initialize=0)
  
  # Objective
  model.cost = Objective(rule=objective_lagrangian, sense=minimize)

  # Constraints
  model.initial = Constraint(rule=c.inital_position_constraint)
  model.location = Constraint(model.time_window, rule=c.location_constraint)
  model.movement_departure = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_departure)
  model.movement_arrival = Constraint(model.nodes, model.time_window, rule=c.movement_constraint_arrival)
  model.match_agent_destination = Constraint(rule=c.match_agent_destination)
  model.train_not_present = Constraint(model.departures, rule=c.train_not_present_constraint)
  model.train_presence_continuity = Constraint(model.time_window, rule=c.train_presence_continuity_constraint)
  
  return model

# Update penalty values in the model for agent a and solve the model
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
  solver.options['Threads'] = 1
  solver.solve(m, warmstart=True, keepfiles=False)
  
  x_values = {(i,j): { t: m.x[(i,j),t].value for t in m.time_window} for (i,j) in m.edges}
  p_values = {l: { t: m.p[l,t].value for t in m.time_window} for l in m.nodes}
  y_values = {t: m.y[t].value for t in m.time_window}
  
  return x_values, p_values, y_values

# Update ADMM penalties for agent a, calculate values for p/x=1 and p/x=0
def update_admm_values(a, nodes, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho, p_sum, x_sum):
  rho_half = rho / 2
  for t in time_window:
    for l in nodes:
      others_p = p_sum[(l, t)] - p_values[a][l][t]
      p0 = max(0, others_p - 1)
      p1 = max(0, others_p)

      node_admm_values[a, l, t, 0] = rho_half * p0 * p0
      node_admm_values[a, l, t, 1] = rho_half * p1 * p1

    for g, edge_group in enumerate(conflict_edges, start=1):
      others_x = sum(x_sum[(e, t)] for e in edge_group) - sum(x_values[a][e][t] for e in edge_group)
      p0 = max(0, others_x - 1)
      p1 = max(0, others_x)

      edge_admm_values[a, g, t, 0] = rho_half * p0 * p0
      edge_admm_values[a, g, t, 1] = rho_half * p1 * p1
  return node_admm_values, edge_admm_values

# Main loop, initailize, solve and update penalties
def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out):
  n_iter = 100000
  solution_found = False
  models = {}
  conflict_list = []
  start = time.time()
  # Create model for each agent
  for a in agents:
    models[a] = create_model(a, nodes, edges, conflict_edges, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, rho)
  
  x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  y_values = {}
  # Each iteration solve for each agent and update penalties
  for k in range(n_iter):
    print(k)
    p_sum = {(l, t): sum((p_values[a1][l][t] or 0) for a1 in agents) for l in nodes for t in time_window}
    x_sum = {(e, t): sum((x_values[a1][e][t] or 0) for a1 in agents) for e in edges for t in time_window}
    # Solve for each agent and update admm penalties before solving
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(a, nodes, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho, p_sum, x_sum)
      old_p = {l: {t: p_values[a][l][t] for t in time_window} for l in nodes}
      old_x = {e: {t: x_values[a][e][t] for t in time_window} for e in edges}
      x_values[a], p_values[a], y_values[a] = solve_agent(a, models[a], nodes, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values)
      for l in nodes:
        for t in time_window:
          p_sum[(l, t)] += (p_values[a][l][t] or 0) - (old_p[l][t] or 0)
      for e in edges:
        for t in time_window:
          x_sum[(e, t)] += (x_values[a][e][t] or 0) - (old_x[e][t] or 0)
    # Update lagrangian penalties based and remaining conflicts
    conflicts = 0
    p_penalty = {(l, t): round(sum(p_values[a][l][t] for a in agents)) for l in nodes for t in time_window}
    x_penalty = {(g, t): round(sum(x_values[a][e][t] for a in agents for e in conflict_edges[g-1])) for g in range(1, len(conflict_edges)+1) for t in time_window}
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
    print("conflicts", conflicts)
    print(time.time() - start)
    if time.time() - start > time_out:
      print("TIME LIMIT REACHED")
      break
    if conflicts < 1:
      print("NO MORE CONFLICT")
      solution_found = True
      break
  end_time = time.time()
  print("Total time (seconds):", end_time - start)
  print(k)
  # Store solution
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
        if x_values[agent][edge][t] == 1:
          x_values_filtered.append((agent, i, j, t))
  return k, end_time - start, x_values_filtered, p_values_filtered, solution_found, conflict_list

if __name__ == "__main__":
  location = '../../data/locations/location_solver.json'
  scenario = '../../data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json'
  time_out = 1800
  rho = 0.5
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = setup(location, scenario)
  k, time, x_values_filtered, p_values_filtered, solution_found, conflict_list = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out)
