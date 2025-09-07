import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

# Load pixel time series CSV and sample same as training
csv_path = '/Volumes/SSD/Proj_Terra/PEST/pixel_timeseries.csv'  # Update as needed
df = pd.read_csv(csv_path)
data = df.drop(columns=['pixel_id']).values

# Use the same pixel sampling as training
sample_frac = 0.02
sample_size = int(data.shape[0] * sample_frac)
np.random.seed(42)
sample_indices = np.random.choice(data.shape[0], sample_size, replace=False)
data_sampled = data[sample_indices, :]

SEQ_LENGTH = 10
PRED_STEP = 1

def create_sequences(data, seq_length=SEQ_LENGTH, pred_step=PRED_STEP):
    X, y = [], []
    max_time = data.shape[1]
    for i in range(max_time - seq_length - pred_step + 1):
        X.append(data[:, i:i+seq_length])
        y.append(data[:, i+seq_length+pred_step-1])
    X = np.stack(X, axis=1)
    y = np.stack(y, axis=1)
    return X, y

X, y = create_sequences(data_sampled, SEQ_LENGTH, PRED_STEP)

num_pixels, seq_count, seq_len = X.shape
X = X.transpose((1, 0, 2))
X = X.reshape((seq_count * num_pixels, seq_len, 1))
y = y.transpose((1, 0)).flatten()

# Split test data (use same or new split)
_, X_test, _, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True)

# Load saved model checkpoint
model = load_model('/Volumes/SSD/Proj_Terra/PEST/lstm_pest_model_epoch_01.h5')  # Update file name as needed

# Evaluate model on test set
y_pred_prob = model.predict(X_test)
y_pred = (y_pred_prob > 0.5).astype(int).flatten()

print("Test Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# --- Generate pest risk predictions for future time step (next date) ---

# Use last SEQ_LENGTH time steps for each sampled pixel
last_sequences = data_sampled[:, -SEQ_LENGTH:]
last_sequences = last_sequences.reshape(-1, SEQ_LENGTH, 1)

future_pred_prob = model.predict(last_sequences)
future_pred = (future_pred_prob > 0.5).astype(int).flatten()

print(f"Predicted pest risk for next time step per pixel sample (first 10): {future_pred[:10]}")