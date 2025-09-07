from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
import pandas as pd
from affine import Affine
import warnings
from tqdm import tqdm

warnings.filterwarnings("ignore", category=UserWarning, module="geopandas")


def load_masks(folder_path, bbox=None):
    """
    Load all pest mask TIFF files from a folder into a numpy array stack.
    If bbox provided, assign transform and crs if missing.
    Returns: masks_stack (np.ndarray), dates (list), meta (dict)
    """
    folder = Path(folder_path)
    files = sorted([f for f in folder.glob('refined_pest_mask_*.tif')])
    if not files:
        raise FileNotFoundError(f"No mask files found in {folder_path}")
    masks, dates, meta = [], [], None
    for f in tqdm(files, desc="Loading masks"):
        with rasterio.open(f) as src:
            mask = src.read(1)
            masks.append(mask)
            if meta is None:
                meta = src.meta.copy()
                # Assign CRS and transform if missing
                if meta.get('crs') is None and bbox:
                    meta['crs'] = 'EPSG:4326'
                if (meta.get('transform') is None or meta['transform'].is_identity) and bbox:
                    min_lon, min_lat, max_lon, max_lat = bbox
                    w, h = meta['width'], meta['height']
                    pixel_width = (max_lon - min_lon) / w
                    pixel_height = (max_lat - min_lat) / h
                    meta['transform'] = Affine.translation(min_lon, max_lat) * Affine.scale(pixel_width, -pixel_height)
        date_str = f.stem.replace('pest_mask_tanjavur_', '')
        dates.append(date_str)
    masks_stack = np.array(masks)
    return masks_stack, dates, meta


def extract_pixel_timeseries(masks_stack, dates, output_csv):
    n_times, h, w = masks_stack.shape
    data = masks_stack.reshape(n_times, -1).T
    df = pd.DataFrame(data, columns=dates)
    df.insert(0, 'pixel_id', range(df.shape[0]))
    df.to_csv(output_csv, index=False)
    print(f"[INFO] Per-pixel time series saved to {output_csv}")


def raster_to_polygons(mask, transform, crs):
    mask_bool = mask.astype(bool)
    results = (
        {'properties': {'raster_val': v}, 'geometry': s}
        for s, v in shapes(mask_bool.astype('uint8'), mask=mask_bool, transform=transform)
    )
    geoms = list(results)
    if not geoms:
        return gpd.GeoDataFrame(columns=['geometry', 'raster_val'], geometry='geometry', crs='EPSG:4326')
    gdf = gpd.GeoDataFrame.from_features(geoms)

    if crs is None:
        crs_str = 'EPSG:4326'
        print("[WARN] CRS None, setting to EPSG:4326")
    elif hasattr(crs, 'to_string'):
        crs_str = crs.to_string()
    else:
        crs_str = crs

    gdf = gdf.set_crs(crs_str, allow_override=True)
    gdf = gdf.to_crs(epsg=4326)
    return gdf


def save_vector_polygons(masks_stack, dates, meta, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    transform = meta['transform']
    crs = meta['crs']
    summary_rows = []
    for i, date in tqdm(enumerate(dates), total=len(dates), desc="Processing dates"):
        print(f"[INFO] Processing {date} ({i + 1}/{len(dates)})...")
        mask = masks_stack[i]
        gdf = raster_to_polygons(mask, transform, crs)
        risk_gdf = gdf[gdf['raster_val'] == 1].copy()
        if risk_gdf.empty:
            print(f"[WARN] No risk areas detected on {date}.")
        else:
            out_fp = output_dir / f'pest_risk_{date}.geojson'
            risk_gdf.to_file(out_fp, driver='GeoJSON')
            print(f"[INFO] Saved {len(risk_gdf)} risk polygons on {date} to {out_fp}")
            total_area = risk_gdf.to_crs(epsg=3857)['geometry'].area.sum() / 10000
            summary_rows.append({'date': date, 'risk_polygon_count': len(risk_gdf), 'risk_area_ha': total_area})
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = output_dir / 'risk_summary.csv'
    summary_df.to_csv(summary_csv, index=False)
    print(f"[INFO] Risk summary saved to {summary_csv}")
    return summary_df


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pest risk time series vector reporting with debug and progress bars")
    parser.add_argument('--input_folder', type=str, default='/Volumes/SSD/Proj_Terra/data/cleaned_pestRefinedData', help='Folder with refined pest mask TIFFs')
    parser.add_argument('--pixel_csv', type=str, default='pixel_timeseries.csv', help='CSV for per-pixel time series')
    parser.add_argument('--vector_dir', type=str, default='debug_pest_risk_vectors', help='Directory for vector polygons and summary')
    parser.add_argument('--bbox', nargs=4, type=float, default=[79, 10.57, 79.047, 10.617], help='Bounding box: min_lon min_lat max_lon max_lat')
    args = parser.parse_args()

    bbox = args.bbox
    print(f"[INFO] Loading masks from {args.input_folder} with bbox {bbox}")
    masks_stack, dates, meta = load_masks(args.input_folder, bbox)

    print("[INFO] Extracting per-pixel time series...")
    extract_pixel_timeseries(masks_stack, dates, args.pixel_csv)

    print("[INFO] Converting masks to polygons and summarizing...")
    summary_df = save_vector_polygons(masks_stack, dates, meta, args.vector_dir)

    print("[INFO] All done!")


if __name__ == '__main__':
    main()
