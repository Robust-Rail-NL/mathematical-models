from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeIntegers, SolverFactory, minimize, Set, Binary, Param

def objective(m):
  return sum(m.x[a, (i, j), t] for a in m.agents for t in m.time_window
            for (i, j) in m.edges if i != j)
  
def inital_position_constraint(m, a):
  return m.p[a,m.start_nodes[a],0] == 1

def location_constraint(m, a, t):
  return sum(m.p[a,l,t] for l in m.nodes) == 1

def node_capacity_constraint(m, l, t):
  return sum(m.p[a,l,t] for a in m.agents) <= 1

def edge_capacity_constraint(m, i, j, t):
  if i == j:
    return Constraint.Skip
  return sum(m.x[a,(i,j),t] for a in m.agents) + sum(m.x[a,(j,i),t] for a in m.agents) <= 1

def movement_constraint_departure(m, a, i, t):
  if t == max(m.time_window):
    return Constraint.Skip
  return (m.p[a,i,t] == sum(m.x[a,(i,j),t] for j in m.nodes if (i,j) in m.edges))

def movement_constraint_arrival(m, a, i, t):
  if t == max(m.time_window):
    return Constraint.Skip
  return (m.p[a,i,t+1] == sum(m.x[a,(h,i),t] for h in m.nodes if (h,i) in m.edges))

def destination_reached_constraint(m, a):
  print("Destination constraint for agent", a)
  print("Destination node:", m.destination_nodes[a])
  return m.p[a,m.destination_nodes[a],max(m.time_window)] == 1


agents = [1,2]
t_max = 4
time_window = range(0, t_max)
nodes = [1, 2, 3, 4, 5]
edges = [(1, 3), (3, 1), (2, 3), (3, 2), (3, 4), (4, 3), (3, 5), (5, 3),
         (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
start_nodes = [1,2]
destination_nodes = [5,4]

model = ConcreteModel()

# Sets
model.agents = Set(initialize=agents)
model.time_window = Set(initialize=time_window)
model.nodes = Set(initialize=nodes)
model.edges = Set(initialize=edges, dimen=2)
model.start_nodes = Param(model.agents, initialize={1:1,2:2})
model.destination_nodes = Param(model.agents, initialize={1:3,2:3})

model.x = Var(model.agents, model.edges, model.time_window, domain=Binary)
model.p = Var(model.agents, model.nodes, model.time_window, domain=Binary)

# Objective
model.cost = Objective(rule=objective, sense=minimize)


# Constraint
model.initial = Constraint(model.agents, rule=inital_position_constraint)
model.location = Constraint(model.agents, model.time_window, rule=location_constraint)
model.node_capacity = Constraint(model.nodes, model.time_window, rule=node_capacity_constraint)
model.edge_capacity = Constraint(model.edges, model.time_window, rule=edge_capacity_constraint)
model.movement_departure = Constraint(model.agents, model.nodes, model.time_window, rule=movement_constraint_departure)
model.movement_arrival = Constraint(model.agents, model.nodes, model.time_window, rule=movement_constraint_arrival)
model.destination_reached = Constraint(model.agents, rule=destination_reached_constraint)


# # Solve using Gurobi
solver = SolverFactory('gurobi')
result = solver.solve(model, tee=True, keepfiles=True)
solver_model = model  # Pyomo model
solver_model.write("model.lp")  # Export model to LP
model.solutions.load_from(result)
result.write()
# # Output
print("x[a,(i,j),t] values:")
for a in model.agents:
    for (i,j) in model.edges:
        for t in model.time_window:
            val = model.x[a, (i,j), t].value
            if val is not None and val > 0:
                print(f"x[{a},{i}->{j},{t}] = {val}")
print("\np[a,n,t] values:")
for a in model.agents:
    for n in model.nodes:
        for t in model.time_window:
            val = model.p[a, n, t].value
            if val is not None and val > 0:
                print(f"p[{a},{n},{t}] = {val}")
print("Objective (cost):", model.cost())


