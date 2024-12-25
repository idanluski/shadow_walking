import geopandas as gpd
from SunLocation import SunLocation
from Open_Street_Map import Open_Street_Map
from Class_Shadow import Class_Shadow

PLOT = True
sunloc = SunLocation()
azimuth = sunloc.azimuth
altitude = sunloc.altitude


osm_object = Open_Street_Map()

print("\nBuilding Levels:")
print(osm_object.Buildings['levels'])
print(osm_object.Buildings.crs)

# Reproject buildings to a suitable CRS (e.g., UTM zone 36N for Israel)
osm_object.Buildings = osm_object.Buildings.to_crs(epsg=32636)  # Use EPSG code corresponding to UTM zone


# Step 3: Calculate the area in square meters
osm_object.Buildings['area'] = osm_object.Buildings['geometry'].area

# Ensure height column exists
if 'height' not in osm_object.Buildings.columns:
    osm_object.Buildings['height'] = 0  # Initialize with 0 if not present

# Replace NaN values in height with 0
osm_object.Buildings['height'] = osm_object.Buildings['height'].fillna(0)

# Debug: Print buildings with updated height values
print("\nBuildings with Updated Heights:")
print(osm_object.Buildings[['height', 'geometry']])

# Convert geometry column to GeoDataFrame format if needed
Class_Shadow.convert_geodata(osm_object.Buildings)

# buildings = osm_object.Buildings.to_crs(epsg=32636)
osm_object.Buildings['shadow_geometry'] = osm_object.Buildings.apply(lambda b: Class_Shadow.generate_distorted_shadow(b, azimuth, altitude), axis=1)

osm_object.buildings_with_only_shadows = osm_object.Buildings.copy()
osm_object.buildings_with_only_shadows = osm_object.buildings_with_only_shadows.to_crs(epsg=32636)
osm_object.buildings_with_only_shadows['shadow_only_geometry'] = osm_object.buildings_with_only_shadows.apply(
    lambda row: row['shadow_geometry'].difference(row['geometry']) if row['shadow_geometry'] is not None else None,
    axis=1
)
shadow_only_gdf = gpd.GeoDataFrame(osm_object.buildings_with_only_shadows, geometry='shadow_only_geometry')

# Plot only the shadow areas in red with increased transparency
shadow_gdf = gpd.GeoDataFrame(osm_object.Buildings, geometry='shadow_geometry')
# Set the initial CRS (replace 'EPSG:4326' with your known CRS if different)
shadow_gdf = shadow_gdf.set_crs(epsg=32636)

# Now you can convert to your target CRS
shadow_gdf = shadow_gdf.to_crs(epsg=32636)

print("-------------------------------------------------")

Class_Shadow.analyze_coverage(osm_object.G, shadow_gdf, osm_object.Buildings, osm_object.combined_bounds)
Class_Shadow.analyze_and_plot_coverage(osm_object.G, osm_object.Buildings, osm_object.combined_bounds)
