import folium
from folium import features
import os
from pathlib import Path

# Define the bounding box coordinates (longitude and latitude)
min_lon, min_lat, max_lon, max_lat = 79.0, 10.57, 79.047, 10.617

# Create folium Map centered at bounding box center
center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]
m = folium.Map(location=center, zoom_start=13)

# Add Stamen Terrain basemap with attribution
folium.TileLayer(
    tiles='https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
    attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap contributors',
    name='Stamen Terrain',
    control=True
).add_to(m)

# Add bounding box rectangle
bounds = [(min_lat, min_lon), (max_lat, max_lon)]
folium.Rectangle(
    bounds=bounds,
    color='red',
    weight=3,
    fill=False,
    popup='Pest Risk Area'
).add_to(m)

# Folder containing GeoJSON files
geojson_folder = Path('/Volumes/SSD/Proj_Terra/PEST/debug_pest_risk_vectors')

def style_function(feature):
    return {
        'fillColor': 'red',
        'color': 'red',
        'weight': 2,
        'fillOpacity': 0.4,
    }

# Load and add all GeoJSON files as separate layers with toggles
for geojson_file in sorted(geojson_folder.glob('pest_risk_*.geojson')):
    layer_name = geojson_file.stem.replace('pest_risk_', '')  # extract date as name
    folium.GeoJson(
        str(geojson_file),
        name=f"Pest Risk {layer_name}",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=['raster_val'], aliases=['Risk:'])
    ).add_to(m)

# Add layer control to toggle each date's pest risk polygon
folium.LayerControl(collapsed=False).add_to(m)

# Save map to HTML
output_html = 'pest_risk_multiple_dates_map.html'
m.save(output_html)
print(f"Map with multiple date overlays saved as {output_html}")
