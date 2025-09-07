import os
import numpy as np
import rasterio
from numpy.ma import masked_invalid
from scipy.ndimage import median_filter
import matplotlib.pyplot as plt


def read_raster(path):
    with rasterio.open(path) as src:
        data = src.read(1)
        meta = src.meta
    return data, meta


def write_raster(data, meta, path):
    meta.update(dtype=rasterio.uint8, count=1)
    with rasterio.open(path, 'w', **meta) as dst:
        dst.write(data.astype(rasterio.uint8), 1)


def compute_anomaly(data, baseline):
    data_masked = masked_invalid(data)
    baseline_masked = masked_invalid(baseline)
    anomaly = np.abs(data_masked - baseline_masked) / (baseline_masked + 1e-6)
    return anomaly.filled(0)


def create_label_mask(anomaly, threshold):
    label = (anomaly > threshold).astype(np.uint8)
    return median_filter(label, size=3)


def process_and_save_for_date(date_folder_path, output_base_path):
    ndvi_path = os.path.join(date_folder_path, os.path.basename(date_folder_path) + '_NDVI.tif')
    evi_path = os.path.join(date_folder_path, os.path.basename(date_folder_path) + '_EVI.tif')
    ndwi_path = os.path.join(date_folder_path, os.path.basename(date_folder_path) + '_NDWI.tif')

    if not (os.path.isfile(ndvi_path) and os.path.isfile(evi_path) and os.path.isfile(ndwi_path)):
        print(f"Missing NDVI, EVI or NDWI file in {date_folder_path}. Skipping.")
        return

    ndvi, meta = read_raster(ndvi_path)
    evi, _ = read_raster(evi_path)
    ndwi, _ = read_raster(ndwi_path)

    # Compute spatial median baseline as proxy
    ndvi_baseline = median_filter(ndvi, size=15)
    evi_baseline = median_filter(evi, size=15)
    ndwi_baseline = median_filter(ndwi, size=15)

    # Calculate anomaly maps
    ndvi_anomaly = compute_anomaly(ndvi, ndvi_baseline)
    evi_anomaly = compute_anomaly(evi, evi_baseline)
    ndwi_anomaly = compute_anomaly(ndwi, ndwi_baseline)

    # Thresholds for anomaly detection (tune as needed)
    ndvi_thres = 0.3
    evi_thres = 0.3
    ndwi_thres = 0.3

    # Create binary anomaly masks
    ndvi_mask = create_label_mask(ndvi_anomaly, ndvi_thres)
    evi_mask = create_label_mask(evi_anomaly, evi_thres)
    ndwi_mask = create_label_mask(ndwi_anomaly, ndwi_thres)

    # Refine pest/disease risk mask by removing environmental stress areas
    refined_pest_mask = np.logical_and(ndvi_mask == 1,
                                       np.logical_not(np.logical_or(evi_mask == 1, ndwi_mask == 1))).astype(np.uint8)

    # Save refined mask
    date_folder_name = os.path.basename(date_folder_path)
    save_dir = os.path.join(output_base_path, 'PestRefinedData')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'refined_pest_mask_{date_folder_name}.tif')

    write_raster(refined_pest_mask, meta, save_path)
    print(f'Saved refined pest/disease risk mask: {save_path}')


def main(base_normalized_path):
    # Output directory base
    output_base_path = base_normalized_path  # You may change this if needed

    date_folders = [os.path.join(base_normalized_path, f) for f in os.listdir(base_normalized_path)
                    if os.path.isdir(os.path.join(base_normalized_path, f)) and f.startswith('tanjavur_')]

    for folder in sorted(date_folders):
        process_and_save_for_date(folder, output_base_path)


if __name__ == '__main__':
    normalized_base_path = '/Volumes/SSD/Proj_Terra/data/normalized/'
    main(normalized_base_path)