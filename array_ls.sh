#!/bin/bash
#SBATCH --job-name="rail_solver"
#SBATCH --time=00:40:00
#SBATCH --partition=compute
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=3968MB
#SBATCH --account=education-eemcs-msc-cs
#SBATCH --array=0-0

#SBATCH --output=logs_ls/out_%A_%a.txt
#SBATCH --error=logs_ls/err_%A_%a.txt

# ------------------ SETUP ------------------

module load 2025
export DOTNET_ROOT=$HOME/dotnet
export PATH=$DOTNET_ROOT:$PATH

PROJECT_DIR=~/Robust-Rail-NL/robust-rail-solver/ServiceSiteScheduling/publish
CONFIG_TEMPLATE=~/Robust-Rail-NL/configs/config_cluster.yaml
SCENARIO_LIST=~/Robust-Rail-NL/mathematical-models/scenarios_types.txt

PLAN_DIR=~/Robust-Rail-NL/mathematical-models/local_search_plans
mkdir -p $PLAN_DIR

BATCH_SIZE=5

cd $PROJECT_DIR

# ------------------ COMPUTE RANGE ------------------

START=$((SLURM_ARRAY_TASK_ID * BATCH_SIZE + 1))
END=$((START + BATCH_SIZE - 1))

RESULT_FILE=~/Robust-Rail-NL/mathematical-models/results_ls/results_${SLURM_ARRAY_TASK_ID}.csv
echo "scenario,cost_line,time_line,plan_file" > $RESULT_FILE

# ------------------ LOOP OVER SCENARIOS ------------------

for i in $(seq $START $END)
do
    SCENARIO=$(sed -n "${i}p" $SCENARIO_LIST)

    if [ -z "$SCENARIO" ]; then
        break
    fi

    echo "Running scenario: $SCENARIO"

    TMP_CONFIG=tmp_config_${SLURM_ARRAY_TASK_ID}_${i}.yaml
    OUTPUT_FILE=tmp_output_${SLURM_ARRAY_TASK_ID}_${i}.txt

    # ------------------ CREATE PLAN NAME ------------------

    BASENAME=$(basename "$SCENARIO" .json)

    # Remove prefixes
    BASENAME=${BASENAME/_solver/}
    BASENAME=${BASENAME/scenario_/}

    PLAN_FILE=$PLAN_DIR/plan_${BASENAME}.json

    # ------------------ CREATE CONFIG ------------------

    cp $CONFIG_TEMPLATE $TMP_CONFIG

    # Solver scenario
    sed -i "s|ScenarioPath:.*|ScenarioPath: \"$SCENARIO\"|" $TMP_CONFIG

    # Evaluation scenario
    EVAL_SCENARIO=$(echo "$SCENARIO" | sed 's/_solver//')
    sed -i "s|PathScenario:.*|    PathScenario: \"$EVAL_SCENARIO\"|" $TMP_CONFIG

    # Plan paths
    sed -i "s|PlanPath:.*|PlanPath: \"$PLAN_FILE\"|" $TMP_CONFIG
    sed -i "s|PathPlan:.*|    PathPlan: \"$PLAN_FILE\"|" $TMP_CONFIG

    # ------------------ RUN SOLVER ------------------

    timeout 1800s srun ./ServiceSiteScheduling --config=$TMP_CONFIG > $OUTPUT_FILE

    # ------------------ EXTRACT RESULTS ------------------

    COST_LINE=$(grep "Cost =" $OUTPUT_FILE | tail -1)
    TIME_LINE=$(grep "Total computation time" $OUTPUT_FILE | tail -1)

    if [ -z "$COST_LINE" ]; then
        COST_LINE="NO_COST_FOUND"
    fi

    if [ -z "$TIME_LINE" ]; then
        TIME_LINE="NO_TIME_FOUND"
    fi

    # Check if plan was created
    if [ ! -f "$PLAN_FILE" ]; then
        PLAN_FILE="NO_PLAN_CREATED"
    fi

    # ------------------ STORE RESULT ------------------

    echo "\"$SCENARIO\",\"$COST_LINE\",\"$TIME_LINE\",\"$PLAN_FILE\"" >> $RESULT_FILE

    # Cleanup
    rm $TMP_CONFIG
    rm $OUTPUT_FILE

done

echo "Task ${SLURM_ARRAY_TASK_ID} finished."