import os
import numpy as np
import rasterio
from tqdm import tqdm

def cloud_mask(image_data, blue_band=0, swir_band=7, blue_thresh=0.2, swir_thresh=0.3):
    """
    Simple cloud mask based on reflectance thresholds for Blue and SWIR1 bands.
    Returns a boolean mask where cloud pixels are True.
    """
    blue = image_data[blue_band]
    swir = image_data[swir_band]
    cloud_pixels = (blue > blue_thresh) & (swir > swir_thresh)
    return cloud_pixels

def safe_divide(a, b):
    b = np.where(b == 0, 1e-5, b)
    return a / b

def calculate_indices(img):
    B02 = img[0].astype(float)  # Blue
    B03 = img[1].astype(float)  # Green
    B04 = img[2].astype(float)  # Red
    B08 = img[6].astype(float)  # NIR
    B11 = img[7].astype(float)  # SWIR1

    NDVI = safe_divide(B08 - B04, B08 + B04)
    NDVI[(B08 == 0) | (B04 == 0)] = np.nan

    EVI = 2.5 * safe_divide(B08 - B04, B08 + 6 * B04 - 7.5 * B02 + 1)
    EVI[(B08 == 0) | (B04 == 0) | (B02 == 0)] = np.nan

    NDWI = safe_divide(B03 - B11, B03 + B11)
    NDWI[(B03 == 0) | (B11 == 0)] = np.nan

    return NDVI, EVI, NDWI

def save_geotiff(data, out_path, profile, transform, crs):
    height, width = data.shape
    profile.update(
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=rasterio.float32,
        transform=transform,
        crs=crs,
        nodata=np.nan
    )
    with rasterio.open(out_path, 'w', **profile) as dst:
        dst.write(data.astype(rasterio.float32), 1)

def process_file(file_path, output_base_folder):
    with rasterio.open(file_path) as src:
        image = src.read()  # Read all bands
        profile = src.profile
        transform = src.transform
        crs = src.crs

    cloud_mask_arr = cloud_mask(image)

    # Mask cloud pixels (set to nan) in all bands
    masked_img = image.astype(float)
    for b in range(masked_img.shape[0]):
        band = masked_img[b]
        band[cloud_mask_arr] = np.nan
        masked_img[b] = band

    ndvi, evi, ndwi = calculate_indices(masked_img)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_folder = os.path.join(output_base_folder, base_name)
    os.makedirs(output_folder, exist_ok=True)

    save_geotiff(ndvi, os.path.join(output_folder, f"{base_name}_NDVI.tif"), profile, transform, crs)
    save_geotiff(evi, os.path.join(output_folder, f"{base_name}_EVI.tif"), profile, transform, crs)
    save_geotiff(ndwi, os.path.join(output_folder, f"{base_name}_NDWI.tif"), profile, transform, crs)

    print(f"Processed and saved indices for {base_name}")

def main(raw_folder, output_base_folder):
    files = [f for f in os.listdir(raw_folder) if f.endswith('.tif') or f.endswith('.tiff')]
    for file in tqdm(files, desc="Processing raw images"):
        try:
            process_file(os.path.join(raw_folder, file), output_base_folder)
        except Exception as e:
            print(f"Error processing {file}: {e}")

if __name__ == "__main__":
    raw_data_folder = 'raw'  # Change if needed
    output_folder = 'index_outputs'
    main(raw_data_folder, output_folder)
