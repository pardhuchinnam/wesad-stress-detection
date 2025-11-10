import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.utils import to_categorical
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from models.hybrid_model import CNNLSTMModel, create_windowed_dataset


def load_wesad_data(filepath='data/processed_wesad.csv'):
    """Load preprocessed WESAD data"""
    df = pd.read_csv(filepath)

    # Feature columns
    feature_cols = ['ACC_x', 'ACC_y', 'ACC_z', 'EDA', 'EMG', 'Temp', 'Resp']
    X = df[feature_cols].values

    # Labels (0=baseline, 1=stress, 2=amusement)
    y = df['label'].values

    return X, y


def main():
    print("🚀 Training CNN-LSTM Hybrid Model for WESAD Stress Detection")

    # Load data
    X, y = load_wesad_data()
    print(f"✅ Loaded data: {X.shape[0]} samples, {X.shape[1]} features")

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Create windowed dataset (60s windows, 30s stride)
    X_windowed, y_windowed = create_windowed_dataset(
        X_scaled, y, window_size=60, stride=30
    )
    print(f"✅ Created {X_windowed.shape[0]} windows of shape {X_windowed.shape[1:]}")

    # Convert labels to categorical
    y_categorical = to_categorical(y_windowed, num_classes=3)

    # Train-validation-test split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X_windowed, y_categorical, test_size=0.15, random_state=42, stratify=y_windowed
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.18, random_state=42
    )

    print(f"✅ Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

    # Build and train CNN-LSTM model
    print("\n🔨 Building CNN-LSTM model...")
    model = CNNLSTMModel(input_shape=(60, 7), num_classes=3)
    model.build_model()
    model.model.summary()

    print("\n🎯 Training model...")
    history = model.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)

    # Evaluate
    print("\n📊 Evaluating on test set...")
    metrics = model.evaluate(X_test, y_test)
    print(f"Test Accuracy: {metrics['accuracy']:.4f}")
    print(f"Test Precision: {metrics['precision']:.4f}")
    print(f"Test Recall: {metrics['recall']:.4f}")

    # Save model
    model.save('models/cnn_lstm_model.h5')
    print("\n✅ Model saved to models/cnn_lstm_model.h5")

    # Build and train with Attention
    print("\n🔨 Building CNN-LSTM-Attention model...")
    attention_model = CNNLSTMModel(input_shape=(60, 7), num_classes=3)
    attention_model.build_attention_model()

    print("\n🎯 Training attention model...")
    history_attention = attention_model.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)

    metrics_attention = attention_model.evaluate(X_test, y_test)
    print(f"\nAttention Model - Test Accuracy: {metrics_attention['accuracy']:.4f}")

    attention_model.save('models/cnn_lstm_attention.h5')
    print("\n✅ Attention model saved to models/cnn_lstm_attention.h5")


if __name__ == '__main__':
    main()
