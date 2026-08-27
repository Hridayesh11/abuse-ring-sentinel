from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

from models.baseline import (
    FEATURE_COLUMNS,
    load_dataset,
    train_logistic_baseline,
)

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


def add_entity_noise(
    dataset: pd.DataFrame,
    noise_level: float,
    random_state: int = 42,
) -> pd.DataFrame:
    """Add controlled noise to entity-linkage features.

    Noise is applied only to normal accounts. This simulates
    legitimate accounts sharing infrastructure without changing
    the underlying labels.
    """

    if not 0.0 <= noise_level <= 1.0:
        raise ValueError(
            "noise_level must be between 0.0 and 1.0"
        )

    noisy_dataset = dataset.copy()

    rng = __import__("numpy").random.default_rng(
        random_state
    )

    normal_mask = noisy_dataset["label"] == 0

    entity_features = [
        "shared_device_count",
        "shared_ip_count",
        "shared_address_count",
        "shared_payment_count",
        "multi_signal_link_count",
    ]

    for feature in entity_features:
        mask = normal_mask & (
            rng.random(len(noisy_dataset))
            < noise_level
        )

        noisy_dataset.loc[mask, feature] += 1

    return noisy_dataset


def evaluate_dataset(
    dataset: pd.DataFrame,
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, float]:
    """Evaluate logistic regression using stratified cross-validation."""

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    metrics = {
        "accuracy": [],
        "precision": [],
        "recall": [],
        "f1": [],
        "roc_auc": [],
    }

    for train_index, test_index in validator.split(X, y):
        X_train = X.iloc[train_index]
        X_test = X.iloc[test_index]

        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]

        model = train_logistic_baseline(
            X_train,
            y_train,
        )

        predictions = model.predict(X_test)
        probabilities = model.predict_proba(
            X_test
        )[:, 1]

        metrics["accuracy"].append(
            accuracy_score(
                y_test,
                predictions,
            )
        )

        metrics["precision"].append(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        metrics["recall"].append(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        metrics["f1"].append(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        metrics["roc_auc"].append(
            roc_auc_score(
                y_test,
                probabilities,
            )
        )

    return {
        metric: round(
            sum(values) / len(values),
            4,
        )
        for metric, values in metrics.items()
    }


def run_robustness_analysis(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Evaluate model performance under increasing entity noise."""

    dataset = load_dataset(
        dataset_path
    )

    noise_levels = [
        0.0,
        0.10,
        0.20,
        0.30,
        0.40,
        0.50,
    ]

    results = []

    for noise_level in noise_levels:
        noisy_dataset = add_entity_noise(
            dataset,
            noise_level=noise_level,
        )

        metrics = evaluate_dataset(
            noisy_dataset
        )

        results.append(
            {
                "noise_level": noise_level,
                **metrics,
            }
        )

    return pd.DataFrame(results)


if __name__ == "__main__":
    results = run_robustness_analysis()

    print("\nRobustness Analysis — Entity Noise")
    print("=" * 60)

    print(
        results.to_string(
            index=False
        )
    )