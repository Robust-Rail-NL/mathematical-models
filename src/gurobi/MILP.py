from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory, RangeSet
from pyomo.opt import TerminationCondition, SolverStatus
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import constraints_milp as c
import load_location as ll
import load_scenario as ls
import time
from gurobipy import GRB
import random
import os
import argparse

parser = argparse.ArgumentParser("MILP with Gurobi")
parser.add_argument("-r", "--random-seed", help="An integer random seed (default=42).", type=int, default=42, required=False)
parser.add_argument("-l", "--location", help="The name of the location file (default folder is data/location unless specified otherwise). Default=location_solver.json.", type=str, default="location_solver.json", required=False)
parser.add_argument("-s", "--scenario", help="The path to the scenario file. Default='data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json'.", type=str, default="data/data_types_7hours/scenarios_solver/scenario_solver_25_trains_1_units30.json", required=False)
parser.add_argument("-t", "--timeout", help="Timeout (integer) in seconds. (default=1800)", type=int, default=1800, required=False)

def objective(m):
  return sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
    for (i, j) in m.edges if i != j)

def first_solution_callback(pyomo_model, solver, where):
  if where == GRB.Callback.MIPSOL:
    grb_model = solver._solver_model
    if not hasattr(grb_model, "_first_solution_time"):
      grb_model._first_solution_time = grb_model.cbGet(GRB.Callback.RUNTIME)

def setup(location, scenario):
	data = ll.load_json(location)
	nodes, edges, conflict_edges = ll.load_location(data)
	data = ll.load_json(scenario)
	agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
	# Add all non self edges to conflict edges such that no two trains can move at the same time
	conflict_edges = []
	all_conflcit_edges = []
	for edge in edges:
		i, j = edge
		if i != j:
			all_conflcit_edges.append(edge)
	conflict_edges.append(all_conflcit_edges)
	return nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types

def create_model(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window):
    model = ConcreteModel()
    
    model.agents = Set(initialize=agents)
    model.time_window = Set(initialize=time_window)
    model.nodes = Set(initialize=nodes)
    model.edges = Set(initialize=edges, dimen=2)
    
    model.conflict_groups = RangeSet(len(conflict_edges))
    model.conflict_edges = Set(model.conflict_groups, initialize=lambda m, g: conflict_edges[g-1], dimen=2)
    
    model.start_nodes = Param(model.agents, initialize=start_nodes)
    model.arrival_time = Param(model.agents, initialize=arrival_time)
    model.departures = Set(initialize=departures, dimen=3)
    model.train_types = Param(model.agents, initialize=train_types)

    model.x = Var(model.agents, model.edges, model.time_window, domain=Binary)
    model.p = Var(model.agents, model.nodes, model.time_window, domain=Binary)
    model.y = Var(model.agents, model.time_window, domain=Binary)

    ## Objective
    model.cost = Objective(rule=objective, sense=minimize)
    ## For only feasibility
    # model.cost = Objective(expr=0.0, sense=minimize)

    ## Constraints
    model.initial = Constraint(model.agents, rule=c.inital_position_constraint)
    model.location = Constraint(model.agents, model.time_window, rule=c.location_constraint)
    model.node_capacity = Constraint(model.nodes, model.time_window, rule=c.node_capacity_constraint)
    model.edge_capacity = Constraint(model.conflict_groups, model.time_window, rule=c.edge_capacity_constraint_group)
    model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_departure)
    model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_arrival)
    model.match_agent_destination = Constraint(model.agents, rule=c.match_agent_destination)
    model.train_not_present = Constraint(model.agents, model.departures, rule=c.train_not_present_constraint)
    model.train_presence_continuity = Constraint(model.agents, model.time_window, rule=c.train_presence_continuity_constraint)
    return model

def solve(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_out):
	time_window = range(start_time, end_time+1)
	start = time.time()
	model = create_model(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window)
	
	# Solve using Gurobi
	solver = SolverFactory('gurobi_persistent')
	solver.options['Seed'] = 1
	solver.set_instance(model)	
   
	solver.set_gurobi_param('TimeLimit', time_out)
	solver.set_callback(first_solution_callback)
	result = solver.solve(model, tee=True, keepfiles=True)
	end = time.time()
	
	solution_found = (result.solver.status == SolverStatus.ok and
    result.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible])
 
	time_first_solution = 0.0
	grb_model = solver._solver_model
	if hasattr(grb_model, "_first_solution_time"):
			time_first_solution = grb_model._first_solution_time
	
	print("Time taken (seconds):", end - start)
	print("Time to first solution (seconds):", time_first_solution)
	p_values_filtered = []
	for a in model.agents:
		for n in model.nodes:
			for t in model.time_window:
				val = model.p[a, n, t].value
				if val is not None and val > 0:
					p_values_filtered.append((a,n,t))
	x_values_filtered = []
	for a in model.agents:
		for (i,j) in model.edges:
			for t in model.time_window:
				val = model.x[a, (i,j), t].value
				if val is not None and val > 0:
					x_values_filtered.append((a, i, j, t))
	return 0, end - start, x_values_filtered, p_values_filtered, time_first_solution - start, solution_found
    
if __name__ == "__main__":
  args = parser.parse_args()
  random.seed(args.random_seed)
  time_out = args.timeout
  location = args.location
  if not os.path.isfile(location):
    location = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "locations", location)
    if not os.path.isfile(location):
      print(f"ERROR: could not find location {location}")
      exit(1)
  print("Loaded location", location)
  scenario = args.scenario
  if not os.path.isfile(scenario):
    if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", scenario)):
      scenario = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", scenario)
    else:
      print(f"ERROR: could not find scenario {scenario}")
      exit(1)
  print("Loaded scenario", scenario)
  nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = setup(location, scenario)
  k, time, x_values_filtered, p_values_filtered, time_first_solution, solution_found = solve(nodes, edges, conflict_edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_out)
