import os
import time
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from datetime import datetime
from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    MimeType,
    SentinelHubRequest,
    SentinelHubCatalog,
)
import warnings

# ------------------- CONFIG -------------------
config = SHConfig()
config.instance_id = "3b4ab58e-afa2-4ea7-9ab2-42665d063bd9"
config.sh_client_id = "57239557-1374-4b9f-afa0-8fdfd70150bb"
config.sh_client_secret = "mWgfW9u3zcHkdDjo9A9YPSiGULftegMP"

bbox_coords = [79, 10.57, 79.047, 10.617]
bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)

size = (2023, 2058)
time_range = ("2023-01-01", "2025-09-05")
output_dir = "tanjavur_sentinel_downloads"
os.makedirs(output_dir, exist_ok=True)

evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B02","B03","B04","B05","B06","B07","B08","B11","B12"],
    output: { bands: 9, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [
    2.5 * sample.B02, 2.5 * sample.B03, 2.5 * sample.B04,
    2.5 * sample.B05, 2.5 * sample.B06, 2.5 * sample.B07,
    2.5 * sample.B08, 2.5 * sample.B11, 2.5 * sample.B12
  ];
}
"""


# ------------------- DOWNLOAD FUNCTION -------------------
def download_all_images():
    catalog = SentinelHubCatalog(config=config)

    # Search for Sentinel-2 L2A products
    search_iterator = catalog.search(
        DataCollection.SENTINEL2_L2A,
        bbox=bbox,
        time=time_range
    )

    all_items = list(search_iterator)
    all_timestamps = [datetime.fromisoformat(item['properties']['datetime']) for item in all_items]
    print(f"Found {len(all_timestamps)} images to download.")

    transform = from_bounds(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y, size[0], size[1])

    for idx, timestamp in enumerate(all_timestamps):
        date_str = timestamp.strftime('%Y-%m-%d')
        filename = os.path.join(output_dir, f"tanjavur_{date_str}.tiff")

        if os.path.exists(filename):
            print(f"Skipping {filename}, already downloaded.")
            continue

        print(f"Requesting data for date: {date_str} ({idx + 1}/{len(all_timestamps)})")

        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(date_str, date_str),
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=size,
            config=config,
        )

        # ----------------- RETRY LOGIC -----------------
        downloaded = False
        while not downloaded:
            try:
                # Suppress rate-limit warnings (we handle them manually)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")  # ignore all warnings for get_data
                    data = request.get_data()[0]

                data = np.squeeze(data)

                # Save georeferenced TIFF
                with rasterio.open(
                        filename,
                        'w',
                        driver='GTiff',
                        height=data.shape[0],
                        width=data.shape[1],
                        count=data.shape[2] if len(data.shape) > 2 else 1,
                        dtype=data.dtype,
                        crs='EPSG:4326',
                        transform=transform
                ) as dst:
                    if len(data.shape) > 2:
                        for i in range(data.shape[2]):
                            dst.write(data[:, :, i], i + 1)
                    else:
                        dst.write(data, 1)

                downloaded = True
                print(f"Downloaded and saved {filename}")

                # Small delay to avoid API throttling
                time.sleep(2)
            except Exception as e:
                print(f"Error downloading {date_str}: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    print("\nAll images downloaded successfully! ✅")


# ------------------- MAIN -------------------
if __name__ == "__main__":
    download_all_images()