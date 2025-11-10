import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CNNLSTMModel:
    """Hybrid CNN-LSTM model for temporal stress detection"""

    def __init__(self, input_shape=(60, 7), num_classes=3):
        """
        Args:
            input_shape: (timesteps, features) e.g., (60, 7) for 60s windows with 7 signals
            num_classes: 3 (baseline, stress, amusement)
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None

    def build_model(self):
        """Build hybrid CNN-LSTM architecture"""
        inputs = layers.Input(shape=self.input_shape)

        # CNN layers for local feature extraction
        x = layers.Conv1D(filters=64, kernel_size=3, activation='relu', padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(pool_size=2)(x)
        x = layers.Dropout(0.3)(x)

        x = layers.Conv1D(filters=128, kernel_size=3, activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(pool_size=2)(x)
        x = layers.Dropout(0.3)(x)

        # LSTM layers for temporal dependencies
        x = layers.LSTM(128, return_sequences=True)(x)
        x = layers.Dropout(0.3)(x)
        x = layers.LSTM(64, return_sequences=False)(x)
        x = layers.Dropout(0.3)(x)

        # Dense layers
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)

        self.model = Model(inputs=inputs, outputs=outputs, name='CNN_LSTM_StressNet')

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )

        logger.info(f"CNN-LSTM model built with input shape {self.input_shape}")
        return self.model

    def build_attention_model(self):
        """Build CNN-LSTM with Attention mechanism"""
        inputs = layers.Input(shape=self.input_shape)

        # CNN layers
        x = layers.Conv1D(filters=64, kernel_size=3, activation='relu', padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling1D(pool_size=2)(x)

        # LSTM with return sequences for attention
        lstm_out = layers.LSTM(128, return_sequences=True)(x)

        # Attention mechanism
        attention = layers.Dense(1, activation='tanh')(lstm_out)
        attention = layers.Flatten()(attention)
        attention = layers.Activation('softmax')(attention)
        attention = layers.RepeatVector(128)(attention)
        attention = layers.Permute([2, 1])(attention)

        # Apply attention weights
        attended = layers.Multiply()([lstm_out, attention])
        attended = layers.Lambda(lambda x: tf.reduce_sum(x, axis=1))(attended)

        # Dense layers
        x = layers.Dense(64, activation='relu')(attended)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(self.num_classes, activation='softmax')(x)

        self.model = Model(inputs=inputs, outputs=outputs, name='CNN_LSTM_Attention')

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )

        logger.info("CNN-LSTM-Attention model built successfully")
        return self.model

    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """Train the model with early stopping"""
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            ),
            keras.callbacks.ModelCheckpoint(
                'models/cnn_lstm_best.h5',
                monitor='val_accuracy',
                save_best_only=True
            )
        ]

        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        return history

    def evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        results = self.model.evaluate(X_test, y_test, verbose=0)
        metrics = dict(zip(self.model.metrics_names, results))
        logger.info(f"Test metrics: {metrics}")
        return metrics

    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X)

    def save(self, filepath='models/cnn_lstm_model.h5'):
        """Save model to file"""
        self.model.save(filepath)
        logger.info(f"Model saved to {filepath}")

    def load(self, filepath='models/cnn_lstm_model.h5'):
        """Load model from file"""
        self.model = keras.models.load_model(filepath)
        logger.info(f"Model loaded from {filepath}")
        return self.model


def create_windowed_dataset(features, labels, window_size=60, stride=30):
    """
    Create sliding windows from continuous data

    Args:
        features: numpy array of shape (n_samples, n_features)
        labels: numpy array of shape (n_samples,)
        window_size: number of timesteps per window
        stride: step size for sliding window

    Returns:
        X: windowed features (n_windows, window_size, n_features)
        y: corresponding labels (n_windows,)
    """
    X_windows = []
    y_windows = []

    for i in range(0, len(features) - window_size + 1, stride):
        window = features[i:i + window_size]
        # Use majority vote for label in window
        window_labels = labels[i:i + window_size]
        majority_label = np.bincount(window_labels.astype(int)).argmax()

        X_windows.append(window)
        y_windows.append(majority_label)

    return np.array(X_windows), np.array(y_windows)
