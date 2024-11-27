from shapely.affinity import translate
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

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
    #shadow_length *= 2#try other day or other shadow
    # If no shadow length (e.g., sun is directly overhead or negative), return the footprint itself
    if shadow_length <= 0:
        return footprint

    # Calculate the azimuth direction as unit vector
    azimuth_radians = np.radians(azimuth)

    dx = -shadow_length * np.sin(azimuth_radians)  # East-West (x-axis)
    dy = -shadow_length * np.cos(azimuth_radians)  # North-South (y-axis)

    # Translate footprint to create the shadow polygon
    if isinstance(footprint, (Polygon, MultiPolygon)):
        if footprint.is_empty:
            print("Warning: Empty geometry for building.")
            return footprint
        
        # Translate the building footprint to the shadow position
        shadow = translate(footprint, xoff=dx, yoff=dy)
        #shadow = translate(footprint)

        # Union of the original footprint and the shadow to extend the polygon
        extended_polygon = footprint.union(shadow)
        print(f"Building Height: {height}, Altitude: {altitude_value}, Calculated Shadow Length: {shadow_length}")
        print(f"Azimuth: {azimuth}, Azimuth (radians): {azimuth_radians}")
        print(f"Calculated dx: {dx}, dy: {dy}, type(dx): {type(dx)}, type(dy): {type(dy)}")

        return extended_polygon
    else:
        raise ValueError(f"Invalid geometry type for footprint: {type(footprint)}")



def convert_geodata(building):
    return gpd.GeoDataFrame(building)
