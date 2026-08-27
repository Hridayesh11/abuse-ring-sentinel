from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from models.baseline import (
    BEHAVIORAL_FEATURES,
    FEATURE_COLUMNS,
    RING_LINKAGE_FEATURES,
    load_dataset,
)


DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


def feature_label_correlation(
    dataset: pd.DataFrame,
) -> pd.DataFrame:
    """Measure correlation between every feature and the abuse label."""

    rows = []

    for feature in FEATURE_COLUMNS:
        correlation = dataset[feature].corr(
            dataset["label"]
        )

        rows.append(
            {
                "feature": feature,
                "label_correlation": correlation,
                "absolute_correlation": abs(correlation),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            "absolute_correlation",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def evaluate_feature_group(
    dataset: pd.DataFrame,
    features: list[str],
    n_splits: int = 5,
    random_state: int = 42,
) -> float:
    """Evaluate a feature group using stratified CV."""

    X = dataset[features]
    y = dataset["label"]

    model = Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=5000,
                    class_weight="balanced",
                    random_state=random_state,
                ),
            ),
        ]
    )

    validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    scores = cross_val_score(
        model,
        X,
        y,
        cv=validator,
        scoring="roc_auc",
    )

    return round(
        scores.mean(),
        4,
    )


def run_leakage_audit(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> dict[str, float]:
    """Run basic synthetic-data leakage checks."""

    dataset = load_dataset(dataset_path)

    return {
        "behavioral_only": evaluate_feature_group(
            dataset,
            BEHAVIORAL_FEATURES,
        ),
        "ring_linkage_only": evaluate_feature_group(
            dataset,
            RING_LINKAGE_FEATURES,
        ),
        "full_model": evaluate_feature_group(
            dataset,
            FEATURE_COLUMNS,
        ),
    }


if __name__ == "__main__":
    dataset = load_dataset()

    print("\nFeature / Label Correlation")
    print("=" * 60)

    correlation = feature_label_correlation(
        dataset
    )

    print(
        correlation.to_string(
            index=False
        )
    )

    print("\n\nFeature Group ROC-AUC")
    print("=" * 60)

    results = run_leakage_audit()

    for group_name, score in results.items():
        print(
            f"{group_name:25s}: {score:.4f}"
        )