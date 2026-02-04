import Lagrangian as L
import MILP as M
import ADMM as A
import csv
import os

l_s = []
# l_s.append(('locations/five_tracks_location.json',
# 'scenarios/five_tracks/two_trains_easiest.json')) # trains from opposite sides 5/3 to 2/4
# l_s.append(('locations/five_tracks_location.json',
# 'scenarios/five_tracks/two_trains_simple.json')) # both trains from the same side 5/4 to 2/3
# l_s.append(('locations/five_tracks_location.json',
# 'scenarios/five_tracks/two_trains.json')) # trains need to go to each others start track
# l_s.append(('locations/five_tracks_location.json',
# 'scenarios/five_tracks/three_trains.json')) # 4/5/3 to 2/3/5
# l_s.append(('locations/five_tracks_location.json',
# 'scenarios/five_tracks/three_trains_difficult.json')) # 4/5/3 to 3/2/5

# l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains_simple.json'))# 5/3 to 3/4
# l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains_more_time.json'))#5/3 to 3/5
# l_s.append(('locations/four_tracks_location.json', 'scenarios/four_tracks/two_trains.json'))#5/3 to 3/5

# l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/three_trains.json'))# 4/5/2 3/2/6
# l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/four_trains.json')) # 4/5/2/3 3/2/6/5
# l_s.append(('locations/six_tracks_location.json', 'scenarios/six_tracks/four_trains_difficult.json')) #4/5/2/3 3/2/6/4

# l_s.append(('locations/circle_location.json', 'scenarios/circle/four_trains.json'))
# l_s.append(('locations/circle_location_small.json', 'scenarios/circle/three_trains.json'))

# l_s.append(('locations/8_tracks_location.json', 'scenarios/8_tracks/7_trains.json'))
# l_s.append(('locations/ten_tracks_location.json', 'scenarios/ten_tracks/nine_trains.json'))
# l_s.append(('locations/ten_tracks_location.json', 'scenarios/ten_tracks/nine_trains_more_time.json'))
# l_s.append(('locations/ten_tracks_location.json', 'scenarios/ten_tracks/ten_trains.json'))
# l_s.append(('locations/ten_tracks_location.json', 'scenarios/ten_tracks/ten_trains_more_time.json'))

# l_s.append(('locations/6_tracks_location.json', 'scenarios/6_tracks/4_trains.json'))
# l_s.append(('locations/6_tracks_location.json', 'scenarios/6_tracks/5_trains.json'))
# l_s.append(('locations/6_tracks_location.json', 'scenarios/6_tracks/5_trains_difficult.json'))
# l_s.append(('locations/9_tracks_location.json', 'scenarios/9_tracks/7_trains.json'))
# l_s.append(('locations/9_tracks_location.json', 'scenarios/9_tracks/7_trains_difficult.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/5_trains.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/5_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/5_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/5_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/5_trains5.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/10_trains.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/10_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/10_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/10_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/10_trains5.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/15_trains.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/15_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/15_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/15_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/15_trains5.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/20_trains.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/20_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/20_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/20_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/20_trains5.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst3/25_trains.json'))

l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/5_trains1.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/5_trains2.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/5_trains3.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/5_trains4.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/5_trains5.json'))

l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/10_trains1.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/10_trains2.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/10_trains3.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/10_trains4.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/10_trains5.json'))

l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/15_trains1.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/15_trains2.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/15_trains3.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/15_trains4.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/15_trains5.json'))

l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/20_trains1.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/20_trains2.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/20_trains3.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/20_trains4.json'))
l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/20_trains5.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/25_trains1.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/25_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/25_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/25_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/25_trains5.json'))

# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/30_trains1.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/30_trains2.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/30_trains3.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/30_trains4.json'))
# l_s.append(('locations/binckhorst.json', 'scenarios/binckhorst_mixed_traffic_false/30_trains5.json'))


with open("results/MILP_mixed_traffic_2.csv", mode="w", newline="") as file:
  writer = csv.writer(file)
  writer.writerow(["num_trains", "k", "time", "time_solution"])
  for loc, scenario in l_s:
    # nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r, m = L.setup(loc, scenario)
    # k, time = L.Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, r, m)
    
    # nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho = A.setup(loc, scenario)
    # k, time = A.Lagrangian(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types, time_window, lambda_values, mu_values, node_admm_values, edge_admm_values, r, cost, rho)
    
    nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types = M.setup(loc, scenario)
    k, time, time_solution = M.solve(nodes, edges, agents, start_nodes, arrival_time, departures, start_time, end_time, train_types)
    filename = os.path.basename(scenario)
    num_trains = len(agents)
    writer.writerow([num_trains, k, time, time_solution])
    print(f"Finished scenario {scenario} with {num_trains} trains: k={k}, time={time}, time_solution={time_solution}")
    
    # filename = os.path.basename(scenario)  
    # num_trains = len(agents)
    # writer.writerow([num_trains, k, time])
    # print(f"Finished scenario {scenario} with {num_trains} trains: k={k}, time={time}")