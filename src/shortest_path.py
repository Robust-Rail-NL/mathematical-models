from networkx import edges

import rustworkx as rx
import load_location as ll
import load_scenario as ls
import random
import time
from collections import defaultdict
import os
import argparse

parser = argparse.ArgumentParser("ALR with Shortest Path")
parser.add_argument("-r", "--random-seed", help="An integer random seed (default=42).", type=int, default=42, required=False)
parser.add_argument("-l", "--location", help="The name of the location file (default folder is data/location unless specified otherwise). Default=location_solver.json.", type=str, default="location_solver.json", required=False)
parser.add_argument("-s", "--scenario", help="The path to the scenario file. Default='data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json'.", type=str, default="data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json", required=False)
parser.add_argument("-t", "--timeout", help="Timeout (integer) in seconds. (default=1800)", type=int, default=1800, required=False)
parser.add_argument("-p", "--rho", help="Rho (float between 0 and 1). (default=0.5)", type=float, default=0.5, required=False)

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
  node_admm_values = {(a,i,t): 0.0 for a in agents for i in nodes for t in time_window}
  edge_admm_values = {(a,g,t): 0.0 for a in agents for g in range(1, len(conflict_edges)+1) for t in time_window}
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values

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
def set_cost_per_agent_graph(g_a, a, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_info):
  for edge_idx, u_data, v_data in edge_info:
    if v_data == ("sink", "final"):
      g_a.update_edge_by_index(edge_idx, 0.0)
      continue

    u, t = u_data
    v, t_next = v_data
    base_cost = 0.0 if u == v else 0.01
    node_cost = lambda_values[(v, t_next)] + node_admm_values[(a, v, t_next)]
    edge_cost = 0.0
    g = edge_to_group.get((u, v))
    if g is not None:
      edge_cost = mu_values[(g, t)] + edge_admm_values[(a, g, t)]

    g_a.update_edge_by_index(edge_idx, base_cost + node_cost + edge_cost)

  return g_a

# Update the admm penalty values for agent a
def update_admm_values(a, nodes, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho, x_sum, p_sum):
  rho_half = rho / 2

  for t in time_window:
    for l in nodes:
      others_p = p_sum[(l, t)] - p_values[a][l][t]
      p1 = max(0, others_p)
      node_admm_values[(a, l, t)] = rho_half * p1 * p1

    for g, edge_group in enumerate(conflict_edges, start=1):
      total = 0
      own = 0
      for e in edge_group:
        total += x_sum[(e, t)]
        own += x_values[a][e][t]

      others_x = total - own
      p1 = max(0, others_x)
      edge_admm_values[(a, g, t)] = rho_half * p1 * p1
  return node_admm_values, edge_admm_values

# Extract the path found for agent a
def extract_path(a, path):
  x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  for node, t in path:
    p_values[a][node][t] = 1
  for i in range(len(path) - 1):
    (u, t1) = path[i]
    (v, t2) = path[i + 1]
    if u == "sink" or v == "sink":
      continue

    x_values[a][(u, v)][t1] = 1

  return p_values, x_values

# Main loop, initailize, solve and update penalties
def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out):
  n_iter = 1000000
  solution_found = False
  
  graphs = {}
  starts = {}
  sinks = {}
  
  conflict_list = []
  
  start_time = time.time()
  
  p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

  edge_to_group = {}
  for g, group in enumerate(conflict_edges, start=1):
    for e in group:
      edge_to_group[e] = g
  
  edge_infos = {}
  # Create and store graph for each agent
  for a in agents:
    graphs[a], starts[a], sinks[a], edge_infos[a] = create_graph_per_agent(nodes, edges, start_nodes[a], arrival_time[a], departures, train_types[a], time_window)
  p_sum = {(l, t): 0 for l in nodes for t in time_window}
  x_sum = {(e, t): 0 for e in edges for t in time_window}
  # Each iteration solve for each agent and update penalties
  for k in range(n_iter):
    print("iteration", k)
    # Solve for each agent and update admm penalties before solving
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(a, nodes, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho, x_sum, p_sum)
      graphs[a] = set_cost_per_agent_graph(graphs[a], a, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_infos[a])
      old_node = p_values[a]
      old_edge = x_values[a]
      
      sink_data = graphs[a][sinks[a]]
      path_indices = rx.astar_shortest_path(graphs[a], starts[a], lambda node: node == sink_data, edge_cost_fn=lambda x: x, estimate_cost_fn=lambda _: 0)
      path = [graphs[a][i] for i in path_indices]
      nv, ev = extract_path(a, path)
      p_values[a] = nv[a]
      x_values[a] = ev[a]
      for t in time_window:
        for l in nodes:
          p_sum[(l, t)] += p_values[a][l][t] - old_node[l][t]
        for e in edges:
          x_sum[(e, t)] += x_values[a][e][t] - old_edge[e][t]
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
    conflict_list.append((conflicts, time.time() - start_time))
    print("conflicts", conflicts)
    print("time", time.time() - start_time)
    if time.time() - start_time > time_out:
      print("TIME LIMIT REACHED")
      break
    if conflicts < 1:
      print("NO MORE CONFLICT")
      solution_found = True
      break
  end_time = time.time()
  print("Total time (seconds):", end_time - start_time)
  print("final iteration", k)
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
  return k, end_time - start_time, x_values_filtered, p_values_filtered, solution_found, conflict_list

if __name__ == "__main__":
  args = parser.parse_args()
  random.seed(args.random_seed)
  time_out = args.timeout
  rho = args.rho
  location = args.location
  if not os.path.isfile(location):
    location = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "locations", location)
    if not os.path.isfile(location):
      print(f"ERROR: could not find location {location}")
      exit(1)
  print("Loaded location", location)
  scenario = args.scenario
  if not os.path.isfile(scenario):
    if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", scenario)):
      scenario = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", scenario)
    else:
      print(f"ERROR: could not find scenario {scenario}")
      exit(1)
  print("Loaded scenario", scenario)
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = setup(location, scenario)
  k, time_total, x_values_filtered, p_values_filtered, solution_found, conflict_list = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho=0.5, time_out=1800)