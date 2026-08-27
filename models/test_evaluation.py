from __future__ import annotations

from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from models.ablation import ENTITY_FEATURES, GRAPH_FEATURES, load_dataset

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)

BEST_FEATURES = GRAPH_FEATURES + ENTITY_FEATURES


def evaluate_test_set(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
    random_state: int = 42,
) -> None:
    """Evaluate the selected model on a held-out test set."""

    dataset = load_dataset(dataset_path)

    X = dataset[BEST_FEATURES]
    y = dataset["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=random_state,
    )

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

    print("\nHeld-Out Test Evaluation")
    print("=" * 60)

    print(f"Training samples : {len(X_train)}")
    print(f"Test samples     : {len(X_test)}")

    print("\nMetrics")
    print("-" * 60)

    print(
        f"accuracy  : {accuracy_score(y_test, predictions):.4f}"
    )
    print(
        f"precision : {precision_score(y_test, predictions, zero_division=0):.4f}"
    )
    print(
        f"recall    : {recall_score(y_test, predictions, zero_division=0):.4f}"
    )
    print(
        f"f1        : {f1_score(y_test, predictions, zero_division=0):.4f}"
    )
    print(
        f"roc_auc   : {roc_auc_score(y_test, probabilities):.4f}"
    )

    print("\nConfusion Matrix")
    print("-" * 60)
    print(confusion_matrix(y_test, predictions))

    print("\nClassification Report")
    print("-" * 60)
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["normal", "abuse"],
            zero_division=0,
        )
    )

    results = dataset.loc[
        X_test.index,
        ["account_id", "label"],
    ].copy()

    results["prediction"] = predictions
    results["abuse_probability"] = probabilities.round(4)

    results["error_type"] = "correct"

    results.loc[
        (results["label"] == 0)
        & (results["prediction"] == 1),
        "error_type",
    ] = "false_positive"

    results.loc[
        (results["label"] == 1)
        & (results["prediction"] == 0),
        "error_type",
    ] = "false_negative"

    print("\nPrediction Details")
    print("-" * 60)
    print(
        results.sort_values(
            "abuse_probability",
            ascending=False,
        ).to_string(index=False)
    )

    errors = results[
        results["error_type"] != "correct"
    ]

    print("\nErrors")
    print("-" * 60)

    if errors.empty:
        print("No false positives or false negatives.")
    else:
        print(errors.to_string(index=False))


if __name__ == "__main__":
    evaluate_test_set()