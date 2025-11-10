import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def compare_models_ttest(results_model1, results_model2, metric='accuracy'):
    """
    Perform paired t-test between two models

    Args:
        results_model1: dict or DataFrame with results from model 1
        results_model2: dict or DataFrame with results from model 2
        metric: metric to compare (e.g., 'accuracy', 'f1_score')

    Returns:
        dict with statistical test results
    """
    scores1 = results_model1[metric].values if isinstance(results_model1, pd.DataFrame) else results_model1[metric]
    scores2 = results_model2[metric].values if isinstance(results_model2, pd.DataFrame) else results_model2[metric]

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(scores1, scores2)

    # Effect size (Cohen's d)
    diff = scores1 - scores2
    cohens_d = np.mean(diff) / np.std(diff)

    result = {
        't_statistic': t_stat,
        'p_value': p_value,
        'cohens_d': cohens_d,
        'mean_diff': np.mean(diff),
        'std_diff': np.std(diff),
        'significant': p_value < 0.05,
        'interpretation': 'Model 1 is significantly better' if (t_stat > 0 and p_value < 0.05)
        else 'Model 2 is significantly better' if (t_stat < 0 and p_value < 0.05)
        else 'No significant difference'
    }

    return result


def wilcoxon_test(results_model1, results_model2, metric='accuracy'):
    """Non-parametric alternative to paired t-test"""
    scores1 = results_model1[metric].values if isinstance(results_model1, pd.DataFrame) else results_model1[metric]
    scores2 = results_model2[metric].values if isinstance(results_model2, pd.DataFrame) else results_model2[metric]

    w_stat, p_value = stats.wilcoxon(scores1, scores2)

    return {
        'w_statistic': w_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }


def create_pvalue_heatmap(comparison_matrix, model_names, save_path='static/pvalue_heatmap.png'):
    """
    Create heatmap of p-values from multiple model comparisons

    Args:
        comparison_matrix: 2D array of p-values
        model_names: list of model names
    """
    plt.figure(figsize=(10, 8))

    # Create mask for diagonal
    mask = np.eye(len(model_names), dtype=bool)

    sns.heatmap(
        comparison_matrix,
        annot=True,
        fmt='.4f',
        cmap='RdYlGn_r',
        xticklabels=model_names,
        yticklabels=model_names,
        mask=mask,
        cbar_kws={'label': 'p-value'},
        vmin=0,
        vmax=0.1
    )

    plt.title('Statistical Significance Heatmap\n(p-values from paired t-tests)', fontsize=14)
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Model', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    return save_path
