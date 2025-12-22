import Lagrangian as L

l_s = []
l_s.append(('locations/five_tracks_location.json',
'scenarios/five_tracks/two_trains_easiest.json')) # both trains from the same side 5/4 to 2/3
l_s.append(('locations/five_tracks_location.json',
'scenarios/five_tracks/two_trains_simple.json')) # trains from opposite sides 5/3 to 2/4
l_s.append(('locations/five_tracks_location.json',
'scenarios/five_tracks/two_trains.json')) # trains need to go to each others start track
l_s.append(('locations/five_tracks_location.json',
'scenarios/five_tracks/three_trains.json')) # 4/5/3 to 3/2/5
l_s.append(('locations/five_tracks_location.json',
'scenarios/five_tracks/three_trains_difficult.json')) #4/5/3 to 2/3/5

l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains_simple.json'))# 5/3 to 3/4
l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains_more_time.json'))#5/3 to 3/5
l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains.json'))#5/3 to 3/5

l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/three_trains.json'))# 4/5/2 3/2/6
l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/four_trains.json')) # 4/5/2/3 3/2/6/5
l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/four_trains_difficult.json')) #4/5/2/3 3/2/6/4

# l_s.append(('locations/8_tracks_location.json', 'scenarios/8_tracks/7_trains.json'))

for i in l_s:
  print(i)
  nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r = L.setup(i[0], i[1])
  L.Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r)