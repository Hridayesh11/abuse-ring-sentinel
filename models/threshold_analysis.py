from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from models.baseline import (
    FEATURE_COLUMNS,
    load_dataset,
    train_logistic_baseline,
)

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)

DEFAULT_THRESHOLDS = [
    round(0.20 + index * 0.05, 2)
    for index in range(13)
]


def get_test_probabilities(
    dataset: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[pd.Series, pd.Series]:
    """Train the baseline model and return test labels and probabilities."""

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = train_logistic_baseline(
        X_train,
        y_train,
    )

    probabilities = pd.Series(
        model.predict_proba(X_test)[:, 1],
        index=y_test.index,
    )

    return y_test, probabilities


def evaluate_threshold(
    y_true: pd.Series,
    probabilities: pd.Series,
    threshold: float,
) -> dict[str, float]:
    """Evaluate classification metrics at a probability threshold."""

    predictions = (
        probabilities >= threshold
    ).astype(int)

    return {
        "threshold": threshold,
        "accuracy": round(
            accuracy_score(
                y_true,
                predictions,
            ),
            4,
        ),
        "precision": round(
            precision_score(
                y_true,
                predictions,
                zero_division=0,
            ),
            4,
        ),
        "recall": round(
            recall_score(
                y_true,
                predictions,
                zero_division=0,
            ),
            4,
        ),
        "f1": round(
            f1_score(
                y_true,
                predictions,
                zero_division=0,
            ),
            4,
        ),
    }


def run_threshold_analysis(
    dataset: pd.DataFrame,
    thresholds: list[float] | None = None,
    test_size: float = 0.20,
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate the logistic model across classification thresholds."""

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    if not thresholds:
        raise ValueError(
            "At least one threshold is required"
        )

    if any(
        threshold <= 0 or threshold >= 1
        for threshold in thresholds
    ):
        raise ValueError(
            "Thresholds must be between 0 and 1"
        )

    y_test, probabilities = get_test_probabilities(
        dataset,
        test_size=test_size,
        random_state=random_state,
    )

    results = [
        evaluate_threshold(
            y_test,
            probabilities,
            threshold,
        )
        for threshold in thresholds
    ]

    return pd.DataFrame(results)


def select_best_threshold(
    results: pd.DataFrame,
) -> pd.Series:
    """Select the best threshold using F1, precision, recall and accuracy."""

    required_columns = {
        "threshold",
        "accuracy",
        "precision",
        "recall",
        "f1",
    }

    missing_columns = (
        required_columns - set(results.columns)
    )

    if missing_columns:
        raise ValueError(
            "Threshold results are missing required columns: "
            f"{sorted(missing_columns)}"
        )

    ranked_results = results.sort_values(
        by=[
            "f1",
            "precision",
            "recall",
            "accuracy",
            "threshold",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            True,
        ],
    )

    return ranked_results.iloc[0]


def run_analysis(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> tuple[pd.DataFrame, pd.Series]:
    """Run the complete threshold analysis."""

    dataset = load_dataset(
        dataset_path
    )

    results = run_threshold_analysis(
        dataset
    )

    best_threshold = select_best_threshold(
        results
    )

    return results, best_threshold


if __name__ == "__main__":
    results, best_threshold = run_analysis()

    print("\nThreshold Analysis")
    print("=" * 60)

    print(
        results.to_string(
            index=False
        )
    )

    print("\n\nSelected Threshold")
    print("=" * 60)

    print(
        f"  threshold : "
        f"{best_threshold['threshold']:.2f}"
    )

    print(
        f"  accuracy  : "
        f"{best_threshold['accuracy']:.4f}"
    )

    print(
        f"  precision : "
        f"{best_threshold['precision']:.4f}"
    )

    print(
        f"  recall    : "
        f"{best_threshold['recall']:.4f}"
    )

    print(
        f"  f1        : "
        f"{best_threshold['f1']:.4f}"
    )