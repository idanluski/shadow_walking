
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
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
        self.buildings_gdf = self.convert_geodata()

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

    def get_nearest_node(self, x, y):
         return ox.distance.nearest_nodes(self.G, X=x, Y=y)

    def graph_to_gdfs(self):
        nodes_gdf, edges_gdf = ox.graph_to_gdfs(self.G, nodes=True, edges=True)
        return nodes_gdf, edges_gdf

    def plot_route_folium(self, route_nodes, weight=5, color='blue' ):
        return ox.plot_route_folium(self.G, route_nodes, weight=weight, color=color)

    def find_nodes_in_G(self, dest, original):
        """
         take 2 point from GPS and fines the nearest node in G
         input : tuple contain (lat,lng)
        """

        # origin_latlng = (31.2622, 34.8007)
        # dest_latlng   = (31.2615, 34.7991)
        origin_latlng = original
        dest_latlng = dest

        # In OSMnx, the graph is projected, but the function nearest_nodes()
        # expects x=longitude, y=latitude in the graph’s coordinate system.
        # For a projected graph, we need to first transform our lat/lng to EPSG:32636.

        # Let's create a tiny GeoDataFrame with our origin/destination in WGS84:

        coords_gdf = gpd.GeoDataFrame(
            geometry=[Point(origin_latlng[1], origin_latlng[0]),  # (lon, lat)
                      Point(dest_latlng[1], dest_latlng[0])],
            crs="EPSG:4326"
        )
        # Reproject to EPSG:32636
        coords_gdf_32636 = coords_gdf.to_crs(epsg=32636)
        # Extract x, y
        origin_x_32636, origin_y_32636 = coords_gdf_32636.geometry.iloc[0].x, coords_gdf_32636.geometry.iloc[0].y
        dest_x_32636, dest_y_32636 = coords_gdf_32636.geometry.iloc[1].x, coords_gdf_32636.geometry.iloc[1].y

        # Now find nearest nodes in the projected graph
        orig_node_32636 = self.get_nearest_node(x=origin_x_32636, y=origin_y_32636)
        dest_node_32636 = self.get_nearest_node(x=dest_x_32636, y=dest_y_32636)
        return orig_node_32636, dest_node_32636
