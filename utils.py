import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon, Polygon, LineString, MultiLineString
from shapely.ops import unary_union
import plot as pl
from shapely.ops import linemerge


def calculate_high(buildings):
    # Set 'levels' to numeric if it exists, otherwise set to None
    floor_high = 2.7
    if 'building:levels' in buildings.columns:
        buildings['levels'] = pd.to_numeric(buildings['building:levels'], errors='coerce')
    else:
        buildings['levels'] = None
    print(buildings['building:levels'])    
    print(f"height : {buildings['height']}")


    # If building has levels, calculate height as levels * 2.7
    buildings['height'] = buildings.apply(
    lambda row: row['levels'] * floor_high if pd.notna(row['levels']) else row['height'], axis=1
    )
    print(f"height : {buildings['height']}")


    # Set height to 0 if it is still missing
    buildings['height'].fillna(0, inplace=True)



# def analyze_and_plot_coverage(G, buildings, custom_bounds=None):
#     # Step 1: Create a MultiPolygon for all building geometries
#     all_shadows = MultiPolygon([building for building in buildings['geometry'] if building is not None])

#     # Step 2: Validate and fix invalid geometries
#     all_shadows = all_shadows.buffer(0) if not all_shadows.is_valid else all_shadows

#     # Step 3: Merge all shadow and building polygons into a single MultiPolygon, ignoring overlaps
#     combined_geometry = unary_union([all_shadows])

#     # Step 4: Iterate over all the paths in the graph G and calculate the shadow/building coverage
#     covered_lengths = []
#     total_lengths = []

#     for u, v, edge in G.edges(data=True):
#         path = edge.get('geometry')
#         if path is not None and isinstance(path, (LineString, MultiLineString)):
#             if isinstance(path, MultiLineString):
#                 path = linemerge(path)  # Merge MultiLineString into LineString
            
#             # Step 5: Find the intersection of the path with the combined geometry
#             intersection = combined_geometry.intersection(path)

#             # Calculate the length of the path and the covered part
#             total_path_length = path.length
#             covered_path_length = intersection.length if not intersection.is_empty else 0

#             # Store the lengths for further analysis
#             covered_lengths.append(covered_path_length)
#             total_lengths.append(total_path_length)

#     # Step 6: Calculate the percentage of each path covered by shadow or building
#     coverage_percentages = [(covered / total) * 100 if total > 0 else 0 for covered, total in zip(covered_lengths, total_lengths)]

#     # Output the results for each path
#     for edge, coverage in zip(G.edges(data=True), coverage_percentages):
#         u, v, data = edge
#         print(f"Edge {u}-{v}: {coverage:.2f}% covered by shadow/buildings")


import matplotlib.pyplot as plt
from shapely.ops import linemerge, unary_union
from shapely.geometry import MultiPolygon, LineString, MultiLineString
import osmnx as ox

def analyze_and_plot_coverage(G, buildings, custom_bounds=None):
    # Step 1: Create a MultiPolygon for all building geometries
    all_shadows = MultiPolygon([building for building in buildings['geometry'] if building is not None])

    # Step 2: Validate and fix invalid geometries
    all_shadows = all_shadows.buffer(0) if not all_shadows.is_valid else all_shadows

    # Step 3: Merge all shadow and building polygons into a single MultiPolygon, ignoring overlaps
    combined_geometry = unary_union([all_shadows])

    # Step 4: Iterate over all the paths in the graph G and calculate the shadow/building coverage
    covered_lengths = []
    total_lengths = []

    # Create a larger figure
    fig, ax = plt.subplots(figsize=(20, 20))

    # Plot buildings (as shadow proxies)
    buildings.plot(ax=ax, color='orange', alpha=0.7, edgecolor='black')

    # Plot the graph with all paths using osmnx
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color="gray", edge_linewidth=1)

    for u, v, edge in G.edges(data=True):
        path = edge.get('geometry')
        if path is not None and isinstance(path, (LineString, MultiLineString)):
            if isinstance(path, MultiLineString):
                path = linemerge(path)  # Merge MultiLineString into LineString
            
            # Step 5: Find the intersection of the path with the combined geometry
            intersection = combined_geometry.intersection(path)

            # Calculate the length of the path and the covered part
            total_path_length = path.length
            covered_path_length = intersection.length if not intersection.is_empty else 0

            # Store the lengths for further analysis
            covered_lengths.append(covered_path_length)
            total_lengths.append(total_path_length)

            # Plot the path with a larger line width
            x, y = path.xy
            ax.plot(x, y, color='gray', linestyle='-', linewidth=2, alpha=0.7)

            # Plot the covered portion of the path in red with a larger line width
            if not intersection.is_empty and isinstance(intersection, LineString):
                x, y = intersection.xy
                ax.plot(x, y, color='red', linestyle='-', linewidth=3, alpha=0.9)

    # Step 6: Calculate the percentage of each path covered by shadow or building
    coverage_percentages = [(covered / total) * 100 if total > 0 else 0 for covered, total in zip(covered_lengths, total_lengths)]

    # Output the results for each path
    for edge, coverage in zip(G.edges(data=True), coverage_percentages):
        u, v, data = edge
        print(f"Edge {u}-{v}: {coverage:.2f}% covered by shadow/buildings")

    # Set custom bounds if specified
    if custom_bounds:
        ax.set_xlim([custom_bounds[0], custom_bounds[2]])
        ax.set_ylim([custom_bounds[1], custom_bounds[3]])

   

    

# Example usage
# analyze_and_plot_coverage(G, buildings)



# Usage Example
# analyze_and_plot_coverage(G, buildings)





    # # Step 6: Plot all the buildings, shadows, and paths
    # fig, ax = plt.subplots(figsize=(10, 10))

    # # Plot all buildings
    # buildings_gdf = gpd.GeoSeries(all_buildings)
    # buildings_gdf.plot(ax=ax, color='lightgrey', edgecolor='black', alpha=0.7, label='Buildings')

    # # Plot all shadows
    # shadows_gdf = gpd.GeoSeries(all_shadows)
    # shadows_gdf.plot(ax=ax, color='darkgrey', alpha=0.5, label='Shadows')

    # # Plot all paths from the graph G
    # for i, edge in enumerate(G.edges(data=True)):
    #     u, v, data = edge
    #     path = data.get('geometry')
    #     if path is not None and isinstance(path, LineString):
    #         x, y = path.xy
    #         ax.plot(x, y, color='blue', linewidth=2, label='Path' if i == 0 else "")

    # # Add legend and labels
    # ax.set_title('Buildings, Shadows, and Paths')
    # ax.set_xlabel('Longitude')
    # ax.set_ylabel('Latitude')
    # ax.legend()
    # plt.show()
