import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logger = logging.getLogger(__name__)


def leave_one_subject_out_cv(X, y, subjects, model_class=RandomForestClassifier):
    """
    Perform Leave-One-Subject-Out Cross Validation

    Args:
        X: feature matrix
        y: labels
        subjects: subject IDs for each sample
        model_class: ML model class to use

    Returns:
        dict with per-subject results
    """
    logo = LeaveOneGroupOut()
    results = []

    print("🔬 Starting Leave-One-Subject-Out Cross Validation...")

    for train_idx, test_idx in logo.split(X, y, groups=subjects):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        test_subject = subjects[test_idx[0]]

        # Train model
        model = model_class(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)

        results.append({
            'subject': test_subject,
            'accuracy': accuracy,
            'f1_score': f1,
            'precision': precision,
            'recall': recall,
            'n_samples': len(test_idx)
        })

        print(f"✅ Subject {test_subject}: Accuracy={accuracy:.4f}, F1={f1:.4f}")

    return pd.DataFrame(results)


def visualize_subject_results(results_df, save_path='static/subject_comparison.png'):
    """Create visualization of per-subject performance"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    metrics = ['accuracy', 'f1_score', 'precision', 'recall']
    titles = ['Accuracy', 'F1-Score', 'Precision', 'Recall']

    for ax, metric, title in zip(axes.flatten(), metrics, titles):
        ax.bar(results_df['subject'].astype(str), results_df[metric], color='steelblue')
        ax.axhline(results_df[metric].mean(), color='red', linestyle='--',
                   label=f'Mean: {results_df[metric].mean():.3f}')
        ax.set_xlabel('Subject ID')
        ax.set_ylabel(title)
        ax.set_title(f'Per-Subject {title}')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Subject comparison plot saved to {save_path}")
    return save_path


def main():
    # Load your WESAD data with subject IDs
    df = pd.read_csv('data/processed_wesad.csv')

    feature_cols = ['ACC_x', 'ACC_y', 'ACC_z', 'EDA', 'EMG', 'Temp', 'Resp']
    X = df[feature_cols].values
    y = df['label'].values
    subjects = df['subject_id'].values

    # Run LOSO-CV
    results_df = leave_one_subject_out_cv(X, y, subjects)

    # Save results
    results_df.to_csv('results/subject_wise_results.csv', index=False)

    # Visualize
    visualize_subject_results(results_df)

    # Print summary
    print("\n📊 Summary Statistics:")
    print(results_df[['accuracy', 'f1_score', 'precision', 'recall']].describe())

    print(f"\n✅ Mean Accuracy: {results_df['accuracy'].mean():.4f} ± {results_df['accuracy'].std():.4f}")
    print(f"✅ Mean F1-Score: {results_df['f1_score'].mean():.4f} ± {results_df['f1_score'].std():.4f}")


if __name__ == '__main__':
    main()
