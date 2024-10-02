import geopandas as gpd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import pandas as pd
import contextily as ctx
from typing import Literal
import os

ZOOM_OUT_FACTOR = 0.8 # 80%
TILE_SET: Literal['google', 'openstreetmap'] = 'openstreetmap'

LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT = {'Brisbane City', 'Logan City', 'Moreton Bay City'}

suburb_df = gpd.read_file("doc.kml")

def get_output_path(lga: str, locality: str) -> str:
    save_directory = os.path.join('output', lga)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    save_path = os.path.join(save_directory, f'{locality}.jpg')
    return save_path


# Function to extract locality and lga
def extract_locality_lga(html_description):
    soup = BeautifulSoup(html_description, 'html.parser')
    
    # Find all rows in the table
    rows = soup.find_all('tr')
    
    # Initialize variables
    locality = None
    lga = None
    
    # Iterate over rows to find locality and lga
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            header = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            if header == 'locality':
                locality = value
            elif header == 'lga':
                lga = value
    
    return locality, lga

def get_zoom_level_from_distance(distance_meters: float) -> int:
    # Earth's circumference in meters (at the equator)
    earth_circumference_meters = 40075016.686

    # Loop through zoom levels from 0 to 21 (Google Maps max zoom)
    for zoom in range(0, 22):
        # Calculate tile width at this zoom level in meters
        tile_width_meters = earth_circumference_meters / (2 ** zoom)

        # If the distance is smaller than the tile width, this zoom level is good
        if tile_width_meters < distance_meters:
            return zoom

    return 0  # Default to zoom level 0 if no match found

# Apply the function to extract locality and LGA
suburb_df[['locality', 'lga']] = suburb_df['Description'].apply(lambda x: pd.Series(extract_locality_lga(x)))

for _, _, geometry, locality, lga in suburb_df.itertuples(index=False):
    # if locality != 'Anstead':
    #     continue

    if lga not in LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT:
        continue

    # if os.path.exists(get_output_path(lga, locality)):
    #     continue

    # Assign the selected suburb's geometry
    selected_suburb = gpd.GeoDataFrame(geometry=[geometry], crs=suburb_df.crs)

    # Reproject to Web Mercator (EPSG 3857) for compatibility with the basemap
    selected_suburb = selected_suburb.to_crs(epsg=3857)

    # Plot the selected suburb with a solid fill color
    ax = selected_suburb.plot(figsize=(5, 5), alpha=1.0, edgecolor='k', color='white')

    # Get current bounds and expand them to zoom out
    minx, miny, maxx, maxy = selected_suburb.total_bounds
    
    # Calculate expanded bounds
    x_range = maxx - minx
    y_range = maxy - miny
    
    # Expand the bounds by the zoom-out factor
    minx -= x_range * ZOOM_OUT_FACTOR
    maxx += x_range * ZOOM_OUT_FACTOR
    miny -= y_range * ZOOM_OUT_FACTOR
    maxy += y_range * ZOOM_OUT_FACTOR

    # Determine the center and the maximum extent
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    max_extent = max(maxx - minx, maxy - miny) / 2  # Half of the largest extent

    # Set new axis limits to ensure the plot is square
    ax.set_xlim(center_x - max_extent, center_x + max_extent)
    ax.set_ylim(center_y - max_extent, center_y + max_extent)

    zoom_level = get_zoom_level_from_distance(maxx - minx)

    # Zoom out by reducing the zoom level
    if TILE_SET == 'google':
        google_maps_tile_url = "http://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
        ctx.add_basemap(ax, source=google_maps_tile_url, zoom=zoom_level)
    elif TILE_SET == 'openstreetmap':
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution='')

    # Hide axes
    ax.set_axis_off()

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Save the plot to an image file
    plt.savefig(get_output_path(lga, locality), bbox_inches='tight', pad_inches=0, dpi=150, transparent=False)
    plt.close()

    print(f"Map for {locality}, {lga} created!")

