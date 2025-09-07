import os
import torch
from torch.utils.data import Dataset
import numpy as np
import glob
import rasterio

class TemporalSequenceDataset(Dataset):
    """
    Dataset that returns sequences of images per location in temporal order.
    """
    def __init__(self, data_base_dir, label_base_dir, sequence_length=5, transform=None):
        self.data_base_dir = data_base_dir
        self.label_base_dir = label_base_dir
        self.sequence_length = sequence_length
        self.transform = transform

        # List all sequence folders (assuming naming convention with dates)
        all_folders = sorted([d for d in os.listdir(data_base_dir) if os.path.isdir(os.path.join(data_base_dir, d))])
        # Group folders by spatial location prefix (e.g., farm or plot name)
        self.locations = {}
        for folder in all_folders:
            loc = "_".join(folder.split("_")[:-1])
            if loc not in self.locations:
                self.locations[loc] = []
            self.locations[loc].append(folder)
        # Filter locations with enough sequence length
        self.locations = {k: sorted(v) for k, v in self.locations.items() if len(v) >= self.sequence_length}
        self.location_keys = list(self.locations.keys())

    def read_indices(self, folder_path):
        ndvi = self.read_geotiff(glob.glob(os.path.join(folder_path, '*NDVI*.tif'))[0])
        evi = self.read_geotiff(glob.glob(os.path.join(folder_path, '*EVI*.tif'))[0])
        ndwi = self.read_geotiff(glob.glob(os.path.join(folder_path, '*NDWI*.tif'))[0])
        image = np.stack([ndvi, evi, ndwi], axis=0).astype(np.float32)
        # Normalize each channel to [0,1]
        min_vals = image.min(axis=(1,2), keepdims=True)
        max_vals = image.max(axis=(1,2), keepdims=True)
        image = (image - min_vals) / (max_vals - min_vals + 1e-6)
        return torch.tensor(image, dtype=torch.float32)

    def read_geotiff(self, filepath):
        with rasterio.open(filepath) as src:
            array = src.read(1).astype(np.float32)
            array = np.nan_to_num(array, nan=0.0)
        return array

    def __len__(self):
        return len(self.location_keys)

    def __getitem__(self, idx):
        loc = self.location_keys[idx]
        seq_folders = self.locations[loc][:self.sequence_length]
        images = []
        labels = []
        for folder in seq_folders:
            folder_path = os.path.join(self.data_base_dir, folder)
            img = self.read_indices(folder_path)
            if self.transform:
                img = self.transform(img)
            images.append(img)

            # Read label for last time step only, or sequence labels if available
            label_path = os.path.join(self.label_base_dir, folder, f"{folder}_label.tif")
            if os.path.exists(label_path):
                label_array = self.read_geotiff(label_path)
                label_tensor = torch.tensor(label_array, dtype=torch.float32).unsqueeze(0)
            else:
                label_tensor = torch.zeros_like(img[:1])  # fallback
            labels.append(label_tensor)

        images = torch.stack(images)  # (seq_len, 3, H, W)
        labels = labels[-1]  # Using label of last timestamp only; adjust if needed

        return images, labels
