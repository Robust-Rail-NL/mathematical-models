import rustworkx as rx
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict
import numpy as np

random.seed(1)

# This code has been sped up compared to shortest_path.py

# Load all data and initalize penalty data structures
def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, conflict_edges, expanded_edges, macro_edge_nodes = ll.load_location_sp_continuous(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  edges = sorted(set(expanded_edges))
  nodes = sorted(nodes)
  agents = sorted(agents)
  node_to_idx = {n:i for i,n in enumerate(nodes)}
  edge_to_idx = {e:i for i,e in enumerate(edges)}
  agent_to_idx = {a:i for i,a in enumerate(agents)}
  # Add all non self edges to conflict edges such that no two trains can move at the same time
  conflict_edges = []
  all_conflict_edges = []
  for edge in edges:
    i, j = edge
    if i != j:
      all_conflict_edges.append(edge)
  conflict_edges.append(all_conflict_edges)
  T = len(time_window)
  N = len(nodes)
  E = len(edges)
  A = len(agents)
  G = len(conflict_edges)

  lambda_values = np.zeros((N, T), dtype=np.float64)
  mu_values = np.zeros((G, T), dtype=np.float64)

  node_admm_values = np.zeros((A, N, T), dtype=np.float64)
  edge_admm_values = np.zeros((A, G, T), dtype=np.float64)
  edge_group_matrix = np.zeros((G, E), dtype=np.float64)
  for g, group in enumerate(conflict_edges):
    for e in group:
      edge_group_matrix[g, edge_to_idx[e]] = 1
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes, node_to_idx, edge_to_idx, agent_to_idx, edge_group_matrix

# Create the yard as graph for each agent
def create_graph_per_agent(nodes, edges, start_node, arrival_time, departures, train_type, time_window):
  g = rx.PyDiGraph()
  graph_nodes = {}

  for t in time_window:
    for n in nodes:
      graph_nodes[(n, t)] = g.add_node((n, t))

  sink = g.add_node(("sink", "final"))

  for t in time_window[:-1]:
    for (u, v) in edges:
      if u != v:
        g.add_edge(graph_nodes[(u, t)], graph_nodes[(v, t + 1)], 0.01)
      else:
        g.add_edge(graph_nodes[(u, t)], graph_nodes[(v, t + 1)], 0.0)

  start = graph_nodes[(start_node, arrival_time)]
  # Connect valid departures to sink
  for departure in departures:
    n, type, t = departure
    if type == train_type:
      g.add_edge(graph_nodes[(n, t)], sink, 0)
  
  edge_info = []
  for edge_idx in g.edge_indices():
    u_idx, v_idx = g.get_edge_endpoints_by_index(edge_idx)
    u_data = g[u_idx]
    v_data = g[v_idx]
    edge_info.append((edge_idx, u_data, v_data))
  return g, start, sink, edge_info

# Set the edge cost for each agent graph
def set_cost_per_agent_graph(g_a, a_idx, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_info, node_to_idx, macro_edge_nodes):
  for edge_idx, u_data, v_data in edge_info:

    if v_data == ("sink", "final"):
      g_a.update_edge_by_index(edge_idx, 0.0)
      continue

    u, t = u_data
    v, t_next = v_data

    base_cost = 0.0 if u == v else 0.01

    occupied_nodes = macro_edge_nodes.get((u, v), [v])

    node_cost = 0.0
    for n in occupied_nodes:
      n_idx = node_to_idx[n]
      node_cost += (lambda_values[n_idx, t_next] + node_admm_values[a_idx, n_idx, t_next])
    
    edge_cost = 0.0
    g = edge_to_group.get((u, v))
    if g is not None:
      g_idx = g - 1
      edge_cost = (mu_values[g_idx, t] + edge_admm_values[a_idx, g_idx, t])
    g_a.update_edge_by_index(edge_idx, base_cost + node_cost + edge_cost)

  return g_a

# Update the admm penalty values for agent a
def update_admm_values(a_idx, x_values, p_values, node_admm_values, edge_admm_values, rho, x_sum, p_sum, edge_group_matrix):
  rho_half = rho / 2

  others_p = p_sum - p_values[a_idx]
  node_admm_values[a_idx] = rho_half * np.maximum(0, others_p) ** 2
  
  others_x = x_sum - x_values[a_idx]
  group_totals = edge_group_matrix @ others_x
  edge_admm_values[a_idx] = rho_half * np.maximum(0, group_totals) ** 2
  return node_admm_values, edge_admm_values

# Extract the path found for agent a
def extract_path(a_idx, path, p_values, x_values, node_to_idx, edge_to_idx, macro_edge_nodes):
  p_values[a_idx, :, :] = 0
  x_values[a_idx, :, :] = 0

  # initial occupancy
  start_node, start_t = path[0]
  start_node_idx = node_to_idx[start_node]

  p_values[a_idx, start_node_idx, start_t] = 1

  for i in range(len(path) - 1):
    (u, t) = path[i]
    (v, t2) = path[i + 1]
    if u == "sink" or v == "sink":
      continue
    # edge usage
    edge_idx = edge_to_idx[(u, v)]
    x_values[a_idx, edge_idx, t] = 1
    # occupancy during/after movement
    occupied_nodes = macro_edge_nodes.get((u, v), [v])

    for n in occupied_nodes:
      node_idx = node_to_idx[n]
      p_values[a_idx, node_idx, t2] = 1

  return p_values, x_values

# Main loop, initailize, solve and update penalties
def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out, macro_edge_nodes, node_to_idx, edge_to_idx, agent_to_idx, edge_group_matrix):
  n_iter = 1000000
  solution_found = False
  
  graphs = {}
  starts = {}
  sinks = {}
  
  conflict_list = []
  
  start_time = time.time()
  
  T = len(time_window)
  N = len(nodes)
  E = len(edges)
  A = len(agents)

  p_values = np.zeros((A, N, T), dtype=np.int8)
  x_values = np.zeros((A, E, T), dtype=np.int8)
  edge_to_group = {}
  for g, group in enumerate(conflict_edges, start=1):
    for e in group:
      edge_to_group[e] = g
  
  edge_infos = {}
  # Create and store graph for each agent
  for a in agents:
    graphs[a], starts[a], sinks[a], edge_infos[a] = create_graph_per_agent(nodes, edges, start_nodes[a], arrival_time[a], departures, train_types[a], time_window)
  p_sum = p_values.sum(axis=0)
  x_sum = x_values.sum(axis=0)
  for k in range(n_iter):
    print(k)
    # Solve for each agent and update admm penalties before solving
    for a_idx, a in enumerate(agents):
      node_admm_values, edge_admm_values = update_admm_values(a_idx, x_values, p_values, node_admm_values, edge_admm_values, rho, x_sum, p_sum, edge_group_matrix)
      graphs[a] = set_cost_per_agent_graph(graphs[a], a_idx, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_infos[a], node_to_idx, macro_edge_nodes)
      old_node = p_values[a_idx].copy()
      old_edge = x_values[a_idx].copy()
      
      sink_data = graphs[a][sinks[a]]
      
      path_indices = rx.astar_shortest_path(graphs[a], starts[a], lambda node: node == sink_data, edge_cost_fn=lambda x: x, estimate_cost_fn=lambda _: 0)
      path = [graphs[a][i] for i in path_indices]
      p_values, x_values = extract_path(a_idx, path, p_values, x_values, node_to_idx, edge_to_idx, macro_edge_nodes)
      p_sum += p_values[a_idx] - old_node
      x_sum += x_values[a_idx] - old_edge
    # Update lagrangian penalties based and remaining conflicts
    conflicts = 0
    p_penalty = p_values.sum(axis=0)
    lambda_values += (1/(k+1)) * (p_penalty - 1)
    np.maximum(lambda_values, 0, out=lambda_values)
    group_penalty = edge_group_matrix @ x_sum
    mu_values += (1/(k+1)) * (group_penalty - 1)
    np.maximum(mu_values, 0, out=mu_values)
    conflicts = np.sum(p_penalty > 1) + np.sum(group_penalty > 1)
    conflict_list.append((conflicts, time.time() - start_time))
    print("conflicts", conflicts)
    print(time.time() - start_time)
    if time.time() - start_time > time_out:
      print("TIME LIMIT REACHED")
      break
    if conflicts < 1:
      print("NO MORE CONFLICT")
      solution_found = True
      break
  end_time = time.time()
  # Store solution
  p_values_filtered = []
  for a_idx, agent in enumerate(agents):
    for node in nodes:
      node_idx = node_to_idx[node]
      for t in time_window:
        if p_values[a_idx, node_idx, t] == 1:
          p_values_filtered.append((agent, node, t))
  x_values_filtered = []
  for a_idx, agent in enumerate(agents):
    for edge in edges:
      i, j = edge
      edge_idx = edge_to_idx[edge]
      for t in time_window:
        if x_values[a_idx, edge_idx, t] == 1:
          x_values_filtered.append((agent, i, j, t))
  return k, end_time - start_time, x_values_filtered, p_values_filtered, solution_found, conflict_list

if __name__ == "__main__":
  location = '../data/locations/location_solver.json'
  # scenario = '../data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json'
  scenario = '../../scenario-planning-inputs/Location_KleineBinckhorst/scenarios/20_trains1.json'
  scenario = '../../scenario-planning-inputs/Location_KleineBinckhorst/scenarios_solver/scenario_solver_25_trains_5_units4_3420.json'
  time_out = 1800
  rho = 0.5
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes, node_to_idx, edge_to_idx, agent_to_idx, edge_group_matrix = setup(location, scenario)
  k, time_total, x_values_filtered, p_values_filtered, solution_found, conflict_list = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho=0.5, time_out=1800, macro_edge_nodes=macro_edge_nodes, node_to_idx=node_to_idx, edge_to_idx=edge_to_idx, agent_to_idx=agent_to_idx, edge_group_matrix=edge_group_matrix) 
