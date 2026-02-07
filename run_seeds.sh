#!/usr/bin/env bash

SEEDS="1 2 3 4 5"
TRAINS="5 10 15 20 25 30"

BASE_CONFIG="data/scenario_configurations/test.json"
CFG_DIR="data/scenario_configurations"

for n_trains in $TRAINS; do
  for seed in $SEEDS; do
    cfg="$CFG_DIR/tmp_${n_trains}_trains_seed_${seed}.json"
    scenario="${n_trains}_trains${seed}.json"

    jq ".seed = $seed | .number_of_trains = $n_trains" \
      "$BASE_CONFIG" > "$cfg"

    python src/main.py \
      --config "$(basename "$cfg")" \
      --scenario-file "$scenario"
  done
done

rm -f "$CFG_DIR"/tmp_*_trains_seed_*.json
