
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
import osmnx as ox


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

    def combine(self):
        # Define combined bounds for full coverage
        node_positions = [data for _, data in self.G.nodes(data=True)]
        graph_bounds = (
            min(node["x"] for node in node_positions),  # minx
            min(node["y"] for node in node_positions),  # miny
            max(node["x"] for node in node_positions),  # maxx
            max(node["y"] for node in node_positions),  # maxy
        )
        building_bounds = self.Buildings.total_bounds
        combined_bounds = (
            min(building_bounds[0], graph_bounds[0]),
            min(building_bounds[1], graph_bounds[1]),
            max(building_bounds[2], graph_bounds[2]),
            max(building_bounds[3], graph_bounds[3])
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
