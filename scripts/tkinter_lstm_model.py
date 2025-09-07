import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tensorflow.keras.models import load_model


class PestRiskPredictorApp:
    def __init__(self, master):
        self.master = master
        master.title("Pest Risk Predictor with LSTM")

        # Instruction label
        self.label = tk.Label(master, text="Load 10 normalized NDVI .tif files for prediction")
        self.label.pack(pady=5)

        # Load NDVI files button
        self.load_button = tk.Button(master, text="Load NDVI Files", command=self.load_files)
        self.load_button.pack(pady=5)

        # Predict button, disabled until files loaded
        self.predict_button = tk.Button(master, text="Predict Future Pest Risk", command=self.predict, state='disabled')
        self.predict_button.pack(pady=5)

        # Export button, disabled until prediction is done
        self.export_button = tk.Button(master, text="Export Risk Map", command=self.export_risk_map, state='disabled')
        self.export_button.pack(pady=5)

        # Canvas and figure placeholders for plot
        self.canvas = None
        self.fig = None

        # NDVI data stack: shape (time, height, width)
        self.ndvi_stack = None

        # Model
        self.model = load_model('/Volumes/SSD/Proj_Terra/PEST/checkpoints/lstm_pest_model_epoch_05_valLoss_0.6144.h5')

        # Sequence length expected by the model
        self.SEQ_LENGTH = 10

        # Metadata for export
        self.meta = None

        # To store predicted risk map
        self.risk_map = None

    def load_files(self):
        # Open file dialog to select exactly 10 TIFF files
        file_paths = filedialog.askopenfilenames(
            title="Select 10 NDVI .tif files",
            filetypes=[("TIFF files", "*.tif")]
        )

        if len(file_paths) != self.SEQ_LENGTH:
            messagebox.showerror("Error", f"Please select exactly {self.SEQ_LENGTH} .tif files")
            return

        try:
            arrays = []
            for i, fp in enumerate(file_paths):
                with rasterio.open(fp) as src:
                    arr = src.read(1).astype(float)
                    arrays.append(arr)
                    # Save metadata from first file for georeferencing export
                    if i == 0:
                        self.meta = src.meta.copy()
            self.ndvi_stack = np.stack(arrays, axis=0)  # (time, height, width)
            self.height, self.width = self.ndvi_stack.shape[1], self.ndvi_stack.shape[2]

            messagebox.showinfo("Success", "NDVI files loaded successfully")
            self.predict_button.config(state='normal')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load files:\n{e}")

    def predict(self):
        if self.ndvi_stack is None:
            messagebox.showerror("Error", "No NDVI data loaded")
            return

        # Reshape stack to (pixels, time_steps)
        pixels = self.height * self.width
        data = self.ndvi_stack.reshape(self.SEQ_LENGTH, pixels).T  # (pixels, time_steps)

        # Reshape to (samples, seq_len, features) -> (pixels, sequence_length, 1)
        X_input = data[:, :, np.newaxis]

        try:
            pred_prob = self.model.predict(X_input, batch_size=1024)
            pred_binary = (pred_prob > 0.999).astype(np.uint8).flatten()
            risk_map = pred_binary.reshape(self.height, self.width)
            self.risk_map = risk_map  # Save for export

            self.display_map(risk_map)
            self.export_button.config(state='normal')  # Enable export button

        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed:\n{e}")

    def display_map(self, risk_map):
        if self.canvas:
            self.canvas.get_tk_widget().pack_forget()

        self.fig, ax = plt.subplots(figsize=(6, 6))
        cax = ax.imshow(risk_map, cmap='Reds', interpolation='none')
        ax.set_title("Predicted Pest Risk (Next Time Step)")
        plt.colorbar(cax, ax=ax, label='Risk (0=No, 1=Yes)')
        ax.axis('off')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10)

    def export_risk_map(self):
        if self.risk_map is None or self.meta is None:
            messagebox.showerror("Error", "No risk map to export")
            return

        export_meta = self.meta.copy()
        export_meta.update({
            "count": 1,
            "dtype": "uint8"
        })

        export_path = filedialog.asksaveasfilename(
            defaultextension=".tif",
            filetypes=[("TIFF files", "*.tif")],
            title="Save Predicted Pest Risk Map"
        )

        if not export_path:
            return

        try:
            with rasterio.open(export_path, 'w', **export_meta) as dst:
                dst.write(self.risk_map.astype('uint8'), 1)
            messagebox.showinfo("Success", f"Pest risk map saved to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save risk map:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PestRiskPredictorApp(root)
    root.mainloop()
