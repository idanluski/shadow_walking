from shapely.affinity import translate
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import scale, rotate

def calculate_shadow_weight(edge, shadows):
    edge_geom = edge['geometry']
    shadowed_length = 0

    for shadow in shadows['shadow_geometry']:
        if edge_geom.intersects(shadow):
            shadowed_length += edge_geom.intersection(shadow).length

    return shadowed_length / edge_geom.length  # Fraction of edge in shadow

def project_shadow(building, azimuth, altitude):
    height = float(building['height'])  # Use building height in meters
    footprint = building['geometry']  # Original building footprint
    
    # Extract scalar value from altitude if it's a pd.Series
    altitude_value = altitude.values[0] if isinstance(altitude, pd.Series) else altitude
    azimuth = azimuth.iloc[0] if isinstance(azimuth, pd.Series) else azimuth

    # Calculate shadow length using the altitude value
    shadow_length = height / max(0.1, np.tan(np.radians(altitude_value)))

    # If no shadow length (e.g., sun is directly overhead or negative), return the footprint itself
    if shadow_length <= 0:
        return footprint

    # Calculate the azimuth direction as unit vector
    azimuth_radians = np.radians(azimuth)

    # Reverse the signs of dx and dy to cast the shadow in the opposite direction
    dx = -shadow_length * np.sin(azimuth_radians)  # East-West (x-axis)
    dy = -shadow_length * np.cos(azimuth_radians)  # North-South (y-axis)

   
    # Translate footprint to create the shadow polygon
    if isinstance(footprint, (Polygon, MultiPolygon)):
        if footprint.is_empty:
            print("Warning: Empty geometry for building.")
            return footprint
        
        # Translate the building footprint to the shadow position
        #shadow = translate(footprint, xoff=dx, yoff=dy)
        shadow = create_shadow_polygon(footprint,dx,dy)
        # Combine the building footprint and the shadow to ensure continuity
        extended_polygon = footprint.union(shadow)
        
        print(f"Building Height: {height}, Altitude: {altitude_value}, Calculated Shadow Length: {shadow_length}")
        print(f"Azimuth: {azimuth}, Azimuth (radians): {azimuth_radians}")
        print(f"Calculated dx: {dx}, dy: {dy}, type(dx): {type(dx)}, type(dy): {type(dy)}")

        return extended_polygon
    else:
        raise ValueError(f"Invalid geometry type for footprint: {type(footprint)}")

def generate_stretched_shadow(building, azimuth, altitude):
    height = float(building['height'])  # Use building height in meters
    footprint = building['geometry']  # Original building footprint

    # Extract scalar value from altitude if it's a pd.Series
    altitude_value = altitude.values[0] if isinstance(altitude, pd.Series) else altitude
    azimuth = azimuth.iloc[0] if isinstance(azimuth, pd.Series) else azimuth

    # Calculate shadow length using the altitude value
    shadow_length = height / max(0.1, np.tan(np.radians(altitude_value)))

    # If no shadow length (e.g., sun is directly overhead or negative), return None
    if shadow_length <= 0:
        return None

    # Calculate stretch factor
    stretch_factor = shadow_length / height  # Stretch based on shadow length relative to height

    # Rotate the building footprint to align with the azimuth
    azimuth_radians = np.radians(azimuth)
    rotated_footprint = rotate(footprint, angle=-azimuth, origin='center', use_radians=False)

    # Scale the rotated footprint to simulate the stretching effect
    stretched_shadow = scale(rotated_footprint, xfact=1, yfact=stretch_factor, origin='center')

    # Translate the stretched shadow along the azimuth direction
    dx = -shadow_length * np.sin(azimuth_radians)
    dy = -shadow_length * np.cos(azimuth_radians)
    translated_shadow = translate(stretched_shadow, xoff=dx, yoff=dy)

    return translated_shadow

def convert_geodata(building):
    return gpd.GeoDataFrame(building)



def create_shadow_polygon(building, dx, dy):
    # Assuming `building` is a Polygon, get the exterior coordinates
    exterior_coords = list(building.exterior.coords)
    shadow_coords = [(x + dx, y + dy) for x, y in exterior_coords]
    return Polygon(shadow_coords)