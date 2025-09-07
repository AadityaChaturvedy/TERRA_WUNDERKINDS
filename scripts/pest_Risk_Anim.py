import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter

def load_masks_folder(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith('.tif') and f.startswith('refined_pest_mask_')]
    files = sorted(files)

    masks = []
    dates = []
    for f in files:
        path = os.path.join(folder_path, f)
        with rasterio.open(path) as src:
            mask = src.read(1)
            masks.append(mask)
            date_str = f.replace('refined_pest_mask_tanjavur_', '').replace('.tif', '')
            dates.append(date_str)
    masks_stack = np.array(masks)
    return masks_stack, dates

def animate_risk_timeseries_save_gif(masks_stack, dates, output_file='pest_disease_risk_timelapse.gif'):
    fig, ax = plt.subplots(figsize=(6, 6))
    img = ax.imshow(masks_stack[0], cmap='gray', vmin=0, vmax=1)
    ax.axis('off')
    title = ax.text(0.5, 1.05, "", size=plt.rcParams["axes.titlesize"],
                    ha="center", transform=ax.transAxes)

    def update(frame):
        img.set_data(masks_stack[frame])
        title.set_text(f'Date: {dates[frame]}')
        return [img, title]

    ani = FuncAnimation(fig, update, frames=len(dates), blit=True, interval=500, repeat=False)

    writer = PillowWriter(fps=2)
    ani.save(output_file, writer=writer)
    print(f'Animation saved as {output_file}')
    plt.close(fig)

if __name__ == '__main__':
    folder_path = '/Volumes/SSD/Proj_Terra/data/normalized/PestRefinedData'
    masks_stack, dates = load_masks_folder(folder_path)
    animate_risk_timeseries_save_gif(masks_stack, dates)