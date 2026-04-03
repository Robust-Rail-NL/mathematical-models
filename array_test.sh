#!/bin/bash
#
#SBATCH --job-name="test_array"
#SBATCH --time=04:00:00
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=education-eemcs-msc-cs
#SBATCH --array=0-294

#SBATCH --output=logs/out_%A_%a.txt
#SBATCH --error=logs/err_%A_%a.txt

module load 2025
module load python
module load gurobi/12.0.0
module load pyomo

cd /home/thomasverwaal/Robust-Rail-NL/mathematical-models
source ~/pyomo_project/env/bin/activate

srun python3 experiments_cluster.py