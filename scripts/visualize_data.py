import rasterio
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# -----------------------------
# Bulletproof: avoid style file issues
# -----------------------------
# Force default matplotlib style without reading any external style files
matplotlib.rcParams.update(matplotlib.rcParamsDefault)


# -----------------------------
# Visualization function
# -----------------------------
def visualize_indices_and_label(ndvi_path, evi_path, ndwi_path, label_path=None):
    """
    Plots NDVI, EVI, NDWI rasters and optionally a label mask.

    Parameters:
        ndvi_path (str): Path to NDVI GeoTIFF
        evi_path (str): Path to EVI GeoTIFF
        ndwi_path (str): Path to NDWI GeoTIFF
        label_path (str, optional): Path to label mask GeoTIFF
    """
    n_plots = 4 if label_path else 3
    fig, axs = plt.subplots(1, n_plots, figsize=(6 * n_plots, 6))

    # Ensure axs is iterable
    if n_plots == 1:
        axs = [axs]

    # Helper to load raster and mask invalid values
    def load_raster(path):
        with rasterio.open(path) as src:
            return np.ma.masked_invalid(src.read(1))

    # NDVI
    ndvi = load_raster(ndvi_path)
    im0 = axs[0].imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
    axs[0].set_title('NDVI')
    axs[0].axis('off')
    fig.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)

    # EVI
    evi = load_raster(evi_path)
    im1 = axs[1].imshow(evi, cmap='RdYlGn', vmin=-1, vmax=1)
    axs[1].set_title('EVI')
    axs[1].axis('off')
    fig.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)

    # NDWI
    ndwi = load_raster(ndwi_path)
    im2 = axs[2].imshow(ndwi, cmap='Blues', vmin=-1, vmax=1)
    axs[2].set_title('NDWI')
    axs[2].axis('off')
    fig.colorbar(im2, ax=axs[2], fraction=0.046, pad=0.04)

    # Optional label mask
    if label_path:
        label = load_raster(label_path)
        im3 = axs[3].imshow(label, cmap='gray', vmin=0, vmax=1)
        axs[3].set_title('Label Mask')
        axs[3].axis('off')
        fig.colorbar(im3, ax=axs[3], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.show()


# -----------------------------
# Example usage: update your paths
# -----------------------------
visualize_indices_and_label(
    '/Volumes/SSD/Proj_Terra/data/processed/tanjavur_2023-01-05/tanjavur_2023-01-05_NDVI.tif',
    '/Volumes/SSD/Proj_Terra/data/processed/tanjavur_2023-01-05/tanjavur_2023-01-05_EVI.tif',
    '/Volumes/SSD/Proj_Terra/data/processed/tanjavur_2023-01-05/tanjavur_2023-01-05_NDWI.tif',
    '/Volumes/SSD/Proj_Terra/data/normalized/tanjavur_2023-01-05/tanjavur_2023-01-05_EVI.tif'
)