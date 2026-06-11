#!/usr/bin/env bash

repo_path="$(dirname $(realpath $file))"

set -euo pipefail
NUM_SEEDS=30
TRAINS="5 10 15 20 25 26 27 28 29 30 31 32 33"

BASE_CONFIG="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/configurations/scenario_config_test.json"
CFG_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/configurations"

EVAL_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios_eval"
SOLVER_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios_solver"

SRC_DIR="${repo_path}/scenario-planning-inputs/Location_KleineBinckhorst/scenarios"

GENERATOR_PATH="${repo_path}/robust-rail-generator/src/main.py"

mkdir -p "$EVAL_DIR"
mkdir -p "$SOLVER_DIR"

ALL_TYPES=(
  "VIRM4-4" "VIRM6-6"
  "DDZ4-4" "DDZ6-6"
  "SLT4-4" "SLT6-6"
  "ICM3-3" "ICM4-4"
  "ICR7-7" "ICR9-9"
  "FLIRT FFF3-3" "FLIRT FFF4-4"
  "SNG3-3" "SNG4-4"
  "SGMM2-2" "SGMM3-3"
  "ICNG5-5" "ICNG8-8"
  "SLT5-5" "SLT7-7"
  "SLT8-8" "SLT9-9"
  "SLT10-10" "SLT11-11"
  "VIRM5-5" "VIRM7-7"
  "VIRM8-8" "VIRM9-9"
  "DDZ5-5" "DDZ7-7"
  "DDZ8-8" "DDZ9-9"
  "ICM5-5"
)

pick_types() {
  local n=$1
  printf "%s\n" "${ALL_TYPES[@]}" | head -n "$n"
}

for n_trains in $TRAINS; do
  UNIT_TYPES=(1 5 $(( (n_trains + 2) / 3 )) $(( (n_trains + 1) / 2 )) $n_trains)

  for n_units in "${UNIT_TYPES[@]}"; do
    for ((seed=1; seed<=NUM_SEEDS; seed++)); do
      echo "Running: trains=$n_trains units=$n_units seed=$seed"
      cfg="$CFG_DIR/tmp_${n_trains}_trains_${n_units}_units${seed}.json"
      scenario="scenario_${n_trains}_trains_${n_units}_units${seed}.json"

      types=$(pick_types "$n_units")
      types_json=$(printf '%s\n' "$types" | jq -R . | jq -s .)

      derived_seed=$(( seed + 1000 * n_units + 100000 * n_trains ))
      jq \
        --argjson types "$types_json" \
        ".seed = $derived_seed
         | .number_of_trains = $n_trains
         | .number_of_train_unit_types = $n_units
         | .train_unit_distribution.train_unit_types = \$types" \
        "$BASE_CONFIG" > "$cfg"

      python ${GENERATOR_PATH} \
        --config "$(basename "$cfg")" \
        --scenario-file "$scenario"
    done
  done
done

# Move solver files first
mv "$SRC_DIR"/scenario_solver_*.json "$SOLVER_DIR" 2>/dev/null

# Move normal scenario files
mv "$SRC_DIR"/scenario_[0-9]*.json "$EVAL_DIR" 2>/dev/null

# Cleanup temp configs
rm -f "$CFG_DIR"/tmp_*_trains_*_units*.json
