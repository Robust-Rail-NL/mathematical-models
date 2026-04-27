import rustworkx as rx
import load_location as ll
import load_scenario as ls
import random
import time
import math
from collections import defaultdict

random.seed(42)

def check_graph_consistency(g, nodes, edges):
  # --- extract base nodes from graph ---
  graph_nodes = {n for (n, t) in g.nodes()}

  setup_nodes = set(nodes)

  print("NODE CHECK")
  print("Missing in graph:", setup_nodes - graph_nodes)
  print("Extra in graph:", graph_nodes - setup_nodes)
  print()

  # --- extract base edges from graph (ignore time) ---
  graph_edges = set()

  for u_idx, v_idx in g.edge_list():
      u_node, _ = g[u_idx]
      v_node, _ = g[v_idx]
      graph_edges.add((u_node, v_node))

  setup_edges = set(edges) | {(v, u) for (u, v) in edges}  # because you added both directions

  print("EDGE CHECK")
  print("Missing in graph:", setup_edges - graph_edges)
  print("Extra in graph:", graph_edges - setup_edges)
  print()

  # --- optional strict assertions ---
  assert setup_nodes == graph_nodes, "Node mismatch!"
  assert setup_edges == graph_edges, "Edge mismatch!"

  print("Graph matches setup perfectly")
  return

def create_base_graph(nodes, edges, time_window):
  g = rx.PyDiGraph()
  graph_nodes = {}
  for t in time_window:
    for n in nodes:
      graph_nodes[(n, t)] = g.add_node((n, t))
  for t in time_window[:-1]:
    for (u, v) in edges:
      g.add_edge(graph_nodes[(u, t)], graph_nodes[(v, t + 1)], 0.01)
  return g


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


def create_graph_per_agent(a, start_node, arrival_time, departures, train_type, time_window):
  g = rx.PyDiGraph()
  graph_nodes = {}

  # Create time-expanded nodes
  for t in time_window:
    for n in nodes:
      graph_nodes[(n, t)] = g.add_node((n, t))

  # Create single global sink
  sink = g.add_node(("sink", "final"))

  # Movement edges
  for t in time_window[:-1]:
    for (u, v) in edges:
      if u != v:
        g.add_edge(graph_nodes[(u, t)], graph_nodes[(v, t + 1)], 0.01)
      else:
        g.add_edge(graph_nodes[(u, t)], graph_nodes[(v, t + 1)], 0.0)

  # Start node
  start = graph_nodes[(start_node, arrival_time)]

  # Connect valid departures to sink
  for departure in departures:
    n, type, t = departure
    if type == train_type:
      g.add_edge(graph_nodes[(n, t)], sink, 0)
        
  # node_idx = graph_nodes[('1',3)]
  # for succ in g.successor_indices(node_idx):
  #     print(g[node_idx], "->", g[succ], "cost:", g.get_edge_data(node_idx, succ))
  return g, start, sink
  
def set_cost_per_agent_graph(g_a, a, lambda_values, mu_values, node_admm_values, edge_admm_values, conflict_edges):
  edge_to_group = {}

  for g, group in enumerate(conflict_edges, start=1):
    # print(f"Conflict group {g}: {group}")
    for e in group:
      # print(f"  Edge {e} belongs to group {g}")
      edge_to_group[e] = g

  for edge_idx in g_a.edge_indices():
    u_idx, v_idx = g_a.get_edge_endpoints_by_index(edge_idx)
    u_data = g_a[u_idx]
    v_data = g_a[v_idx]

    if v_data == ("sink", "final"):
      g_a.update_edge_by_index(edge_idx, 0.0)
      continue

    u, t = u_data
    v, t_next = v_data

    base_cost = 0.0 if u == v else 0.01

    node_cost = (
      lambda_values[(v, t_next)]
      + node_admm_values[(a, v, t_next)]
    )

    edge_cost = 0.0
    if (u, v) in edge_to_group:
      g = edge_to_group[(u, v)]
      edge_cost = (
        mu_values[(g, t)]
        + edge_admm_values[(a, g, t)]
      )

    total_cost = base_cost + node_cost + edge_cost
    g_a.update_edge_by_index(edge_idx, total_cost)
  return g_a

def update_admm_values(a, nodes, conflict_edges, time_window, edge_values, node_values, node_admm_values, edge_admm_values, rho, edge_sum, node_sum):
  rho_half = rho / 2

  for t in time_window:
    for l in nodes:
      others_p = node_sum[(l, t)] - node_values[a][l][t]
      p1 = max(0, others_p)
      node_admm_values[(a, l, t)] = rho_half * p1 * p1

    for g, edge_group in enumerate(conflict_edges, start=1):
      others_x = (sum(edge_sum[(e, t)] for e in edge_group) - sum(edge_values[a][e][t] for e in edge_group))
      p1 = max(0, others_x)
      edge_admm_values[(a, g, t)] = rho_half * p1 * p1
  # print(f"\n[Updated ADMM NODE VALUES for agent {a}]")
  # for (agent, l, t), val in node_admm_values.items():
  #     if agent == a and val != 0:
  #         print(f"node_admm[{l},{t}] = {val}")
  # print(f"\n[Updated ADMM EDGE VALUES for agent {a}]")
  # for (agent, g_id, t), val in edge_admm_values.items():
  #     if agent == a and val != 0:
  #         print(f"edge_admm[group {g_id}, t={t}] = {val}")
  return node_admm_values, edge_admm_values

def debug_compare(a, path, node_values, edge_values):
  print(f"\n================ AGENT {a} ================")

  # ---- PATH ----
  print("\n[Dijkstra path]")
  print(" -> ".join(str(p) for p in path))

  # ---- NODE VALUES ----
  # print("\n[Node values]")
  # for node, t in path:
  #   if node != "sink":
  #     val = node_values[a][node][t]
  #     print(f"{node}@{t} = {val}")

  # # ---- EDGE VALUES ----
  # print("\n[Edge values]")
  # for i in range(len(path) - 1):
  #   (u, t1) = path[i]
  #   (v, t2) = path[i + 1]

  #   if u != "sink" and v != "sink":
  #     val = edge_values[a][(u, v)][t1]
  #     print(f"{u}->{v}@{t1} = {val}")



def extract_from_path(a, path, nodes, edges, time_window):
  edge_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  node_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

  # mark node usage
  for node, t in path:
    node_values[a][node][t] = 1

  # mark edge usage from consecutive pairs
  for i in range(len(path) - 1):
    (u, t1) = path[i]
    (v, t2) = path[i + 1]

    # ignore sink transitions if needed
    if u == "sink" or v == "sink":
      continue

    edge_values[a][(u, v)][t1] = 1

  return node_values, edge_values

def Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho, time_out):
  n_iter = 100
  solution_found = False
  
  graphs = {}
  starts = {}
  sinks = {}
  
  conflict_list = []
  
  start_time = time.time()
  
  node_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  edge_values = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
  
  for a in agents:
    graphs[a], starts[a], sinks[a] = create_graph_per_agent(a, start_nodes[a], arrival_time[a], departures, train_types[a], time_window)
  for k in range(n_iter):
    print(k)
    
    node_sum = {(l, t): sum(node_values[a1][l][t] for a1 in agents) for l in nodes for t in time_window}
    edge_sum = {(e, t): sum(edge_values[a1][e][t] for a1 in agents) for e in edges for t in time_window}
    for a in agents:
      node_admm_values, edge_admm_values = update_admm_values(a, nodes, conflict_edges, time_window, edge_values, node_values, node_admm_values, edge_admm_values, rho, edge_sum, node_sum)
      graphs[a] = set_cost_per_agent_graph(graphs[a], a, lambda_values, mu_values, node_admm_values, edge_admm_values, conflict_edges)
      old_node = {l: {t: node_values[a][l][t] for t in time_window} for l in nodes}
      old_edge = {e: {t: edge_values[a][e][t] for t in time_window} for e in edges}
      
      sink_data = graphs[a][sinks[a]]
      path_indices = rx.astar_shortest_path(graphs[a], starts[a], lambda node: node == sink_data, edge_cost_fn=lambda x: x, estimate_cost_fn=lambda _: 0)
      path = [graphs[a][i] for i in path_indices]
      nv, ev = extract_from_path(a, path, nodes, edges, time_window)
      node_values[a] = nv[a]
      edge_values[a] = ev[a]
      for l in nodes:
        for t in time_window:
          node_sum[(l, t)] += (node_values[a][l][t] or 0) - (old_node[l][t] or 0)
      for e in edges:
        for t in time_window:
          edge_sum[(e, t)] += (edge_values[a][e][t] or 0) - (old_edge[e][t] or 0)
      # debug_compare(a, path, node_values, edge_values)
      # total_cost = 0
      # for i in range(len(path) - 1):
      #   u_data = path[i]
      #   v_data = path[i + 1]

      #   # find edge weight in graph
      #   u_idx = graphs[a].nodes().index(u_data)
      #   v_idx = graphs[a].nodes().index(v_data)

      #   edge_idx = graphs[a].edge_indices_from_endpoints(u_idx, v_idx)[0]
      #   weight = graphs[a].get_edge_data_by_index(edge_idx)

      #   total_cost += weight

      # print(f"\n[Total path cost]")
      # print(total_cost)
    conflicts = 0
    p_penalty = {(l, t): round(sum(node_values[a][l][t] for a in agents)) for l in nodes for t in time_window}
    x_penalty = {(g, t): round(sum(edge_values[a][e][t] for a in agents for e in conflict_edges[g-1])) for g in range(1, len(conflict_edges)+1) for t in time_window}
    for l in nodes:
      for t in time_window:
        if p_penalty[l,t] > 1.0:
          print(f"p_penalty[{l},{t}] = {p_penalty[l,t]}")
    for t in time_window:
      for g in range(1, len(conflict_edges)+1):
        if x_penalty[g,t] > 1.0:
          # print(f"Conflict group {conflict_edges[g-1]} at time {t} has penalty {x_penalty[g,t]}")
          for a in agents: 
            for e in conflict_edges[g-1]:
              if edge_values[a][e][t] == 1:
                print(f"  Agent {a} uses edge {e} at time {t}")
    for t in time_window:
      for l in nodes:
        penalty = 1/(k+1) * (p_penalty[l,t] - 1)
        if penalty > 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          lambda_values[l,t] = max(0.0, lambda_values[l,t] + penalty/2)
      for g in range(1, len(conflict_edges)+1):
        penalty = 1/(k+1) * (x_penalty[g,t] - 1)
        if penalty > 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty)
          conflicts += 1
        elif penalty < 0:
          mu_values[g,t] = max(0.0, mu_values[g,t] + penalty/2)
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
if __name__ == "__main__":
  location = 'locations/five_tracks_location.json'
  scenario = 'scenarios/five_tracks/three_trains_difficult.json'
  location = 'locations/location_solver.json'
  scenario = 'data_types_360/scenarios_solver_types/scenario_solver_33_trains_1_units22.json'
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values = setup(location, scenario)
  print(nodes)
  print(edges)
  Lagrangian(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, rho=1.0, time_out=1800)
