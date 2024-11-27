import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd

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


