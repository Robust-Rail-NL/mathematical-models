from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeIntegers, SolverFactory, minimize, Set, Binary, Param

def inital_position_constraint(m, a):
  return m.p[a,m.start_nodes[a],0] == 1

def location_constraint(m, a, t):
  return sum(m.p[a,i,t] for i in m.nodes) == 1

def node_capacity_constraint(m, i, t):
  return sum(m.p[a,i,t] for a in m.agents) <= 1

def edge_capacity_constraint(m, i, j, t):
  if j <= i:
    return Constraint.Skip
  return sum(m.x[a, (i,j), t] + m.x[a, (j,i), t] for a in m.agents) <= 1

def movement_constraint_departure(m, a, i, t):
  if t == max(m.time_window):
    return Constraint.Skip
  return (m.p[a,i,t] == sum(m.x[a,(i,j),t] for j in m.nodes if (i,j) in m.edges))

def movement_constraint_arrival(m, a, i, t):
  if t == max(m.time_window):
    return Constraint.Skip
  return (m.p[a,i,t+1] == sum(m.x[a,(h,i),t] for h in m.nodes if (h,i) in m.edges))

def destination_reached_constraint(m, a):
  return m.p[a,m.destination_nodes[a],max(m.time_window)] == 1