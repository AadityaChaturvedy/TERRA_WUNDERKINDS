import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.models import Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, CSVLogger
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from imblearn.over_sampling import RandomOverSampler
from sklearn.utils import class_weight
from tqdm import tqdm
import os
from typing import Tuple


def load_data(csv_path: str, sample_frac: float = 0.05, random_state: int = 42) -> np.ndarray:
    df = pd.read_csv(csv_path)
    if 'pixel_id' in df.columns:
        data = df.drop(columns=['pixel_id']).values
    else:
        data = df.values

    print(f"Original data shape: {data.shape} (pixels x timesteps)")

    np.random.seed(random_state)
    sample_size = int(data.shape[0] * sample_frac)
    sample_indices = np.random.choice(data.shape[0], sample_size, replace=False)
    data_sampled = data[sample_indices, :]
    print(f"Sampled data shape: {data_sampled.shape}")
    return data_sampled


def create_sequences(data: np.ndarray, seq_length: int, pred_step: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sequences and labels for LSTM input.
    Returns:
      X: shape (num_pixels, num_sequences, seq_length)
      y: shape (num_pixels, num_sequences)
    """
    max_time = data.shape[1]
    X_seq, y_seq = [], []

    for start_idx in tqdm(range(max_time - seq_length - pred_step + 1), desc="Creating sequences"):
        X_seq.append(data[:, start_idx: start_idx + seq_length])
        y_seq.append(data[:, start_idx + seq_length + pred_step - 1])

    X_arr = np.stack(X_seq, axis=1)
    y_arr = np.stack(y_seq, axis=1)

    print(f"X shape before reshape: {X_arr.shape}")
    print(f"y shape before reshape: {y_arr.shape}")
    return X_arr, y_arr


def oversample_data(X: np.ndarray, y: np.ndarray, seq_length: int, random_state: int = 42) -> Tuple[
    np.ndarray, np.ndarray]:
    """
    Oversamples minority class using RandomOverSampler
    """
    num_pixels, seq_count, _ = X.shape
    X_reshaped = X.transpose((1, 0, 2)).reshape(seq_count * num_pixels, seq_length, 1)
    y_reshaped = y.transpose((1, 0)).flatten()

    print(f"X reshaped for oversampling: {X_reshaped.shape}")
    print(f"y reshaped for oversampling: {y_reshaped.shape}")

    unique, counts = np.unique(y_reshaped, return_counts=True)
    print(f"Label distribution before oversampling: {dict(zip(unique, counts))}")

    X_flat = X_reshaped.reshape(X_reshaped.shape[0], -1)
    ros = RandomOverSampler(random_state=random_state)
    X_resampled_flat, y_resampled = ros.fit_resample(X_flat, y_reshaped)

    X_resampled = X_resampled_flat.reshape(-1, seq_length, 1)

    unique_resampled, counts_resampled = np.unique(y_resampled, return_counts=True)
    print(f"Label distribution after oversampling: {dict(zip(unique_resampled, counts_resampled))}")

    return X_resampled, y_resampled


def build_lstm_model(seq_length: int) -> Model:
    inputs = Input(shape=(seq_length, 1))
    x = LSTM(64)(inputs)
    x = Dropout(0.3)(x)
    x = Dense(32, activation='relu')(x)
    outputs = Dense(1, activation='sigmoid')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=Adam(0.001), loss='binary_crossentropy', metrics=['accuracy'])
    return model


def plot_predicted_probabilities(pred_probs: np.ndarray, bins: int = 50) -> None:
    plt.figure(figsize=(8, 5))
    plt.hist(pred_probs, bins=bins, alpha=0.7, color='c')
    plt.title("Predicted Pest Risk Probabilities on Test Set")
    plt.xlabel("Probability")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()


def main(
        csv_path: str = 'pixel_timeseries.csv',
        sample_frac: float = 0.05,
        seq_length: int = 10,
        pred_step: int = 1,
        batch_size: int = 512,
        epochs: int = 30,
        random_state: int = 42,
        threshold: float = 0.5
):
    # Load and sample data
    data_sampled = load_data(csv_path, sample_frac, random_state)

    # Create sequences
    X, y = create_sequences(data_sampled, seq_length, pred_step)

    # Oversample
    X_resampled, y_resampled = oversample_data(X, y, seq_length, random_state)

    # Train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled, y_resampled, test_size=0.2, random_state=random_state, stratify=y_resampled
    )

    # Compute class weights
    class_weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weights_dict = dict(enumerate(class_weights))
    print(f"Class weights: {class_weights_dict}")

    # Build model
    model = build_lstm_model(seq_length)
    model.summary()

    # Callbacks
    checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, "lstm_pest_model_epoch_{epoch:02d}_valLoss_{val_loss:.4f}.h5")

    checkpoint = ModelCheckpoint(
        filepath=checkpoint_path,
        save_weights_only=False,
        verbose=1,
        monitor='val_loss',
        save_best_only=True,
        mode='min'
    )

    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=7,
        restore_best_weights=True,
        verbose=1
    )

    csv_logger = CSVLogger('training_log.csv')

    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.1,
        callbacks=[checkpoint, early_stop, csv_logger],
        class_weight=class_weights_dict,
        verbose=1
    )

    # Evaluate
    y_pred_prob = model.predict(X_test, verbose=0)
    y_pred = (y_pred_prob > threshold).astype(int).flatten()

    print("Test Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred, digits=4))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    plot_predicted_probabilities(y_pred_prob)

    # Predict future pest risk for last sequences from sampled data
    last_sequences = data_sampled[:, -seq_length:].reshape(-1, seq_length, 1)
    future_pred_prob = model.predict(last_sequences, verbose=0)
    future_pred = (future_pred_prob > threshold).astype(int).flatten()
    print(f"Predicted pest risk for next time step for first 10 pixels: {future_pred[:10]}")

    # Save final model
    model.save('lstm_pest_model_final.h5')
    print("Model saved to lstm_pest_model_final.h5")


if __name__ == "__main__":
    main()