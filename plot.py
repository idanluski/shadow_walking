import osmnx as ox
from pvlib.location import Location
from datetime import datetime
import matplotlib.pyplot as plt
import re
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon, LineString
import geopandas as gpd

ox.settings.use_cache = False
# Define the location and time
location = Location(latitude=31.261, longitude=34.802)
time = datetime(2024, 11, 27, 14, 30)  # Example time (noon)
solar_position = location.get_solarposition(time)

# Extract solar azimuth and altitude
azimuth = solar_position['azimuth']
altitude = solar_position['apparent_elevation']

place_name = "Ben Gurion University, Beer Sheva, Israel"
custom_filter = '["highway"~"footway|path|pedestrian|sidewalk|cycleway|living_street|service|unclassified|residential|tertiary|road"]'

# Extract graph and geometries
G = ox.graph_from_place(place_name, network_type="walk", custom_filter=custom_filter)
G = ox.project_graph(G, to_crs='EPSG:32636')

buildings = ox.geometries_from_place(place_name, tags={"building": True})

# Define combined bounds for full coverage
node_positions = [data for _, data in G.nodes(data=True)]
graph_bounds = (
    min(node["x"] for node in node_positions),  # minx
    min(node["y"] for node in node_positions),  # miny
    max(node["x"] for node in node_positions),  # maxx
    max(node["y"] for node in node_positions),  # maxy
)
building_bounds = buildings.total_bounds 
combined_bounds = (
    min(building_bounds[0], graph_bounds[0]),
    min(building_bounds[1], graph_bounds[1]),
    max(building_bounds[2], graph_bounds[2]),
    max(building_bounds[3], graph_bounds[3])
)

# Plot functions
def plot_graph(G, buildings, custom_bounds=None):
    fig, ax = plt.subplots(figsize=(14, 14))
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color="gray", edge_linewidth=0.5)
    buildings.plot(ax=ax, color="orange", alpha=0.7, edgecolor="black")
    if custom_bounds:
        ax.set_xlim([custom_bounds[0], custom_bounds[2]])
        ax.set_ylim([custom_bounds[1], custom_bounds[3]])
    plt.title("Buildings and Roads at Ben Gurion University", fontsize=16)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

def pedestrian(place_name):
    pedestrian_paths = ox.geometries_from_place(
        place_name,
        tags={"highway": ["footway", "path", "pedestrian", "sidewalk", "cycleway", "living_street", "service", "unclassified"]}
    )
    fig, ax = plt.subplots(figsize=(14, 14))
    pedestrian_paths.plot(ax=ax, color="green", alpha=0.6, linewidth=1)
    plt.title("Raw Pedestrian Paths at Ben Gurion University", fontsize=16)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

def plot_roads_as_graph(G, custom_bounds=None):
    fig, ax = plt.subplots(figsize=(14, 14))
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color='blue',node_size=15,node_color='red', edge_linewidth=0.8)
    if custom_bounds:
        ax.set_xlim([custom_bounds[0], custom_bounds[2]])
        ax.set_ylim([custom_bounds[1], custom_bounds[3]])
    plt.title("Roads at Ben Gurion University", fontsize=16)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()



def after_shadow(buildings):
        # Assuming `buildings` GeoDataFrame now has a 'shadow_geometry' column with the extended shadows
    # Create a new GeoDataFrame to store buildings with extended shadows for easier plotting
    buildings_with_shadows =buildings

    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot original buildings in blue
    buildings.plot(ax=ax, color='blue', alpha=0.5, edgecolor='k', label='Original Buildings')

    # Plot buildings with extended shadows in green (or any color you like)
    buildings_with_shadows.plot(ax=ax, color='green', alpha=0.4, edgecolor='r', label='Buildings with Shadows')

    # Add legend, title, and labels for better interpretation
    plt.legend()
    plt.title("Buildings with Extended Shadows")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    # Show the plot
    plt.show()

def plot_graph_with_numeric_addresses(G, buildings, custom_bounds=None):
    fig, ax = plt.subplots(figsize=(14, 14))
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color="gray", edge_linewidth=0.5)
    buildings.plot(ax=ax, color="orange", alpha=0.7, edgecolor="black")
    
    # Adding numeric house number labels to buildings if available
    for idx, building in buildings.iterrows():
        housenumber = building.get('addr:housenumber', None)

        if pd.notna(housenumber):
            # Extract only the numeric part of the house number
            numeric_housenumber = ''.join(re.findall(r'\d+', str(housenumber)))

            if numeric_housenumber:  # Only label if a numeric part exists
                centroid = building.geometry.centroid
                ax.text(centroid.x, centroid.y, numeric_housenumber, fontsize=8, color='black', alpha=0.9, ha='center')

    if custom_bounds:
        ax.set_xlim([custom_bounds[0], custom_bounds[2]])
        ax.set_ylim([custom_bounds[1], custom_bounds[3]])
    
    plt.title("Buildings and Roads at Ben Gurion University with Numeric House Numbers", fontsize=16)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


def analyze_and_plot_coverage(G, buildings, custom_bounds=None):
    # Step 1: Create a MultiPolygon for all shadow geometries
    all_shadows = MultiPolygon([shadow for shadow in buildings['shadow_geometry'] if shadow is not None])

    # Step 2: Plot all the shadows, paths, and buildings with numeric addresses
    fig, ax = plt.subplots(figsize=(14, 14))

    # Plot the roads graph using osmnx
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color='gray', edge_linewidth=0.5)

    # Plot all shadows on top of roads
    shadows_gdf = gpd.GeoSeries(all_shadows)
    shadows_gdf.plot(ax=ax, color='darkgrey', alpha=0.7, label='Shadows')

    # Plot buildings
    buildings.plot(ax=ax, color='orange', alpha=0.7, edgecolor='black')

    # Adding numeric house number labels to buildings if available
    for idx, building in buildings.iterrows():
        housenumber = building.get('addr:housenumber', None)

        if pd.notna(housenumber):
            # Extract only the numeric part of the house number
            numeric_housenumber = ''.join(re.findall(r'\d+', str(housenumber)))

            if numeric_housenumber:  # Only label if a numeric part exists
                centroid = building.geometry.centroid
                ax.text(centroid.x, centroid.y, numeric_housenumber, fontsize=8, color='black', alpha=0.9, ha='center')

    # Apply custom bounds if provided
    if custom_bounds:
        ax.set_xlim([custom_bounds[0], custom_bounds[2]])
        ax.set_ylim([custom_bounds[1], custom_bounds[3]])

    # Add legend and labels
    ax.set_title('Buildings, Shadows, and Paths at Ben Gurion University with Numeric House Numbers')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.legend()
    plt.show()


# Plotting
#plot_graph_with_numeric_addresses(G, buildings, custom_bounds=combined_bounds)
#plot_graph(G, buildings, custom_bounds=combined_bounds)
#pedestrian(place_name)
#plot_roads_as_graph(G, custom_bounds=combined_bounds)
