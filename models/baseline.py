from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_DATASET_PATH = Path(
    "datasets/abuse_ring_dataset.csv"
)


FEATURE_COLUMNS = [
    "transaction_count",
    "total_sent",
    "total_received",
    "average_sent",
    "average_received",
    "active_days",
    "transactions_per_active_day",
    "activity_span_hours",
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
BEHAVIORAL_FEATURES = [
    "transaction_count",
    "total_sent",
    "total_received",
    "average_sent",
    "average_received",
    "active_days",
    "transactions_per_active_day",
    "activity_span_hours",
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "community_size",
    "internal_degree",
]

RING_LINKAGE_FEATURES = [
    "shared_device_count",
    "shared_ip_count",
    "shared_address_count",
    "shared_payment_count",
    "multi_signal_link_count",
]


def load_dataset(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Load and validate the generated ML dataset."""

    dataset_path = Path(dataset_path)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    dataset = pd.read_csv(dataset_path)

    required_columns = {
        "account_id",
        "label",
        *FEATURE_COLUMNS,
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


def split_dataset(
    dataset: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
]:
    """Create a stratified train/test split."""

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """Evaluate a binary classification model."""

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    return {
        "accuracy": round(
            accuracy_score(
                y_test,
                predictions,
            ),
            4,
        ),
        "precision": round(
            precision_score(
                y_test,
                predictions,
                zero_division=0,
            ),
            4,
        ),
        "recall": round(
            recall_score(
                y_test,
                predictions,
                zero_division=0,
            ),
            4,
        ),
        "f1": round(
            f1_score(
                y_test,
                predictions,
                zero_division=0,
            ),
            4,
        ),
        "roc_auc": round(
            roc_auc_score(
                y_test,
                probabilities,
            ),
            4,
        ),
    }


def train_dummy_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> DummyClassifier:
    """Train a majority-class dummy baseline."""

    model = DummyClassifier(
        strategy="most_frequent",
    )

    model.fit(
        X_train,
        y_train,
    )

    return model


def train_logistic_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Pipeline:
    """Train a scaled logistic-regression baseline."""

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
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(
        X_train,
        y_train,
    )

    return model


def run_baseline(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> dict[str, dict[str, float]]:
    """Run both baseline models and return their metrics."""

    dataset = load_dataset(
        dataset_path
    )

    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = split_dataset(
        dataset
    )

    dummy_model = train_dummy_baseline(
        X_train,
        y_train,
    )

    logistic_model = train_logistic_baseline(
        X_train,
        y_train,
    )

    dummy_metrics = evaluate_model(
        dummy_model,
        X_test,
        y_test,
    )

    logistic_metrics = evaluate_model(
        logistic_model,
        X_test,
        y_test,
    )

    return {
        "dummy": dummy_metrics,
        "logistic_regression": logistic_metrics,
    }


def run_k_fold_cross_validation(
    dataset: pd.DataFrame,
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, dict[str, float]]:
    """Evaluate baseline models using stratified K-fold cross-validation."""

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    cross_validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    model_scores: dict[
        str,
        dict[str, list[float]],
    ] = {
        "dummy": {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": [],
            "roc_auc": [],
        },
        "logistic_regression": {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": [],
            "roc_auc": [],
        },
    }

    for train_index, test_index in cross_validator.split(
        X,
        y,
    ):
        X_train = X.iloc[train_index]
        X_test = X.iloc[test_index]

        y_train = y.iloc[train_index]
        y_test = y.iloc[test_index]

        dummy_model = train_dummy_baseline(
            X_train,
            y_train,
        )

        logistic_model = train_logistic_baseline(
            X_train,
            y_train,
        )

        dummy_metrics = evaluate_model(
            dummy_model,
            X_test,
            y_test,
        )

        logistic_metrics = evaluate_model(
            logistic_model,
            X_test,
            y_test,
        )

        for metric_name, value in dummy_metrics.items():
            model_scores["dummy"][
                metric_name
            ].append(value)

        for metric_name, value in logistic_metrics.items():
            model_scores["logistic_regression"][
                metric_name
            ].append(value)

    averaged_scores: dict[
        str,
        dict[str, float],
    ] = {}

    for model_name, metrics in model_scores.items():
        averaged_scores[model_name] = {
            metric_name: round(
                sum(values) / len(values),
                4,
            )
            for metric_name, values in metrics.items()
        }

    return averaged_scores

def run_feature_ablation(
    dataset: pd.DataFrame,
    feature_groups: dict[str, list[str]],
    n_splits: int = 5,
    random_state: int = 42,
) -> dict[str, dict[str, float]]:
    """Evaluate logistic regression using different feature groups."""

    y = dataset["label"]

    cross_validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    results: dict[str, dict[str, float]] = {}

    for group_name, features in feature_groups.items():
        X = dataset[features]

        fold_metrics: dict[str, list[float]] = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": [],
            "roc_auc": [],
        }

        for train_index, test_index in cross_validator.split(
            X,
            y,
        ):
            X_train = X.iloc[train_index]
            X_test = X.iloc[test_index]

            y_train = y.iloc[train_index]
            y_test = y.iloc[test_index]

            model = train_logistic_baseline(
                X_train,
                y_train,
            )

            metrics = evaluate_model(
                model,
                X_test,
                y_test,
            )

            for metric_name, value in metrics.items():
                fold_metrics[metric_name].append(value)

        results[group_name] = {
            metric_name: round(
                sum(values) / len(values),
                4,
            )
            for metric_name, values in fold_metrics.items()
        }

    return results


def analyze_feature_importance(
    dataset: pd.DataFrame,
) -> pd.DataFrame:
    """Analyze logistic-regression feature importance."""

    X = dataset[FEATURE_COLUMNS]
    y = dataset["label"]

    model = train_logistic_baseline(
        X,
        y,
    )

    classifier = model.named_steps["classifier"]

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "coefficient": classifier.coef_[0],
        }
    )

    importance["absolute_importance"] = (
        importance["coefficient"].abs()
    )

    importance = importance.sort_values(
        "absolute_importance",
        ascending=False,
    ).reset_index(
        drop=True
    )

    return importance


if __name__ == "__main__":
    results = run_baseline()

    print("\nBaseline evaluation")
    print("=" * 60)

    for model_name, metrics in results.items():
        print(f"\n{model_name}")

        for metric_name, value in metrics.items():
            print(
                f"  {metric_name:10s}: {value:.4f}"
            )

    dataset = load_dataset()

    cv_results = run_k_fold_cross_validation(
        dataset
    )

    print("\n\n5-Fold Cross-Validation")
    print("=" * 60)

    for model_name, metrics in cv_results.items():
        print(f"\n{model_name}")

        for metric_name, value in metrics.items():
            print(
                f"  {metric_name:10s}: {value:.4f}"
            )

    feature_importance = analyze_feature_importance(
        dataset
    )

    print("\n\nFeature Importance")
    print("=" * 60)

    print(
        feature_importance.to_string(
            index=False
        )
    )
    feature_groups = {
        "behavioral_only": BEHAVIORAL_FEATURES,
        "ring_linkage_only": RING_LINKAGE_FEATURES,
        "full_model": FEATURE_COLUMNS,
    }

    ablation_results = run_feature_ablation(
        dataset,
        feature_groups,
    )

    print("\n\nFeature Ablation")
    print("=" * 60)

    for group_name, metrics in ablation_results.items():
        print(f"\n{group_name}")

        for metric_name, value in metrics.items():
            print(
                f"  {metric_name:10s}: {value:.4f}"
            )
