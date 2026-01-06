import pyroutelib3

live_graph = pyroutelib3.osm.LiveGraph(pyroutelib3.osm.CarProfile())

start_node = live_graph.find_nearest_node((52.23201, 21.00737))
end_node = live_graph.find_nearest_node((52.24158, 21.02807))

route = pyroutelib3.find_route_without_turn_around(live_graph, start_node.id, end_node.id)
route_lat_lons = [live_graph.get_node(node).position for node in route]