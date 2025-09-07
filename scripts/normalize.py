import os
import numpy as np
import imageio.v2 as imageio

def normalize_index_image(input_path, output_path):
    """
    Normalize an index image (NDVI, NDWI, EVI) from [-1, 1] to [0, 1],
    replace invalid values, and save as 8-bit image.
    """
    image = imageio.imread(input_path).astype(np.float32)
    # Replace NaN and infinite values
    invalid_mask = np.isnan(image) | np.isinf(image)
    if np.any(invalid_mask):
        print(f"Found {np.sum(invalid_mask)} invalid values in {input_path}, replacing with -1.")
        image[invalid_mask] = -1.0
    # Clip to [-1, 1]
    image = np.clip(image, -1, 1)
    # Normalize to [0,1]
    normalized_image = (image + 1) / 2
    # Convert to 8-bit
    normalized_8bit = (normalized_image * 255).astype(np.uint8)
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Save normalized image
    imageio.imwrite(output_path, normalized_8bit)
    print(f"Saved normalized image to {output_path}")

def batch_normalize_images(processed_dir='/Volumes/SSD/Proj_Terra/data/processed', normalized_dir='/Volumes/SSD/Proj_Terra/data/normalized'):
    """
    Batch normalize NDVI, NDWI, EVI images in subfolders of processed_dir
    and save outputs preserving folder structure under normalized_dir.
    """
    for date_folder in os.listdir(processed_dir):
        date_path = os.path.join(processed_dir, date_folder)
        if os.path.isdir(date_path):
            for index_name in ['NDVI', 'NDWI', 'EVI']:
                filename = f"{date_folder}_{index_name}.tif"
                input_path = os.path.join(date_path, filename)
                if os.path.exists(input_path):
                    output_path = os.path.join(normalized_dir, date_folder, filename)
                    normalize_index_image(input_path, output_path)
                else:
                    print(f"File not found: {input_path}")

if __name__ == "__main__":
    batch_normalize_images()
