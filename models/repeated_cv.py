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
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from models.ablation import ENTITY_FEATURES, GRAPH_FEATURES, load_dataset

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)

BEST_FEATURES = GRAPH_FEATURES + ENTITY_FEATURES


def run_repeated_cv(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
    n_splits: int = 5,
    n_repeats: int = 5,
    random_state: int = 42,
) -> dict[str, dict[str, float]]:
    """Evaluate the selected feature set using repeated stratified CV."""

    dataset = load_dataset(dataset_path)

    X = dataset[BEST_FEATURES]
    y = dataset["label"]

    cross_validator = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=n_repeats,
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

        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

        scores["accuracy"].append(
            accuracy_score(y_test, predictions)
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

    results = {}

    for metric, values in scores.items():
        results[metric] = {
            "mean": round(sum(values) / len(values), 4),
            "std": round(pd.Series(values).std(ddof=1), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    return results


if __name__ == "__main__":
    results = run_repeated_cv()

    print("\nRepeated Stratified Cross-Validation")
    print("=" * 60)

    print("Configuration")
    print("-" * 60)
    print("Folds    : 5")
    print("Repeats  : 5")
    print("Runs     : 25")

    print("\nResults")
    print("-" * 60)

    for metric, values in results.items():
        print(
            f"{metric:10s}: "
            f"mean={values['mean']:.4f}  "
            f"std={values['std']:.4f}  "
            f"min={values['min']:.4f}  "
            f"max={values['max']:.4f}"
        )