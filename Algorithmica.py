import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
from Open_Street_Map import Open_Street_Map



class Algorithmic:
    def __init__(self, open_object : Open_Street_Map):
        self.open_street_map_object = open_object

    def shortest_path_near_bgu_with_buildings(self, dest, original):
        """
        input : tuple contain (lat,lng)

        1. Download road network and buildings near BGU, Beer Sheva, Israel.
        2. Project them to EPSG:32636.
        3. Compute a shortest path between two lat/lng coordinates near campus.
        4. Plot the route on a Folium map.
        5. (Optionally) plot buildings + edges + nodes in Matplotlib.
        """

        # Now find nearest nodes in the projected graph
        orig_node_32636, dest_node_32636 = self.open_street_map_object.find_nodes_in_G(dest, original)
        G = self.open_street_map_object.G
        # Shortest path by length (in meters)
        route_nodes = nx.shortest_path(G, orig_node_32636, dest_node_32636, weight='length')
        route_length = nx.shortest_path_length(G, orig_node_32636, dest_node_32636, weight='length')
        print("Route node IDs:", route_nodes)
        print(f"Route distance: {route_length:.2f} meters")

        # ----------------------------
        # 4) FOLIUM PLOT
        # ----------------------------
        # If we want to visualize in Folium, we must use the unprojected graph (in lat-lng, EPSG:4326).
        # So let's "unproject" (revert) or simply re-download the route in WGS84.
        # In practice, it's simpler to do the shortest-path in EPSG:32636
        # but *plot* it using the original G with lat/lng coords.

        # We can map the route_nodes (which are from G_32636) to the equivalent in G:
        # Easiest way: let OSMnx handle a "solution" using the original G for the folium route.
        # We'll demonstrate how to do that simply:
        route_map = self.open_street_map_object.plot_route_folium(route_nodes)
        route_map.save("bgu_route.html")
        print("Folium map saved to bgu_route.html")

        # ----------------------------
        # 5) (OPTIONAL) MATPLOTLIB PLOT
        # ----------------------------
        # Convert projected graph to GeoDataFrames
        nodes_gdf, edges_gdf = self.open_street_map_object.graph_to_gdfs()


        # Plot
        fig, ax = plt.subplots(figsize=(10,10))

        # a) Buildings
        self.open_street_map_object.buildings_gdf.plot(ax=ax, color='lightgray', alpha=0.7, edgecolor='none', label='Buildings')

        # b) Edges
        edges_gdf.plot(ax=ax, color='black', linewidth=1, alpha=0.8, label='Roads')

        # c) Nodes (optional)
        nodes_gdf.plot(ax=ax, color='red', markersize=5, label='Nodes')

        # d) Highlight the route
        #   We'll subset edges_gdf to only those edges in the route
        #   (But note in a MultiDiGraph, route edges are pairs of consecutive route_nodes)
        route_edges = list(zip(route_nodes[:-1], route_nodes[1:]))
        route_edges_set = set(route_edges)  # for quick membership check

        # We'll create a mask for edges that are in the route
        edges_gdf['is_route'] = edges_gdf.apply(lambda row:
                                                (row['u'], row['v']) in route_edges_set or
                                                (row['v'], row['u']) in route_edges_set, axis=1)
        edges_on_route = edges_gdf[edges_gdf['is_route'] == True]
        edges_on_route.plot(ax=ax, color='blue', linewidth=3, label='Route')

        # e) Add some legend / title
        ax.set_title("Ben-Gurion University Shortest Path (EPSG:32636)", fontsize=14)
        ax.legend()

        plt.show()



