import os
import numpy as np
import rasterio
from tqdm import tqdm

def cloud_mask(image_data, blue_band, swir_band=None, blue_thresh=0.3, swir_thresh=0.3):
    """
    Cloud mask based on thresholding blue (and optionally SWIR) band.
    For 3-band images (e.g., RGB), swir_band can be None, mask only on blue.
    """
    blue = image_data[blue_band]
    if swir_band is not None and swir_band < image_data.shape[0]:
        swir = image_data[swir_band]
        cloud_pixels = (blue > blue_thresh) & (swir > swir_thresh)
    else:
        cloud_pixels = blue > blue_thresh
    return cloud_pixels

raw_folder = '/Volumes/SSD/Proj_Terra/data/raw'
output_folder = '/Volumes/SSD/Proj_Terra/data/cloud_masked'
os.makedirs(output_folder, exist_ok=True)

files = [f for f in os.listdir(raw_folder) if (f.endswith('.tiff') or f.endswith('.tif')) and not f.startswith('._')]

for file in tqdm(files, desc='Cloud masking images'):
    file_path = os.path.join(raw_folder, file)
    try:
        with rasterio.open(file_path) as src:
            image = src.read()  # Read all bands
            profile = src.profile

            # Determine band indices: blue usually band 2 in RGB, 0-based indexing
            # Adjust swir_band if more bands exist; else None
            blue_band = 2 if image.shape[0] >= 3 else 0
            swir_band = 4 if image.shape[0] > 4 else None

            cloud_mask_arr = cloud_mask(image, blue_band, swir_band)

            masked_image = image.copy()
            nodata_val = profile.get('nodata', 0) or 0
            for b in range(masked_image.shape[0]):
                band = masked_image[b]
                band[cloud_mask_arr] = nodata_val
                masked_image[b] = band

            profile.update(dtype=rasterio.float32)

            output_path = os.path.join(output_folder, file)
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(masked_image.astype(rasterio.float32))
    except Exception as e:
        print(f"Skipping file {file} due to error: {e}")

print("Cloud masked images saved to folder:", output_folder)
