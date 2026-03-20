#!/bin/bash
#
#SBATCH --job-name="test_array"
#SBATCH --time=01:30:00
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=3GB
#SBATCH --account=education-eemcs-msc-cs
#SBATCH --array=0-0   # 👈 ONLY ONE TASK (5 scenarios)

#SBATCH --output=logs/out_%A_%a.txt
#SBATCH --error=logs/err_%A_%a.txt

# ================= MODULES =================
module load 2025
module load python
module load gurobi/12.0.0
module load pyomo

# ================= ENV =================
cd /home/thomasverwaal/Robust-Rail-NL/mathematical-models
source ~/pyomo_project/env/bin/activate

# ================= RUN =================
srun python3 ADMM_constraint_edges_cluster.py