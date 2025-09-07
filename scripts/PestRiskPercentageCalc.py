import rasterio
import numpy as np


def calculate_pest_risk_percentage(risk_map_path):
    with rasterio.open(risk_map_path) as src:
        risk_data = src.read(1)
        # Mask no-data if defined
        valid_mask = risk_data != src.nodata if src.nodata is not None else np.ones_like(risk_data, dtype=bool)

        total_valid_pixels = np.sum(valid_mask)
        risk_pixels = np.sum(risk_data[valid_mask] == 1)

        pest_risk_percent = (risk_pixels / total_valid_pixels) * 100
        return pest_risk_percent


# Usage example
risk_image_path = "/Volumes/SSD/Proj_Terra/PEST/PestPredictedMap.tiff"
percent_risk = calculate_pest_risk_percentage(risk_image_path)
print(f"Pest Risk Percentage: {percent_risk:.2f}%")