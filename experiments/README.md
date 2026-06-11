# Code used for experiments
This folder contains the scripts that were used for running the experiments on delftblue and the scripts used to generate the scenarios. It also contains
[default_train_units.json](https://github.com/Robust-Rail-NL/mathematical-models/experiments/experiment_scripts/default_train_units.json), which contains the train units used in scenario generation since the standard train units do not include enough different types needed for the experiments.
It also contains the code changes that were made in the robust-rail-solver such that the Local Search approach uses the same traversal times as the mathematical model.

Make sure that the generator, evaluator, solver and scenario-planning-inputs repos are all located in the same parent directory as the mathematical models.
