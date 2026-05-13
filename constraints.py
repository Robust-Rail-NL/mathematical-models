from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeIntegers, SolverFactory, minimize, Set, Binary, Param

def inital_position_constraint(m, a):
  return m.p[a,m.start_nodes[a],m.arrival_time[a]] == 1

def location_constraint(m, a, t):
  if t < m.arrival_time[a]:
    return sum(m.p[a,i,t] for i in m.nodes) == 0
  return sum(m.p[a,i,t] for i in m.nodes) == m.y[a,t]

def location_constraint_time(m, a, t):
  if t < m.arrival_time[a]:
    return sum(m.p[a,i,t] for i in m.nodes) == 0
  x = sum(m.x[a,i,j,s] for (i,j) in m.edges if i !=j for s in range(max(0, t - m.traversal_time_edges[i,j] + 1), t))
  return sum(m.p[a,i,t] for i in m.nodes) + x == m.y[a,t]

def node_capacity_constraint(m, i, t):
  return sum(m.p[a,i,t] for a in m.agents) <= 1

def edge_capacity_constraint_group(m, g, t):
  return sum(m.x[a, e, t] for a in m.agents for e in m.conflict_edges[g]) <= 1

def movement_constraint_departure(m, a, i, t):
  if t == max(m.time_window) or t < m.arrival_time[a]:
    return Constraint.Skip
  return (m.p[a,i,t] - m.y[a,t] + m.y[a,t+1] <= sum(m.x[a,(i,j),t] for j in m.nodes if (i,j) in m.edges))

def movement_constraint_arrival(m, a, i, t):
  if t == max(m.time_window) or t < m.arrival_time[a]:
    return Constraint.Skip
  return (m.p[a,i,t+1] == sum(m.x[a,(h,i),t] for h in m.nodes if (h,i) in m.edges))

def match_agent_destination(m,a):
  total = 0
  for l,ty,t in m.departures:
    if ty == m.train_types[a]:
      total += m.p[a,l,t]
  return total == 1

def train_presence_constraint(m,a,l,ty,t):
  return m.p[a,l,t] <= m.y[a,t]

def train_not_present_constraint(m,a,l,ty,t):
  if t >= max(m.time_window) or ty != m.train_types[a]:
    return Constraint.Skip
  return m.y[a,t+1] <= 1 - m.p[a,l,t]

def train_presence_continuity_constraint(m,a,t):
  if t >= max(m.time_window):
    return Constraint.Skip
  return m.y[a,t+1] <= m.y[a,t]