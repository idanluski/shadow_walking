from shapely.affinity import translate
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.affinity import scale, rotate
from shapely.affinity import scale, rotate, translate
from shapely.validation import make_valid
import numpy as np
import shapely.errors


def calculate_shadow_weight(edge, shadows):
    edge_geom = edge['geometry']
    shadowed_length = 0

    for shadow in shadows['shadow_geometry']:
        if edge_geom.intersects(shadow):
            shadowed_length += edge_geom.intersection(shadow).length

    return shadowed_length / edge_geom.length  # Fraction of edge in shadow

def project_shadow(building, azimuth, altitude):
    """
    Creates a shadow polygon for a building by calling the shadow generation function.
    """
    height = float(building['height'])  # Use building height in meters
    footprint = building['geometry']  # Original building footprint

    # Extract scalar values for altitude and azimuth
    altitude_value = altitude.values[0] if isinstance(altitude, pd.Series) else altitude
    azimuth = azimuth.iloc[0] if isinstance(azimuth, pd.Series) else azimuth

    # Calculate shadow length using the altitude value
    shadow_length = height / max(0.1, np.tan(np.radians(altitude_value)))

    # If no shadow length (e.g., sun is directly overhead or negative), return the footprint
    if shadow_length <= 0:
        return footprint

    # Ensure the footprint is valid
    if isinstance(footprint, (Polygon, MultiPolygon)):
        if footprint.is_empty:
            print("Warning: Empty geometry for building.")
            return footprint

        # Call the shadow generation function
        shadow_polygon = generate_distorted_shadow(building, azimuth, altitude)
        if shadow_polygon is None:
            return footprint  # If no shadow could be generated, return the original footprint

        # Combine the building footprint and the shadow to ensure continuity
        extended_polygon = footprint.union(shadow_polygon)

        print(f"Building Height: {height}, Altitude: {altitude_value}, Shadow Length: {shadow_length}")
        print(f"Azimuth: {azimuth}, Shadow Polygon Created: {shadow_polygon is not None}")

        return extended_polygon
    else:
        raise ValueError(f"Invalid geometry type for footprint: {type(footprint)}")

def generate_distorted_shadow(building, azimuth, altitude):
    """
    Generate a realistically distorted shadow for a building polygon based on sun altitude and azimuth.
    Includes the union of the building and shadow to fill gaps.
    """

    

    height = float(building['height'])  # Use building height in meters
    footprint = building['geometry']  # Original building footprint

    # Inflate the building footprint slightly to ensure overlap with shadow
    inflated_footprint = footprint.buffer(0.5)  # Inflate by 0.5 meters

    # Extract scalar values
    altitude_value = altitude.values[0] if isinstance(altitude, pd.Series) else altitude
    azimuth = azimuth.iloc[0] if isinstance(azimuth, pd.Series) else azimuth

    # Calculate shadow length using the altitude value
    shadow_length = height / max(0.1, np.tan(np.radians(altitude_value)))

    # If no shadow length (e.g., sun is directly overhead or negative), return None
    if shadow_length <= 0:
        return None

    # Calculate shadow vector based on azimuth, negated to ensure the shadow is cast away from the building
    azimuth_radians = np.radians(azimuth)
    shadow_vector = np.array([-np.sin(azimuth_radians), -np.cos(azimuth_radians)]) * shadow_length

    # Ensure the geometry is valid
    if isinstance(footprint, (Polygon, MultiPolygon)):
        if footprint.is_empty:
            print("Warning: Empty geometry for building.")
            return footprint

        # Get the coordinates of the polygon's exterior
        original_coords = list(footprint.exterior.coords)
        distorted_coords = []

        # Find the centroid of the building for reference
        centroid = np.mean(np.array(original_coords), axis=0)

        for x, y in original_coords:
            # Calculate the relative position of the vertex to the shadow vector
            vertex_vector = np.array([x, y]) - centroid
            projection = np.dot(vertex_vector, shadow_vector) / np.linalg.norm(shadow_vector)

            # Stretch vertices farther away from the shadow base
            if projection >= 0:  # Vertices on the far side of the shadow
                stretch_factor = 0.5 + (projection / (2 * height))  # Scale down the stretch factor
                displacement = shadow_vector * stretch_factor
            else:  # Vertices closer to the shadow base
                displacement = shadow_vector * 0.2  # Increase displacement for near-side vertices

            # Apply the displacement to the vertex
            new_x = x + displacement[0]
            new_y = y + displacement[1]
            distorted_coords.append((new_x, new_y))

        # Create a new polygon for the shadow
        shadow_polygon = Polygon(distorted_coords)

        # Buffer the shadow polygon slightly to ensure overlap
        buffered_shadow = shadow_polygon.buffer(0.5)

        # Combine the inflated building footprint and the buffered shadow to fill gaps
        combined_polygon = unary_union([inflated_footprint, buffered_shadow])

        # Print information for debugging or verification
        print(f"Building Height: {height}, Altitude: {altitude_value}, Shadow Length: {shadow_length}")
        print(f"Azimuth: {azimuth}, Shadow Vector: {shadow_vector}")

        if isinstance(combined_polygon, Polygon):
            # Create a new Polygon without holes
            filled_polygon = Polygon(combined_polygon.exterior)
        elif combined_polygon.geom_type == 'MultiPolygon':
            # If there are multiple polygons, iterate and remove holes from each
            filled_polygons = []
            for poly in combined_polygon:
                filled_polygons.append(Polygon(poly.exterior))
            filled_polygon = gpd.GeoSeries(filled_polygons).unary_union
        return filled_polygon
    else:
        raise ValueError(f"Invalid geometry type for footprint: {type(footprint)}")

    
    
def convert_geodata(building):
    return gpd.GeoDataFrame(building)



def create_shadow_polygon(building, dx, dy):
    # Assuming `building` is a Polygon, get the exterior coordinates
    exterior_coords = list(building.exterior.coords)
    shadow_coords = [(x + dx, y + dy) for x, y in exterior_coords]
    return Polygon(shadow_coords)



