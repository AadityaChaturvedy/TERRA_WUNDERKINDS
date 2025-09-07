import os
import rasterio
from rasterio.transform import from_bounds

input_dir = 'tanjavur_sentinel_downloads'
output_dir = 'tanjavur_georef'
os.makedirs(output_dir, exist_ok=True)

bbox_coords = [79, 10.57, 79.047, 10.617]  # Known bounding box (min_lon, min_lat, max_lon, max_lat)
size = (2023, 2058)  # Known image size (width, height)
crs = 'EPSG:4326'

def add_georeferencing(input_path, output_path, bbox, size, crs):
    with rasterio.open(input_path) as src:
        img = src.read()  # Read all bands
        profile = src.profile

    transform = from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], size[0], size[1])

    profile.update(
        driver='GTiff',
        height=img.shape[1],
        width=img.shape[2],
        count=img.shape[0],
        crs=crs,
        transform=transform
    )

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(img)

    print(f"Saved georeferenced TIFF: {output_path}")

    # Delete original file after georeferencing
    os.remove(input_path)
    print(f"Deleted original file: {input_path}")

def batch_georeference(input_folder, output_folder, bbox, size, crs):
    for filename in os.listdir(input_folder):
        if filename.endswith('.tiff') or filename.endswith('.tif'):
            input_path = os.path.join(input_folder, filename)
            base, ext = os.path.splitext(filename)
            output_path = os.path.join(output_folder, f"{base}{ext}")
            add_georeferencing(input_path, output_path, bbox, size, crs)

if __name__ == '__main__':
    batch_georeference(input_dir, output_dir, bbox_coords, size, crs)