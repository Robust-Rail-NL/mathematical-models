# Implementation
This folder contains the implementations of different approaches that solve a mathematical model of a simplified version of the TUSP.
Each approach requires a location and scenario file as input:
- A location in robust-rail-solver format such as of the Kleine Binckhorst shunting yard [location_solver.json](https://github.com/Robust-Rail-NL/scenario-planning-inputs/blob/main/Location_KleineBinckhorst/location_solver.json).
The location is loaded with [load_location.py](https://github.com/Robust-Rail-NL/mathematical-models/src/load_location.py).
This code turns the location into the graph structure used by the model. As the continuous version of the shortest path approach requires extra 
- A scenario in robust-rail-solver format such as [scenario_solver_10_trains_10_units1.json](https://github.com/Robust-Rail-NL/mathematical-models/blob/cleanup/data/data_types_7hours/scenarios_solver/scenario_solver_10_trains_10_units1.json).
- Note that the model does not include service tasks and trains consits of one unit, any scenario containing these elements will produce errors.

There are five different approaches:
- [MILP.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/MILP.py): this script solves the model using Gurobi and Pyomo.
- [Lagrangian.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/Lagrangian.py): this script solves the model using Gurobi and Pyomo.
- [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py)
