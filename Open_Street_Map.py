
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
import osmnx as ox
import random


class Open_Street_Map:
    def __init__(self):
        place_name = "Ben Gurion University, Beer Sheva, Israel"
        custom_filter = '["highway"~"footway|path|pedestrian|sidewalk|cycleway|living_street|service|unclassified|residential|tertiary|road|steps"]'
        self.crs = 'EPSG:32636'
        ox.settings.use_cache = False
        #G = pl.G
        G = ox.graph_from_place(place_name, network_type="walk", custom_filter=custom_filter, retain_all=True)
        G = ox.project_graph(G, to_crs=self.crs)
        self.G = G
        self.Buildings = ox.features_from_place(place_name, tags={"building": True})
        self.calculate_high()
        self.handel_bad_path()
        self.buildings_with_only_shadows = None
        self.combined_bounds = self.combine()
        self.buildings_gdf = self.convert_geodata()

    def combine(self):
        # Ensure buildings are reprojected to match the graph CRS
        buildings_projected = self.Buildings.to_crs(self.crs)

        # Define graph bounds based on node positions
        node_positions = [data for _, data in self.G.nodes(data=True)]
        graph_bounds = (
            min(node["x"] for node in node_positions),  # minx
            min(node["y"] for node in node_positions),  # miny
            max(node["x"] for node in node_positions),  # maxx
            max(node["y"] for node in node_positions),  # maxy
        )

        # Get bounds for buildings in the same CRS as the graph
        building_bounds = buildings_projected.total_bounds

        # Combine bounds
        combined_bounds = (
            min(building_bounds[0], graph_bounds[0]),  # minx
            min(building_bounds[1], graph_bounds[1]),  # miny
            max(building_bounds[2], graph_bounds[2]),  # maxx
            max(building_bounds[3], graph_bounds[3])  # maxy
        )
        return combined_bounds

    def calculate_high(self):
        # Set 'levels' to numeric if it exists, otherwise set to None
        floor_high = 2.7
        if 'building:levels' in self.Buildings.columns:
            self.Buildings['levels'] = pd.to_numeric(self.Buildings['building:levels'], errors='coerce')
        else:
            self.Buildings['levels'] = None
        print(self.Buildings['building:levels'])
        print(f"height : {self.Buildings['height']}")

        # If building has levels, calculate height as levels * 2.7
        self.Buildings['height'] = self.Buildings.apply(
            lambda row: row['levels'] * floor_high if pd.notna(row['levels']) else row['height'], axis=1
        )
        print(f"height : {self.Buildings['height']}")

        # Set height to 0 if it is still missing
        self.Buildings['height'].fillna(0, inplace=True)

    def handel_bad_path(self):
        """
        Add geometry if missing to the path in G
        """
        for u, v, key, edge in self.G.edges(keys=True, data=True):
            path = edge.get('geometry')

            # Check if geometry is missing
            if path is None:
                # Get the coordinates of the start and end nodes
                x1, y1 = self.G.nodes[u]['x'], self.G.nodes[u]['y']
                x2, y2 = self.G.nodes[v]['x'], self.G.nodes[v]['y']

                # Create a LineString geometry from the coordinates
                path = LineString([(x1, y1), (x2, y2)])
                edge['geometry'] = path

    def convert_geodata(self):
        return gpd.GeoDataFrame(self.Buildings)

    def validation_height_and_handel(self):
        if 'height' not in self.Buildings.columns:
            self.Buildings['height'] = 0  # Initialize with 0 if not present

        # Replace NaN values in height with 0
        self.Buildings['height'] = self.Buildings['height'].fillna(0)

    def get_nearest_node(self, x, y):
         return ox.distance.nearest_nodes(self.G, X=x, Y=y)

    def graph_to_gdfs(self):
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(self.G, nodes=True, edges=True)
        return nodes_gdf, edges_gdf

    def plot_route_folium(self, route_nodes, weight=5, color='blue' ):
        return ox.plot_route_folium(self.G, route_nodes, weight=weight, color=color)

    def find_nodes_in_G(self, dest, original):
        """
        Find nearest nodes in the graph for two points when the CRS of the input is the same as the graph's CRS.

        Input:
            dest: tuple of destination coordinates (x, y) in the same CRS as the graph.
            original: tuple of origin coordinates (x, y) in the same CRS as the graph.

        Output:
            orig_node: Nearest node in the graph to the origin point.
            dest_node: Nearest node in the graph to the destination point.
        """
        # Extract coordinates
        origin_x, origin_y = original
        dest_x, dest_y = dest

        # Validate coordinates against graph bounds
        bounds = self.combined_bounds  # minx, miny, maxx, maxy
        if not (bounds[0] <= origin_x <= bounds[2] and bounds[1] <= origin_y <= bounds[3]):
            raise ValueError(f"Origin point ({origin_x}, {origin_y}) is outside the graph bounds.")
        if not (bounds[0] <= dest_x <= bounds[2] and bounds[1] <= dest_y <= bounds[3]):
            raise ValueError(f"Destination point ({dest_x}, {dest_y}) is outside the graph bounds.")

        # Find nearest nodes
        orig_node = self.get_nearest_node(x=origin_x, y=origin_y)
        dest_node = self.get_nearest_node(x=dest_x, y=dest_y)

        return orig_node, dest_node

    def get_random_point_in_G(self):
        """
        Generate one random point within the bounds of the graph G.
        """
        # Get the graph bounds

        graph_bounds = self.combined_bounds  # minx, miny, maxx, maxy
        print("-----------------graph_bounds----------------------------")
        print(graph_bounds)
        while True:
            # Generate random coordinates within the bounds
            x = random.uniform(graph_bounds[0], graph_bounds[2])  # Between minx and maxx
            y = random.uniform(graph_bounds[1], graph_bounds[3])  # Between miny and maxy

            # Validate if the point is near any graph node
            try:
                self.get_nearest_node(x, y)  # Check if a valid node exists near this point
                return x, y  # Return the valid random point
            except Exception:
                # If no valid node is found, continue generating another point
                continue

