#!/usr/bin/env bash

repo_path="$(dirname $(realpath $file))"

NUM_SEEDS=5
TRAINS="5 10 15 20 25 30"

BASE_CONFIG="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/configurations/scenario_config_test.json"
CFG_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/configurations"

EVAL_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios_eval"
SOLVER_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios_solver"

GENERATOR_PATH="${repo_path}/robust-rail-generator/src/main.py"

for n_trains in $TRAINS; do
  for ((seed=1; seed<=NUM_SEEDS; seed++)); do
    cfg="$CFG_DIR/tmp_${n_trains}_trains_seed_${seed}.json"
    scenario="scenario_${n_trains}_trains${seed}.json"

    jq ".seed = $seed | .number_of_trains = $n_trains" \
      "$BASE_CONFIG" > "$cfg"

    python ${GENERATOR_PATH} \
      --config "$(basename "$cfg")" \
      --scenario-file "$scenario"
  done
done

# Create destination folders if they don't exist
mkdir -p "$EVAL_DIR"
mkdir -p "$SOLVER_DIR"

# Source directory where Python writes files
SRC_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios"

# Move solver files first
mv "$SRC_DIR"/scenario_solver_*.json "$SOLVER_DIR" 2>/dev/null

# Move normal scenario files
mv "$SRC_DIR"/scenario_[0-9]*.json "$EVAL_DIR" 2>/dev/null

# Cleanup temp configs
rm -f "$CFG_DIR"/tmp_*_trains_seed_*.json
