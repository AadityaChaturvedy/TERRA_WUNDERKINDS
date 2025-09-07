import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Example original raster metadata (replace with your exact values or load from raster)
raster_height = 2058
raster_width = 2023
raster_transform = rasterio.Affine(1.0, 0.0, 79.0, 0.0, -1.0, 10.617)  # Example; use your real transform
raster_crs = "EPSG:4326"  # Use your raster CRS

# Initialize empty array for full raster prediction (all pixels)
full_prediction = np.zeros(raster_height * raster_width, dtype=np.uint8)

# Assign predictions to sampled pixels
full_prediction[sample_indices] = future_pred

# Reshape to 2D raster form
pred_raster = full_prediction.reshape((raster_height, raster_width))

# --- Export as GeoTIFF ---
out_tif = 'future_pest_risk_prediction.tif'
with rasterio.open(
    out_tif,
    'w',
    driver='GTiff',
    height=raster_height,
    width=raster_width,
    count=1,
    dtype=pred_raster.dtype,
    crs=raster_crs,
    transform=raster_transform,
) as dst:
    dst.write(pred_raster, 1)
print(f"Prediction raster saved as {out_tif}")

# --- Plot Raster ---
plt.figure(figsize=(10, 8))
plt.title('Predicted Pest Risk Map (Future Time Step)')
plt.imshow(pred_raster, cmap='Reds', interpolation='none')
plt.colorbar(label='Pest Risk (0=No, 1=Yes)')
plt.xlabel('Pixel X')
plt.ylabel('Pixel Y')
plt.show()