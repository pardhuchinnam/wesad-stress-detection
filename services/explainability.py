"""Enhanced SHAP & LIME explainability"""
import shap
import lime
import lime.lime_tabular
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import jsonify


def explain_prediction_shap(model, X_sample, feature_names):
    """Generate SHAP explanation for a single prediction"""
    try:
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model) if hasattr(model, 'tree_') else shap.KernelExplainer(model.predict,
                                                                                                   X_sample)

        # Calculate SHAP values
        shap_values = explainer.shap_values(X_sample)

        # Get feature importance
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # For binary classification

        importance = dict(zip(feature_names, np.abs(shap_values[0])))
        sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

        return {
            'method': 'SHAP',
            'feature_importance': sorted_importance,
            'top_features': list(sorted_importance.keys())[:5],
            'shap_values': shap_values[0].tolist()
        }

    except Exception as e:
        return {'error': str(e)}


def explain_prediction_lime(model, X_train, X_sample, feature_names, class_names):
    """Generate LIME explanation"""
    try:
        # Create LIME explainer
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train,
            feature_names=feature_names,
            class_names=class_names,
            mode='classification'
        )

        # Explain prediction
        exp = explainer.explain_instance(
            X_sample[0],
            model.predict_proba,
            num_features=10
        )

        # Extract feature importance
        lime_importance = dict(exp.as_list())

        return {
            'method': 'LIME',
            'feature_importance': lime_importance,
            'prediction_confidence': exp.predict_proba.tolist(),
            'top_features': [feat for feat, _ in exp.as_list()[:5]]
        }

    except Exception as e:
        return {'error': str(e)}


def generate_shap_plot(model, X_data, feature_names):
    """Generate SHAP summary plot as base64 image"""
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_data)

        # Create plot
        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X_data, feature_names=feature_names, show=False)

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        return None
