import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon, Polygon, LineString, MultiLineString, GeometryCollection
from shapely.ops import unary_union
import plot as pl
from shapely.ops import linemerge
import re 


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



def analyze_coverage(G, shadow_gdf,buildings, custom_bounds=None):
    # Ensure CRS consistency before analyzing paths
    graph_crs = G.graph.get('crs', None)
    if graph_crs is None:
        raise ValueError("Graph G does not have a defined CRS. Please make sure it has a valid CRS.")

    # Ensure both datasets are in the same CRS
    if shadow_gdf.crs != graph_crs:
        shadow_gdf = shadow_gdf.to_crs(graph_crs)

    # Create a larger figure for visualization
    fig, ax = plt.subplots(figsize=(15, 15), dpi=100)
    fig.tight_layout()

    # Plot buildings (as shadow proxies)
    shadow_gdf.plot(ax=ax, color='darkgrey', alpha=0.7, label='Shadows')

    buildings.plot(ax=ax, color='orange', alpha=0.7, edgecolor='black')

    # Plot the graph with all paths using osmnx
    ox.plot_graph(G, ax=ax, show=False, close=False, edge_color="gray", edge_linewidth=1)

    for u, v, key, edge in G.edges(keys=True, data=True):
        path = edge.get('geometry')

    
        if path is not None and isinstance(path, (LineString, MultiLineString)):
            if isinstance(path, MultiLineString):
                path = linemerge(path)  # Merge MultiLineString into LineString

            # Validate and buffer the path slightly to improve intersection accuracy
            if not path.is_valid:
                path = path.buffer(0)

            # Step 6: Find the intersection of the path with the combined geometry
            intersection = shadow_gdf.unary_union.intersection(path)

            # Step 7: Calculate the covered length
            covered_path_length = 0
            if isinstance(intersection, LineString):
                covered_path_length = intersection.length
            elif isinstance(intersection, MultiLineString):
                covered_path_length = sum(line.length for line in intersection.geoms)
            elif isinstance(intersection, GeometryCollection):
                covered_path_length = sum(geom.length for geom in intersection.geoms if isinstance(geom, (LineString, MultiLineString)))

            # Calculate the length of the path
            total_path_length = path.length

            # Calculate coverage percentage
            coverage_percentage = (covered_path_length / total_path_length) * 100 if total_path_length > 0 else 0

            # Add the coverage percentage as an attribute to the edge
            G[u][v][key]['shadow_coverage'] = coverage_percentage

            # Plot the path
            x, y = path.xy
            ax.plot(x, y, color='gray', linestyle='-', linewidth=2, alpha=0.7)

            # Plot the covered portion of the path in red
            if not intersection.is_empty:
                if isinstance(intersection, LineString):
                    x, y = intersection.xy
                    ax.plot(x, y, color='red', linestyle='-', linewidth=3, alpha=0.9)
                elif isinstance(intersection, MultiLineString):
                    for line in intersection.geoms:
                        x, y = line.xy
                        ax.plot(x, y, color='red', linestyle='-', linewidth=3, alpha=0.9)

    # Step 8: Output the results for each path
    for u, v, key, data in G.edges(keys=True, data=True):
        coverage = data.get('shadow_coverage', 0)
        print(f"Edge {u}-{v}: {coverage:.2f}% covered by shadow/buildings")



        
        if not path.is_valid:
            path = path.buffer(0)  # Fix invalid geometry

        intersection = shadow_gdf.unary_union.intersection(path)
        
     # Adding numeric house number labels to buildings if available
    for idx, building in buildings.iterrows():
        housenumber = building.get('addr:housenumber', None)

        if pd.notna(housenumber):
            # Extract only the numeric part of the house number
            numeric_housenumber = ''.join(re.findall(r'\d+', str(housenumber)))

            if numeric_housenumber:  # Only label if a numeric part exists
                centroid = building.geometry.centroid
                ax.text(centroid.x, centroid.y, numeric_housenumber, fontsize=8, color='black', alpha=0.9, ha='center')

    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()

    # Add a margin to zoom out (e.g., 10% margin)
    margin = 0.1  # 10% margin
    x_margin = (x_max - x_min) * margin
    y_margin = (y_max - y_min) * margin

    # Set new limits with the added margin
    ax.set_xlim(x_min - x_margin, x_max + x_margin)
    ax.set_ylim(y_min - y_margin, y_max + y_margin)



    # Add title and labels
    plt.title("Buildings, Shadows, and Paths at Ben Gurion University", fontsize=20)
    plt.xlabel("Longitude", fontsize=16)
    plt.ylabel("Latitude", fontsize=16)

    # Improve visibility of plot grid and background
    ax.grid(True, linestyle='--', linewidth=0.5)

    # Show the plot
    plt.tight_layout()
    plt.show()



def handel_bad_path(G):
    """
    Add geometry if missing to the path in G
    """
    for u, v, key, edge in G.edges(keys=True, data=True):
        path = edge.get('geometry')


        # Check if geometry is missing
        if path is None:
            # Get the coordinates of the start and end nodes
            x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
            x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
            
            # Create a LineString geometry from the coordinates
            path = LineString([(x1, y1), (x2, y2)])
            edge['geometry']= path