import rasterio
import numpy as np
import os
import glob

def generate_ndvi_label(ndvi_path, threshold=0.3, output_path=None):
    with rasterio.open(ndvi_path) as src:
        ndvi = src.read(1).astype(np.float32)
        ndvi = np.nan_to_num(ndvi, nan=0)
        label = (ndvi >= threshold).astype(np.uint8)

        if output_path:
            profile = src.profile
            profile.update(dtype=rasterio.uint8, count=1)

            # Remove nodata or fix for uint8 data type
            if 'nodata' in profile:
                nodata_value = profile['nodata']
                if isinstance(nodata_value, float) and np.isnan(nodata_value):
                    del profile['nodata']
                elif nodata_value is not None and (nodata_value < 0 or nodata_value > 255):
                    del profile['nodata']

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(label, 1)
            print(f"Saved label mask to {output_path}")
    return label


if __name__ == "__main__":
    base_processed_dir = "/Volumes/SSD/Proj_Terra/data/processed"
    base_label_dir = "/Volumes/SSD/Proj_Terra/data/labels"

    os.makedirs(base_label_dir, exist_ok=True)

    # Find all NDVI files recursively inside processed folder
    ndvi_files = glob.glob(os.path.join(base_processed_dir, '**', '*NDVI*.tif'), recursive=True)

    if not ndvi_files:
        print("No NDVI files found in processed data folder.")
    else:
        for ndvi_path in ndvi_files:
            # Extract date folder name from path: assuming structure ".../processed/date_folder/filename"
            parts = ndvi_path.split(os.sep)
            try:
                date_folder = parts[parts.index('processed') + 1]
            except (ValueError, IndexError):
                print(f"Cannot extract date folder from path: {ndvi_path}, skipping.")
                continue

            label_folder = os.path.join(base_label_dir, date_folder)
            label_file_name = f"{date_folder}_label.tif"
            output_path = os.path.join(label_folder, label_file_name)

            generate_ndvi_label(ndvi_path, threshold=0.3, output_path=output_path)
