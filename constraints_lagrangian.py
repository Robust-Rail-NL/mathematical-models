from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeIntegers, SolverFactory, minimize, Set, Binary, Param

def inital_position_constraint(m):
  return m.p[m.start_node,m.arrival_time] == 1

def location_constraint(m, t):
  if t < m.arrival_time:# or t >= m.departure_time[a]:
    return sum(m.p[i,t] for i in m.nodes) == 0
  return sum(m.p[i,t] for i in m.nodes) == m.y[t]

def movement_constraint_departure(m, i, t):
  if t == max(m.time_window)+1 or t < m.arrival_time:# or t >= m.departure_time[a]:
    return Constraint.Skip
  return (m.p[i,t] == sum(m.x[(i,j),t] for j in m.nodes if (i,j) in m.edges))

def movement_constraint_arrival(m, i, t):
  if t == max(m.time_window) or t < m.arrival_time:# or t >= m.departure_time[a]:
    return Constraint.Skip
  return (m.y[t] - m.y[t+1] + m.p[i,t+1] >= sum(m.x[(h,i),t] for h in m.nodes if (h,i) in m.edges))

# def destination_reached_constraint(m, a):
#   return m.p[a,m.destination_nodes[a],m.departure_time[a]] == 1

def match_agent_destination(m):
  return sum(m.p[l,t] for l,ty,t in m.departures if ty == m.train_type.value) == 1

def train_presence_constraint(m,l,ty,t):
  return m.p[l,t] <= m.y[t]

def train_not_present_constraint(m,l,ty,t):
  if t >= max(m.time_window):
    return Constraint.Skip
  return m.y[t+1] <= 1 - m.p[l,t]

def train_presence_continuity_constraint(m,t):
  if t >= max(m.time_window):
    return Constraint.Skip
  return m.y[t+1] <= m.y[t]

# def no_movement_when_not_present_constraint(m,a,i,j,t):
#   if j <= i:
#     return Constraint.Skip
#   return m.x[a,(i,j),t] <= m.y[a,t]