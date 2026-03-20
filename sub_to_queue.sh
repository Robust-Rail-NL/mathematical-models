#!/bin/bash
#
#SBATCH --job-name="test"
#SBATCH --time=01:30:00
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=3GB
#SBATCH --account=education-eemcs-msc-cs

# Run Python script:
module load 2025
module load python
module load gurobi/12.0.0

cd ~/pyomo_project
source env/bin/activate

module load pyomo

srun python3 /home/thomasverwaal/Robust-Rail-NL/MathemticalModels/ADMM_constraint_edges.py