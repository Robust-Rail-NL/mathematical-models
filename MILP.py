from pyomo.environ import ConcreteModel, Set, Param, Var, Objective, Constraint, Binary, minimize, SolverFactory
from pyomo.opt import TerminationCondition, SolverStatus
import constraints as c
import load_location as ll
import load_scenario as ls
import time
import gurobipy as gp
from gurobipy import GRB

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
    nodes, edges, facilities = ll.load_location(data)
    data = ll.load_json(scenario)
    agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = ls.load_scenario(data)
    return nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types

def create_model(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window):
    model = ConcreteModel()

    # Sets
    model.agents = Set(initialize=agents)
    model.time_window = Set(initialize=time_window)
    model.nodes = Set(initialize=nodes)
    model.edges = Set(initialize=edges, dimen=2)
    model.start_nodes = Param(model.agents, initialize=start_nodes)
    model.arrival_time = Param(model.agents, initialize=arrival_time)
    model.departures = Set(initialize=departures, dimen=3)
    model.train_types = Param(model.agents, initialize=train_types)

    model.x = Var(model.agents, model.edges, model.time_window, domain=Binary)
    model.p = Var(model.agents, model.nodes, model.time_window, domain=Binary)
    model.y = Var(model.agents, model.time_window, domain=Binary)

    # Objective
    model.cost = Objective(rule=objective, sense=minimize)
    # for only feasible:
    # model.cost = Objective(expr=0.0, sense=minimize)

    # Constraint
    model.initial = Constraint(model.agents, rule=c.inital_position_constraint)
    model.location = Constraint(model.agents, model.time_window, rule=c.location_constraint)
    model.node_capacity = Constraint(model.nodes, model.time_window, rule=c.node_capacity_constraint)
    model.edge_capacity = Constraint(model.edges, model.time_window, rule=c.edge_capacity_constraint)
    model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_departure)
    model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=c.movement_constraint_arrival)
    model.match_agent_destination = Constraint(model.agents, rule=c.match_agent_destination)
    # model.train_presence = Constraint(model.agents, model.departures, rule=c.train_presence_constraint)
    model.train_not_present = Constraint(model.agents, model.departures, rule=c.train_not_present_constraint)
    model.train_presence_continuity = Constraint(model.agents, model.time_window, rule=c.train_presence_continuity_constraint)
    # model.no_movement_when_not_present = Constraint(model.agents, model.edges, model.time_window, rule=c.no_movement_when_not_present_constraint)
    return model

def solve(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types):
    time_window = range(start_time, end_time+1)
    model = create_model(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window)
    
    # # Solve using Gurobi
    # solver = SolverFactory('gurobi')
    solver = SolverFactory('gurobi_persistent')
    solver.set_instance(model)
    
    # def stop_after_first_solution(pyomo_model, solver_obj, where):
    #     grb_model = solver_obj._solver_model
    #     if where == GRB.Callback.MIPSOL:
    #         # Record first solution time
    #         if not hasattr(grb_model, "_first_solution_time"):
    #             grb_model._first_solution_time = grb_model.cbGet(GRB.Callback.RUNTIME)
    #         # Immediately terminate the solve
    #         grb_model.terminate()
    solver.set_gurobi_param('TimeLimit', 600)
    solver.set_callback(first_solution_callback)
    # solver.set_callback(stop_after_first_solution)

    start = time.time()
    result = solver.solve(model, tee=True, keepfiles=True)
    end = time.time()
    
    time_solution = 0.0
    grb_model = solver._solver_model
    if hasattr(grb_model, "_first_solution_time"):
        time_solution = grb_model._first_solution_time
    # if (result.solver.status != SolverStatus.ok or
    #     result.solver.termination_condition not in (
    #         TerminationCondition.optimal,
    #         TerminationCondition.feasible
    #     )):
    #     raise RuntimeError(
    #         f"No solution found. "
    #         f"Status: {result.solver.status}, "
    #         f"Termination: {result.solver.termination_condition}"
        # )
        
    # # Output
    # if __name__ == "__main__":
    #     print("x[a,(i,j),t] values:")
    #     for a in model.agents:
    #         for (i,j) in model.edges:
    #             for t in model.time_window:
    #                 val = model.x[a, (i,j), t].value
    #                 if val is not None and val > 0:
    #                     print(f"x[{a},{i}->{j},{t}] = {val}")
    #     print("\np[a,n,t] values:")
    #     for a in model.agents:
    #         for n in model.nodes:
    #             for t in model.time_window:
    #                 val = model.p[a, n, t].value
    #                 if val is not None and val > 0:
    #                     print(f"p[{a},{n},{t}] = {val}")
        # print("\ny[a,t] values:")
        # for a in model.agents:
        #     for t in model.time_window:
        #         val = model.y[a, t].value
        #         if val is not None and val > 0:
        #             print(f"y[{a},{t}] = {val}")                
    # print("Objective (cost):", model.cost())
    print("Time taken (seconds):", end - start)
    print("Time to first solution (seconds):", time_solution)
    return 0, end - start, time_solution
    
if __name__ == "__main__":
    # location = 'locations/five_tracks_location.json'
    # scenario = 'scenarios/five_tracks/two_trains_easiest.json'
    location = 'locations/binckhorst.json'
    # scenario = 'scenarios/binckhorst3/testing.json'
    scenario = 'scenarios/binckhorst_mixed_traffic_false/5_trains1.json'
    # location = 'locations/four_tracks_location.json'
    # scenario = 'scenarios/four_tracks/two_trains_simple.json'
    nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = setup(location, scenario)
    solve(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types)
    