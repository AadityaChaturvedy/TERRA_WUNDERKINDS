import rasterio
from rasterio.features import rasterize
import geopandas as gpd
import numpy as np

# Load your polygon shapefile with class attribute
shapefile = 'labels/field_boundaries.shp'
gdf = gpd.read_file(shapefile)

# Define output mask size, transform from reference image
ref_img = 'processed/tanjavur_2023-01-05/tanjavur_2023-01-05_NDVI.tif'
with rasterio.open(ref_img) as src:
    meta = src.meta.copy()
    transform = src.transform
    out_shape = (src.height, src.width)

# Prepare geometries and corresponding label values
shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['class_id']))

# Rasterize polygons to mask
mask = rasterize(
    shapes=shapes,
    out_shape=out_shape,
    transform=transform,
    fill=0,
    dtype=rasterio.uint8
)

# Save mask to file
mask_path = 'labels/tanjavur_2023-01-05_mask.tif'
meta.update({
    'count': 1,
    'dtype': rasterio.uint8
})

with rasterio.open(mask_path, 'w', **meta) as dst:
    dst.write(mask, 1)