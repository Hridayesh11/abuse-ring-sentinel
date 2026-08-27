from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


BEHAVIORAL_FEATURES = [
    "transaction_count",
    "total_sent",
    "total_received",
    "average_sent",
    "average_received",
]


TEMPORAL_FEATURES = [
    "active_days",
    "transactions_per_active_day",
    "activity_span_hours",
]


GRAPH_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "community_size",
    "internal_degree",
]


ENTITY_FEATURES = [
    "shared_device_count",
    "shared_ip_count",
    "shared_address_count",
    "shared_payment_count",
    "multi_signal_link_count",
]


ALL_FEATURES = (
    BEHAVIORAL_FEATURES
    + TEMPORAL_FEATURES
    + GRAPH_FEATURES
    + ENTITY_FEATURES
)


FEATURE_GROUPS = {
    "behavioral_only": BEHAVIORAL_FEATURES,
    "temporal_only": TEMPORAL_FEATURES,
    "graph_only": GRAPH_FEATURES,
    "entity_only": ENTITY_FEATURES,
    "behavioral_graph": (
        BEHAVIORAL_FEATURES
        + GRAPH_FEATURES
    ),
    "behavioral_temporal": (
        BEHAVIORAL_FEATURES
        + TEMPORAL_FEATURES
    ),
    "graph_entity": (
        GRAPH_FEATURES
        + ENTITY_FEATURES
    ),
    "without_behavioral_features": (
        TEMPORAL_FEATURES
        + GRAPH_FEATURES
        + ENTITY_FEATURES
    ),
    "without_temporal_features": (
        BEHAVIORAL_FEATURES
        + GRAPH_FEATURES
        + ENTITY_FEATURES
    ),
    "without_graph_features": (
        BEHAVIORAL_FEATURES
        + TEMPORAL_FEATURES
        + ENTITY_FEATURES
    ),
    "without_entity_features": (
        BEHAVIORAL_FEATURES
        + TEMPORAL_FEATURES
        + GRAPH_FEATURES
    ),
    "all_features": ALL_FEATURES,
}


def load_dataset(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Load and validate the generated dataset."""

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    dataset = pd.read_csv(dataset_path)

    required_columns = {
        "account_id",
        "label",
        *ALL_FEATURES,
    }

    missing_columns = (
        required_columns - set(dataset.columns)
    )

    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    if dataset["label"].isna().any():
        raise ValueError(
            "Dataset contains missing labels"
        )

    if dataset["label"].nunique() < 2:
        raise ValueError(
            "Dataset must contain at least two classes"
        )

    return dataset


def evaluate_feature_group(
    dataset: pd.DataFrame,
    feature_columns: list[str],
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, float]:
    """Evaluate one feature group using stratified 5-fold CV."""

    X = dataset[feature_columns]
    y = dataset["label"]

    cross_validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    scores = {
        "accuracy": [],
        "precision": [],
        "recall": [],
        "f1": [],
        "roc_auc": [],
    }

    for train_index, test_index in cross_validator.split(X, y):
        X_train = X.iloc[train_index]
        X_test = X.iloc[test_index]

        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]

        model = Pipeline(
    [
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=random_state,
            ),
        ),
    ]
)

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(X_test)

        probabilities = model.predict_proba(
            X_test
        )[:, 1]

        scores["accuracy"].append(
            accuracy_score(
                y_test,
                predictions,
            )
        )

        scores["precision"].append(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        scores["recall"].append(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        scores["f1"].append(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            )
        )

        scores["roc_auc"].append(
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
        for metric, values in scores.items()
    }


def run_ablation(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> dict[str, dict[str, float]]:
    """Run all feature-ablation experiments."""

    dataset = load_dataset(
        dataset_path
    )

    results: dict[str, dict[str, float]] = {}

    for group_name, feature_columns in FEATURE_GROUPS.items():
        results[group_name] = evaluate_feature_group(
            dataset,
            feature_columns,
        )

    return results


if __name__ == "__main__":
    results = run_ablation()

    print("\nFeature Ablation Study")
    print("=" * 60)

    for group_name, metrics in results.items():
        print(f"\n{group_name}")

        for metric_name, value in metrics.items():
            print(
                f"  {metric_name:10s}: {value:.4f}"
            )