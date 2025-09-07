import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from scipy.ndimage import median_filter

# -------------------------
# Fake Data Generators
# -------------------------
time_steps = 10
height, width = 50, 50

# NDVI for LSTM demo
ndvi_data = np.random.rand(time_steps, height, width) * 2 - 1  # NDVI: -1 to 1
pest_risk_probs = np.clip(1 - (ndvi_data + 1) / 2 + 0.2*np.random.rand(*ndvi_data.shape), 0, 1)
pest_risk_binary = (pest_risk_probs > 0.5).astype(int)

# NDVI/EVI/NDWI for anomaly demo (single snapshot)
ndvi = np.random.rand(height, width)
evi = np.random.rand(height, width)
ndwi = np.random.rand(height, width)

def compute_anomaly(data):
    baseline = median_filter(data, size=15)
    return np.abs(data - baseline) / (baseline + 1e-6)

def create_mask(anomaly, threshold=0.3):
    return (anomaly > threshold).astype(np.uint8)

ndvi_anomaly = compute_anomaly(ndvi)
evi_anomaly = compute_anomaly(evi)
ndwi_anomaly = compute_anomaly(ndwi)
ndvi_mask = create_mask(ndvi_anomaly)
evi_mask = create_mask(evi_anomaly)
ndwi_mask = create_mask(ndwi_anomaly)
refined_mask = np.logical_and(ndvi_mask == 1,
                              np.logical_not(np.logical_or(evi_mask == 1, ndwi_mask == 1))).astype(np.uint8)

# Steps for anomaly animation
anomaly_steps = [
    (ndvi, "Original NDVI"),
    (ndvi_anomaly, "NDVI Anomaly"),
    (ndvi_mask, "NDVI Mask"),
    (evi_mask, "EVI Mask"),
    (ndwi_mask, "NDWI Mask"),
    (refined_mask, "Refined Pest Risk")
]

# -------------------------
# Tkinter Setup
# -------------------------
root = tk.Tk()
root.title("Pest Risk Visualization Demos")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# -------------------------
# TAB 1: LSTM Animation
# -------------------------
frame1 = ttk.Frame(notebook)
notebook.add(frame1, text="NDVI → LSTM → Pest Risk")

fig1 = Figure(figsize=(10, 4))
ax1 = fig1.add_subplot(131)
ax2 = fig1.add_subplot(132)
ax3 = fig1.add_subplot(133)

im1 = ax1.imshow(ndvi_data[0], cmap="RdYlGn", vmin=-1, vmax=1)
ax1.set_title("NDVI Input")

im2 = ax2.imshow(pest_risk_probs[0], cmap="viridis", vmin=0, vmax=1)
ax2.set_title("LSTM Risk Probability")

im3 = ax3.imshow(pest_risk_binary[0], cmap="Reds", vmin=0, vmax=1)
ax3.set_title("Binary Pest Risk")

fig1.suptitle("NDVI → LSTM Prediction → Binary Pest Risk", fontsize=12)

canvas1 = FigureCanvasTkAgg(fig1, master=frame1)
canvas1.draw()
canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def update_lstm(frame):
    im1.set_data(ndvi_data[frame])
    im2.set_data(pest_risk_probs[frame])
    im3.set_data(pest_risk_binary[frame])
    fig1.suptitle(f"Time Step {frame+1}/{time_steps}", fontsize=12)
    canvas1.draw()
    return im1, im2, im3

ani1 = animation.FuncAnimation(fig1, update_lstm, frames=time_steps, interval=1000, blit=False, repeat=True)

# -------------------------
# TAB 2: Anomaly Animation
# -------------------------
frame2 = ttk.Frame(notebook)
notebook.add(frame2, text="NDVI/EVI/NDWI → Anomaly → Mask")

fig2 = Figure(figsize=(6, 5))
ax4 = fig2.add_subplot(111)
im4 = ax4.imshow(anomaly_steps[0][0], cmap="viridis")
title = ax4.set_title(anomaly_steps[0][1])
fig2.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)

canvas2 = FigureCanvasTkAgg(fig2, master=frame2)
canvas2.draw()
canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def update_anomaly(i):
    data, label = anomaly_steps[i]
    im4.set_array(data)
    if np.max(data) <= 1:
        im4.set_cmap("gray")
    else:
        im4.set_cmap("viridis")
    title.set_text(label)
    canvas2.draw()
    return [im4, title]

ani2 = animation.FuncAnimation(fig2, update_anomaly, frames=len(anomaly_steps),
                               interval=1500, blit=False, repeat=True)

# -------------------------
# Run Tkinter Loop
# -------------------------
root.mainloop()