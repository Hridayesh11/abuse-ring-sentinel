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
from xgboost import XGBClassifier

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


GRAPH_ENTITY_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "community_size",
    "internal_degree",
    "shared_device_count",
    "shared_ip_count",
    "shared_address_count",
    "shared_payment_count",
    "multi_signal_link_count",
]


def load_dataset(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Load and validate the dataset."""

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    dataset = pd.read_csv(dataset_path)

    required_columns = {
        "account_id",
        "label",
        *GRAPH_ENTITY_FEATURES,
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


def evaluate_model(
    model,
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, float]:
    """Evaluate a model using stratified 5-fold CV."""

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

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

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


def build_models(
    random_state: int = 42,
) -> dict[str, object]:
    """Create the models used for comparison."""

    return {
        "logistic_regression": Pipeline(
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
        ),
        "xgboost": XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=random_state,
        ),
    }


def run_comparison(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> dict[str, dict[str, float]]:
    """Compare models using graph + entity features."""

    dataset = load_dataset(dataset_path)

    X = dataset[GRAPH_ENTITY_FEATURES]
    y = dataset["label"]

    models = build_models()

    results: dict[str, dict[str, float]] = {}

    for model_name, model in models.items():
        results[model_name] = evaluate_model(
            model,
            X,
            y,
        )

    return results


if __name__ == "__main__":
    results = run_comparison()

    print("\nModel Comparison — Graph + Entity Features")
    print("=" * 60)

    for model_name, metrics in results.items():
        print(f"\n{model_name}")

        for metric_name, value in metrics.items():
            print(
                f"  {metric_name:10s}: {value:.4f}"
            )