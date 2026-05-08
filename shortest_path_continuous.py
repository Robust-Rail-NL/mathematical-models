import rustworkx as rx
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict
import numpy as np

random.seed(1)

def node_index(node):
  return int(node.split("_")[1])

def build_equivalent_nodes(nodes):
  groups = defaultdict(list)
  for node in nodes:
    underscore_index = node.find("_")
    if underscore_index != -1:
      base = node[:underscore_index]
      groups[base].append(node)
  for values in groups.values():
    values.sort(key=lambda x: int(x.split("_")[1]))
  return dict(groups)

def build_macro_edges(edges, equivalent_nodes):
  # create lookup for which group a node belongs to and its index in that group
  node_to_group = {}
  group_index = {}
  for group_nodes in equivalent_nodes.values():
    for idx, node in enumerate(group_nodes):
      node_to_group[node] = group_nodes
      group_index[node] = idx
  expanded_edges = set(edges)
  # add edges between all nodes in the same group and edges to next group if 
  # there is an edge to one of the nodes in the group, also store occupied nodes for macro edges
  macro_edge_nodes = {}
  for u, v in edges:
    u_group = node_to_group.get(u)
    v_group = node_to_group.get(v)
    for uu in (u_group or (u,)):
      for vv in (v_group or (v,)):
        if uu == vv:
          continue
        expanded_edges.add((uu, vv))
        occupied = {vv}
        if u_group and v_group and u_group is v_group:
          u_idx = group_index[uu]
          v_idx = group_index[vv]
          if u_idx < v_idx:
            occupied.update(u_group[u_idx + 1:v_idx + 1])
          elif u_idx > v_idx:
            occupied.update(u_group[v_idx:u_idx])
        elif not u_group and v_group:
          v_idx = group_index[vv]
          occupied.update(v_group[:v_idx + 1])
        elif u_group and not v_group:
          u_idx = group_index[uu]
          occupied.update(u_group[:u_idx])
          
        macro_edge_nodes[(uu, vv)] = sorted(occupied)
  return expanded_edges, macro_edge_nodes
  
def setup(location, scenario):
  data = ll.load_json(location)
  nodes, edges, conflict_edges = ll.load_location(data)
  data = ll.load_json(scenario)
  agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
  time_window = range(start_time, end_time+1)
  
  # create dictionary of equivalent nodes based on naming convention and 
  # build macro edges between them. Also adds edges like 15 -> 1_2 if 15 -> 1_1 is an edge
  equivalent_nodes = build_equivalent_nodes(nodes)
  expanded_edges, macro_edge_nodes = build_macro_edges(edges, equivalent_nodes)
  
  edges = sorted(expanded_edges)
  nodes = sorted(nodes)
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
  return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes


def create_graph_per_agent(a, nodes, edges, start_node, arrival_time, departures, train_type, time_window):
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

def set_cost_per_agent_graph(g_a, a, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_info):
  for edge_idx, u_data, v_data in edge_info:
    if v_data == ("sink", "final"):
      g_a.update_edge_by_index(edge_idx, 0.0)
      continue

    u, t = u_data
    v, t_next = v_data
    base_cost = 0.0 if u == v else 0.01
    # node_cost = lambda_values[(v, t_next)] + node_admm_values[(a, v, t_next)]
    occupied_nodes = macro_edge_nodes.get((u, v), [v])
    node_cost = sum(lambda_values[(n, t_next)] + node_admm_values[(a, n, t_next)] for n in occupied_nodes)
    
    edge_cost = 0.0
    g = edge_to_group.get((u, v))
    if g is not None:
      edge_cost = mu_values[(g, t)] + edge_admm_values[(a, g, t)]

    g_a.update_edge_by_index(edge_idx, base_cost + node_cost + edge_cost)

  return g_a

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

def extract_path(a, path, macro_edge_nodes):
    x_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    p_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # initial occupancy
    start_node, start_t = path[0]
    if start_node != "sink":
        p_values[a][start_node][start_t] = 1

    for i in range(len(path) - 1):
        (u, t) = path[i]
        (v, t2) = path[i + 1]

        if u == "sink" or v == "sink":
            continue

        # edge usage
        x_values[a][(u, v)][t] = 1

        # occupancy AFTER movement
        occupied_nodes = macro_edge_nodes.get((u, v), [v])

        for n in occupied_nodes:
            p_values[a][n][t2] = 1

    return p_values, x_values

def debug_compare(a, path):
  print(f"================ AGENT {a} ================")
  print(" -> ".join(str(p) for p in path))

def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out, macro_edge_nodes):
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
  for a in agents:
    graphs[a], starts[a], sinks[a], edge_infos[a] = create_graph_per_agent(a, nodes, edges, start_nodes[a], arrival_time[a], departures, train_types[a], time_window)
  p_sum = {(l, t): 0 for l in nodes for t in time_window}
  x_sum = {(e, t): 0 for e in edges for t in time_window}
  for k in range(n_iter):
    print(k)
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(a, nodes, conflict_edges, time_window, x_values, p_values, node_admm_values, edge_admm_values, rho, x_sum, p_sum)
      graphs[a] = set_cost_per_agent_graph(graphs[a], a, lambda_values, mu_values, node_admm_values, edge_admm_values, edge_to_group, edge_infos[a])
      old_node = p_values[a]
      old_edge = x_values[a]
      
      sink_data = graphs[a][sinks[a]]
      path_indices = rx.astar_shortest_path(graphs[a], starts[a], lambda node: node == sink_data, edge_cost_fn=lambda x: x, estimate_cost_fn=lambda _: 0)
      path = [graphs[a][i] for i in path_indices]
      # debug_compare(a, path, node_admm_values, edge_admm_values)
      nv, ev = extract_path(a, path, macro_edge_nodes)
      p_values[a] = nv[a]
      x_values[a] = ev[a]
      # print(f"p_values for agent {a}:")
      # for n in nodes:
      #   for t in time_window:
      #     val = p_values[a][n][t]
      #     if val is not None and val > 0:
      #       print(f"p[{a},{n},{t}] = {val}")
      # print(f"x_values for agent {a}:")
      # for (i,j) in edges:
      #   for t in time_window:
      #     val = x_values[a][(i,j)][t]
      #     if val is not None and val > 0:
      #       print(f"x[{a},{i}->{j},{t}] = {val}")
      for t in time_window:
        for l in nodes:
          p_sum[(l, t)] += p_values[a][l][t] - old_node[l][t]
        for e in edges:
          x_sum[(e, t)] += x_values[a][e][t] - old_edge[e][t]
    conflicts = 0
    p_penalty = {(l, t): round(sum(p_values[a][l][t] for a in agents)) for l in nodes for t in time_window}
    x_penalty = {(g, t): round(sum(x_values[a][e][t] for a in agents for e in conflict_edges[g-1])) for g in range(1, len(conflict_edges)+1) for t in time_window}
    
    # print("\np[a,n,t] values:")
    # for a in agents:
    #   for n in nodes:
    #     for t in time_window:
    #       val = p_values[a][n][t]
    #       if val is not None and val > 0:
    #           print(f"p[{a},{n},{t}] = {val}")
    # print("x[a,(i,j),t] values:")
    # for a in agents:
    #   for (i,j) in edges:
    #     for t in time_window:
    #       val = x_values[a][(i,j)][t]
    #       if val is not None and val > 0:
    #         print(f"x[{a},{i}->{j},{t}] = {val}")
    # for l in nodes:
    #   for t in time_window:
    #     if p_penalty[l,t] > 1.0:
    #       for a in agents:
    #         if p_values[a][l][t] == 1:
    #           print(f"  Agent {a} occupies node {l} at time {t}")
    #       # print(f"p_penalty[{l},{t}] = {p_penalty[l,t]}")
    # for t in time_window:
    #   for g in range(1, len(conflict_edges)+1):
    #     if x_penalty[g,t] > 1.0:
    #       for a in agents: 
    #         for e in conflict_edges[g-1]:
    #           if x_values[a][e][t] == 1:
    #             print(f"  Agent {a} uses edge {e} at time {t}")
    for t in time_window:
      for l in nodes:
        penalty = 1/(k+1) * (p_penalty[l,t] - 1)
        if penalty > 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
          print(f"lambda_values[{l},{t}] = {lambda_values[l,t]}")
          conflicts += 1
        elif penalty < 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
      for g in range(1, len(conflict_edges)+1):
        penalty = 1/(k+1) * (x_penalty[g,t] - 1)
        if penalty > 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
          print(f"mu_values[{g},{t}] = {mu_values[g,t]}")
          conflicts += 1
        elif penalty < 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)

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
  # print("Total time (seconds):", end_time - start_time)
  # print(k)
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
  # for p_val in p_values_filtered:
  #   print(p_val)
  # print("x")
  # for x_val in x_values_filtered:
  #   print(x_val)
  return k, end_time - start_time, x_values_filtered, p_values_filtered, solution_found, conflict_list

if __name__ == "__main__":
  location = 'locations/four_tracks_location.json'
  scenario = 'scenarios/four_tracks/two_trains_simple.json'
  location = 'locations/location_solver.json'
  # scenario = 'data_types_360/scenarios_solver_types/scenario_solver_33_trains_33_units1.json'
  # scenario = 'data_time_20_old/scenarios_solver_time_20/scenario_solver_20_trains_5_units10_4800.json'
  scenario = 'data_types_120/scenarios_solver_types_120/scenario_solver_20_trains_20_units11.json'
  # scenario = 'scenarios_solver_milp/scenario_solver_5_trains_5_units1.json'
  # location = '/home/thomasverwaal/Robust-Rail-NL/mathematical-models/locations/location_solver.json'
  # scenario = '/home/thomasverwaal/Robust-Rail-NL/mathematical-models/data_time_20_old/scenarios_solver_time_20/scenario_solver_20_trains_5_units10_4800.json'
  # scenario = 'scenarios_solver_milp/scenario_solver_20_trains_5_units1.json'
  time_out = 1800
  rho = 0.5
  print(scenario)
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, macro_edge_nodes = setup(location, scenario)
  # print(nodes)
  # print(edges)
  k, time_total, x_values_filtered, p_values_filtered, solution_found, conflict_list = Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho=0.5, time_out=1800, macro_edge_nodes=macro_edge_nodes)