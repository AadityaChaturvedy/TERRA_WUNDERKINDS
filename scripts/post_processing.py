import os
import glob
import rasterio
import numpy as np

RAW_DIR = "/Volumes/SSD/Proj_Terra/data/raw"
INDEX_DIR = "/Volumes/SSD/Proj_Terra/data"
PATCHED_DIR = "/Volumes/SSD/Proj_Terra/data/patched"

os.makedirs(PATCHED_DIR, exist_ok=True)


def process_date(date_name: str):
    print(f"▶ Processing date: {date_name}")

    # 🔹 Find raw file (.tif or .tiff)
    raw_files = glob.glob(os.path.join(RAW_DIR, f"{date_name}.tif*"))
    if not raw_files:
        print(f"❌ No raw file found for {date_name}")
        return
    raw_path = raw_files[0]

    # 🔹 Find NDVI + NDWI files
    ndvi_files = glob.glob(os.path.join(INDEX_DIR, date_name, f"{date_name}_NDVI.tif*"))
    ndwi_files = glob.glob(os.path.join(INDEX_DIR, date_name, f"{date_name}_NDWI.tif*"))

    if not ndvi_files or not ndwi_files:
        print(f"❌ Missing index files for {date_name}")
        return

    ndvi_path = ndvi_files[0]
    ndwi_path = ndwi_files[0]

    # 🔹 Read raster bands
    with rasterio.open(raw_path) as raw_ds, \
         rasterio.open(ndvi_path) as ndvi_ds, \
         rasterio.open(ndwi_path) as ndwi_ds:

        raw_data = raw_ds.read()
        ndvi_data = ndvi_ds.read(1)
        ndwi_data = ndwi_ds.read(1)

        # Example overlay logic: stack raw + NDVI + NDWI
        stacked = np.vstack([raw_data, ndvi_data[np.newaxis, ...], ndwi_data[np.newaxis, ...]])

        out_meta = raw_ds.meta.copy()
        out_meta.update(count=stacked.shape[0])

        out_path = os.path.join(PATCHED_DIR, f"{date_name}_patched.tif")
        with rasterio.open(out_path, "w", **out_meta) as dst:
            dst.write(stacked)

    print(f"✅ Patched file saved: {out_path}")


def main():
    if not os.path.exists(INDEX_DIR):
        print(f"❌ Index directory not found: {INDEX_DIR}")
        return

    # Get only folders inside INDEX_DIR
    date_folders = [d for d in os.listdir(INDEX_DIR)
                    if os.path.isdir(os.path.join(INDEX_DIR, d))]

    if not date_folders:
        print(f"❌ No date folders found inside {INDEX_DIR}")
        return

    for date_name in sorted(date_folders):
        process_date(date_name)

    print("🎉 All dates processed and patched!")


if __name__ == "__main__":
    main()