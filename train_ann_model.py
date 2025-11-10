import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load preprocessed feature data: TODO replace with your CSV/data loading
data = pd.read_csv(r'C:\Users\PARDHU\Desktop\WESAD\wesad_features.csv')
X = data.drop('label', axis=1).values
y = to_categorical(data['label'].values, num_classes=3)

# Scale features
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define ANN model
model = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(3, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train model
model.fit(X_train, y_train, epochs=50, batch_size=64, validation_split=0.2, callbacks=[early_stop])

# Save model and scaler separately
model.save('models/emotion_ann_model.h5')
import joblib
joblib.dump(scaler, 'models/scaler.save')

print("Model training complete and saved.")
