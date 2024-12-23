
import osmnx as ox
import networkx as nx
from shapely.geometry import Polygon
from shapely.geometry import LineString
from pvlib.location import Location
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import folium
import geopandas as gpd
import utils
import shadow
import plot as pl
import settings
import re





#ox.settings.use_cache = False
# Extract solar azimuth and altitude
azimuth = settings.solar_position['azimuth']
altitude = settings.solar_position['apparent_elevation']

# Initialize Graph and Buildings (assuming pl module has these)
G = pl.G
G = ox.project_graph(G, to_crs='EPSG:32636')
buildings = pl.buildings

# Calculate height for buildings and check building levels
utils.calculate_high(buildings)
utils.handel_bad_path(G)

print("\nBuilding Levels:")
print(buildings['levels'])
print(buildings.crs)

# Reproject buildings to a suitable CRS (e.g., UTM zone 36N for Israel)
buildings = buildings.to_crs(epsg=32636)  # Use EPSG code corresponding to UTM zone


# Step 3: Calculate the area in square meters
buildings['area'] = buildings['geometry'].area



# Ensure height column exists
if 'height' not in buildings.columns:
    buildings['height'] = 0  # Initialize with 0 if not present

# Replace NaN values in height with 0
buildings['height'] = buildings['height'].fillna(0)

# Debug: Print buildings with updated height values
print("\nBuildings with Updated Heights:")
print(buildings[['height', 'geometry']])

# Convert geometry column to GeoDataFrame format if needed
shadow.convert_geodata(buildings)


buildings = buildings.to_crs(epsg=32636)
buildings['shadow_geometry'] = buildings.apply(lambda b: shadow.generate_distorted_shadow(b, azimuth, altitude), axis=1)

buildings_with_only_shadows = buildings.copy()
buildings_with_only_shadows = buildings_with_only_shadows.to_crs(epsg=32636)
buildings_with_only_shadows['shadow_only_geometry'] = buildings_with_only_shadows.apply(
    lambda row: row['shadow_geometry'].difference(row['geometry']) if row['shadow_geometry'] is not None else None,
    axis=1
)
shadow_only_gdf = gpd.GeoDataFrame(buildings_with_only_shadows, geometry='shadow_only_geometry')
fig, ax = plt.subplots(figsize=(12, 10))
shadow_only_gdf.plot(ax=ax, color='green', alpha=0.5, edgecolor='g', label='Shadow Extensions Only')


# Set up the plot
fig, ax = plt.subplots(figsize=(12, 10))

# Plot original buildings in blue
buildings.plot(ax=ax, color='blue', alpha=0.5, edgecolor='k', label='Original Buildings')


# Adding numeric house number labels to buildings if available
for idx, building in buildings.iterrows():
    height = building.get('height', None)

    if pd.notna(height):
        # Extract only the numeric part of the house number
        height = ''.join(re.findall(r'\d+', str(height)))

        if height:  # Only label if a numeric part exists
            centroid = building.geometry.centroid
            ax.text(centroid.x, centroid.y, height, fontsize=8, color='black', alpha=0.9, ha='center')
# Plot only the shadow areas in red with increased transparency
shadow_gdf = gpd.GeoDataFrame(buildings, geometry='shadow_geometry')
shadow_gdf.plot(ax=ax, color='red', alpha=0.3, edgecolor='r', label='Shadows Only')
# Set the initial CRS (replace 'EPSG:4326' with your known CRS if different)
shadow_gdf = shadow_gdf.set_crs(epsg=32636)

# Now you can convert to your target CRS
shadow_gdf = shadow_gdf.to_crs(epsg=32636)

# Add legend, title, and labels for better interpretation
plt.legend()
plt.title("Original Buildings and Translated Shadows")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

# Show the plot
plt.show()





print("-------------------------------------------------")
#edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
#utils.analyze_coverage_gdf(edges, shadow_gdf,pl.combined_bounds)
utils.analyze_coverage(G, shadow_gdf, buildings, pl.combined_bounds)

pl.analyze_and_plot_coverage(G,buildings,pl.combined_bounds)




# pl.after_shadow(buildings)
# # Debug: Print buildings with calculated shadow geometries
# print("\nBuildings with Shadow Geometry:")
# print(buildings[['shadow_geometry']])

# Calculate shadow weight for each edge in graph G
# edges_shadow_weight = []
# for edge in G.edges(data=True):
#     try:
#         shadow_weight = shadow.calculate_shadow_weight(edge, buildings)
#         edges_shadow_weight.append(shadow_weight)
        
#         # Debugging each edge's shadow weight calculation
#         print(f"\nEdge: {edge}, Shadow Weight: {shadow_weight}")
#     except Exception as e:
#         print(f"Error calculating shadow weight for edge {edge}: {e}")
#         edges_shadow_weight.append(None)  # Append None for problematic edges

# # Debug: Final shadow weight results
# print("\nFinal Shadow Weights for Edges:")
# print(edges_shadow_weight)



# edges_shadow_weight = [shadow.calculate_shadow_weight(edge, buildings) for edge in G.edges(data=True)]

# for (u, v, key, data), shadow_weight in zip(G.edges(keys=True, data=True), edges_shadow_weight):
#     data['shadow_weight'] = shadow_weight
#     data['total_weight'] = data['length'] + shadow_weight * settings.shadow_penalty_factor


# # Add a custom weight attribute (e.g., shadow factor)
# for u, v, data in G.edges(data=True):
#     data["weight"] = data.get("length", 1)  # use 'length' as the default weight


# # Add a custom weight attribute (e.g., shadow factor)
# for u, v, data in G.edges(data=True):
#     data["weight"] = data.get("length", 1)  # use 'length' as the default weight

# for u, v, data in G.edges(data=True):
#     print(f"Edge from {u} to {v}:")



# fig, ax = plt.subplots()
# buildings.plot(ax=ax, color='gray', alpha=0.5)
# ox.plot_graph(G, ax=ax)
# ox.plot_graph(G)
# # Choose two nodes in the graph
# origin_node = list(G.nodes)[0]
# destination_node = list(G.nodes)[-1]

# # Use Dijkstra's algorithm to find the shortest path based on the 'weight' attribute
# shortest_path = nx.shortest_path(G, source=origin_node, target=destination_node, weight="weight")

# print("Shortest path:", shortest_path)


