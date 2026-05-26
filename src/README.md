# Implementation
This folder contains the implementations of different approaches that solve a mathematical model of a simplified version of the TUSP.
Each approach requires a location and scenario file as input:
- A location in robust-rail-solver format such as of the Kleine Binckhorst shunting yard [location_solver.json](https://github.com/Robust-Rail-NL/scenario-planning-inputs/blob/main/Location_KleineBinckhorst/location_solver.json).
The location is loaded with [load_location.py](https://github.com/Robust-Rail-NL/mathematical-models/src/load_location.py).
This code turns the location into the graph structure used by the model. The continuous version of the shortest path approach requires extra edges and we thus have two load location functions, ```load_location``` and ``` load_location_sp_continuous```.
- A scenario in robust-rail-solver format such as [scenario_solver_10_trains_10_units1.json](https://github.com/Robust-Rail-NL/mathematical-models/blob/cleanup/data/data_types_7hours/scenarios_solver/scenario_solver_10_trains_10_units1.json). Note that the model does not include service tasks and trains consits of multiple units, any scenario containing these elements will produce errors.

There are five different approaches:
- [MILP.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/MILP.py): this script solves the MILP model using Gurobi and Pyomo.
- [Lagrangian.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/Lagrangian.py): this script solves the Lagrangian Relaxation of the MILP model using Gurobi and Pyomo.
- [ADMM.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/ADMM.py): this script solves the augmented Lagrangian Relaxation of the MILP model with the Alternating Direction Method of Multipliers using Gurobi and Pyomo.
- [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py): this script solves the augmented Lagrangian Relaxation of the MILP model with the Alternating Direction Method of Multipliers using the A* shortest path algorithm.
- [shortest_path_continuous.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path_continuous.py): this script solves the augmented Lagrangian Relaxation of the MILP model with the Alternating Direction Method of Multipliers using the A* shortest path algorithm extended with continuous movements such that traversal between tracks orginating from the same track does not require extra time. This is the best performing approach.

The approaches solved with Gurobi and Pyomo use the constraints defined in [constraints_milp.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/constraints_milp.py) (used by [MILP.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/MILP.py))  and [constraints_lagrangian.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/constraints_lagrangian.py) (used by [Lagrangian.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/Lagrangian.py) and [ADMM.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/ADMM.py)).

[convert_to_plan.py](https://github.com/Robust-Rail-NL/mathematical-models/src/convert_to_plan.py): This script can be used to convert solutions found by the different approach, such as [sp_rho0.5_task0_scenario_solver_10_trains_10_units1.json](https://github.com/Robust-Rail-NL/mathematical-models/data/data_types_7hours/solutions_sp/sp_rho0.5_task0_scenario_solver_10_trains_10_units1.json), to the plan format of the [robust-rail-evaluator](https://github.com/Robust-Rail-NL/robust-rail-evaluator).

