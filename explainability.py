import shap
import numpy as np
import pandas as pd
from tensorflow import keras
import matplotlib.pyplot as plt
import pickle


def explain_prediction_shap(model_path, scaler_path, X_sample, feature_names):
    """
    Generate SHAP explanations for model predictions
    """
    # Load model and scaler
    model = keras.models.load_model(model_path)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)

    # Prepare data
    X_scaled = scaler.transform(X_sample)

    # Create SHAP explainer
    explainer = shap.DeepExplainer(model, X_scaled[:100])  # Use subset for background
    shap_values = explainer.shap_values(X_scaled)

    # Get feature importance
    feature_importance = {
        feature_names[i]: abs(shap_values[0][0][i])
        for i in range(len(feature_names))
    }

    # Sort by importance
    sorted_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

    return sorted_features, shap_values


def generate_shap_summary(model_path='models/emotion_ann_model.h5',
                          scaler_path='models/scaler.save',
                          data_path='../wesad_features.csv'):
    """
    Generate SHAP summary plot
    """
    df = pd.read_csv(data_path)

    feature_columns = ['ACC_mean_x', 'ACC_mean_y', 'ACC_mean_z', 'ACC_std_x', 'ACC_std_y', 'ACC_std_z',
                       'BVP_mean', 'BVP_std', 'EDA_mean', 'EDA_std', 'TEMP_mean', 'TEMP_std']

    X = df[feature_columns].values[:1000]  # Sample for speed

    # Load model
    model = keras.models.load_model(model_path)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)

    X_scaled = scaler.transform(X)

    # SHAP analysis
    explainer = shap.DeepExplainer(model, X_scaled[:100])
    shap_values = explainer.shap_values(X_scaled)

    # Save plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_scaled, feature_names=feature_columns, show=False)
    plt.savefig('static/shap_summary.png', bbox_inches='tight', dpi=150)
    plt.close()

    print("✅ SHAP summary plot saved to static/shap_summary.png")

    return shap_values
