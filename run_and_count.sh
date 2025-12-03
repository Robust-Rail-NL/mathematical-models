#!/bin/bash

N_RUNS=50
SCRIPT="5_3.py"
SEARCH_TEXT="NO MORE CONFLICT"

# ✅ Force user site-packages to be visible
export PYTHONPATH="$HOME/.local/lib/python3.10/site-packages"

count=0

for ((i=1; i<=N_RUNS; i++))
do
    echo "Run $i / $N_RUNS"

    output=$(/usr/bin/python3.10 "$SCRIPT" 2>&1)

    if echo "$output" | grep -qF "$SEARCH_TEXT"; then
        ((count++))
        echo "✅ Found"
    else
        echo "❌ Not found"
    fi
done

echo "-----------------------------------"
echo "Total occurrences of '$SEARCH_TEXT': $count"
echo "Out of $N_RUNS runs"

