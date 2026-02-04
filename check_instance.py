import json
# Calculates the maximum number of trains in the yard at any time for given datasets

datasets = [
    'scenarios/binckhorst3/20_trains5.json',
    'scenarios/binckhorst3/20_trains4.json',
    'scenarios/binckhorst3/20_trains3.json',
    'scenarios/binckhorst3/20_trains2.json',
    'scenarios/binckhorst3/20_trains.json',
    'scenarios/binckhorst3/15_trains.json',
    'scenarios/binckhorst3/15_trains2.json',
    'scenarios/binckhorst3/15_trains3.json',
    'scenarios/binckhorst3/15_trains4.json',
    'scenarios/binckhorst3/15_trains5.json',
    'scenarios/binckhorst3/10_trains.json',
    'scenarios/binckhorst3/10_trains2.json',
    'scenarios/binckhorst3/10_trains3.json',
    'scenarios/binckhorst3/10_trains4.json',
    'scenarios/binckhorst3/10_trains5.json',
    'scenarios/binckhorst3/5_trains.json',
    'scenarios/binckhorst3/5_trains2.json',
    'scenarios/binckhorst3/5_trains3.json',
    'scenarios/binckhorst3/5_trains4.json',
    'scenarios/binckhorst3/5_trains5.json',
    'scenarios/binckhorst3/testing.json',
]

for idx, file_path in enumerate(datasets):
    with open(file_path, "r") as f:
        data = json.load(f)

    events = []

    in_trains = data.get("in", {}).get("trains", [])
    out_trains = data.get("out", {}).get("trainRequests", [])

    n = min(len(in_trains), len(out_trains))
    for i in range(n):
        in_train = in_trains[i]
        out_train = out_trains[i]

        arrival = int(in_train.get("arrival", 0))
        departure = int(out_train.get("departure", 0))

        events.append((arrival, 1))
        events.append((departure, -1))
    events.sort(key=lambda x: (x[0], -x[1]))

    current_trains = 0
    max_trains = 0
    for _, change in events:
        current_trains += change
        max_trains = max(max_trains, current_trains)

    print(f"{file_path}: Maximum number of trains in yard = {max_trains}")