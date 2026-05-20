# Experimental data and results
This folder contains the scenarios used for the experimental evaluation in the Thesis TODO (add link) and the results of the evaluation. It also contains some simple locations and scenarios that weere used for testing.
Most of the data folders also contain a script that was used to combine the results into one csv file.

Folders:
- [data_milp](https://github.com/Robust-Rail-NL/mathematical-models/data/data_milp): this folder contains the scenarios and results for the evalution of [MILP.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/MILP.py).
- [data_rho_n](https://github.com/Robust-Rail-NL/mathematical-models/data/data_rho_n): this folder contains the scenarios and results for the hyperparameter tuning for the rho and starting stepsize value (n) in ADMM.
These experiments were run with [ADMM.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/ADMM.py).
- [data_time_window](https://github.com/Robust-Rail-NL/mathematical-models/data/data_time_window): this folder contains the scenarios and results for the experiment with different time windows in which discreet Local Search and ADMM were compared.
This experiment was run with both [ADMM.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/ADMM.py) and [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py),
the results from [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py) were used in the thesis.
- [data_types_7hours](https://github.com/Robust-Rail-NL/mathematical-models/data/data_types_7hours): this folder contains the scenarios and results for the experiment with a time windows of 7 hours and train types:
1,5,1/3 and number of train in which continuous Local Search, discreet Local Search, ADMM and continuous ADMM were compared.
This experiment was run with [ADMM.py](https://github.com/Robust-Rail-NL/mathematical-models/src/gurobi/ADMM.py) (with rho=2), [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py) (with rho=0.5)
and [shortest_path_continuous.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path_continuous.py) (with rho=0.5). The results from [shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py) and 
and [shortest_path_continuous.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path_continuous.py) were used in the thesis. This experiment was also run with
[shortest_path.py](https://github.com/Robust-Rail-NL/mathematical-models/src/shortest_path.py) (with rho=2) to determine the effect of switching from using Gurobi to the A* algorithm independent of rho.
- [locations](https://github.com/Robust-Rail-NL/mathematical-models/data/locations):This folder contains a number of simple locations that were used for testing.
It also contains [location_solver.json](https://github.com/Robust-Rail-NL/mathematical-models/data/locations/location_solver.json) which is the location file used for the continuous LS, ADMM and SP experiments,
and [location_solver.json](https://github.com/Robust-Rail-NL/mathematical-models/data/locations/binckhorst_split_eval/location_solver.json) which is the location file used for discrete LS in which tracks are split into multiple
tracks of 100 meters long.
- [scenarios](https://github.com/Robust-Rail-NL/mathematical-models/data/locations):This folder contains a number of scenarios taking place at the locations in the locations folder that were used for testing.
- Most of these 
