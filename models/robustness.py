from __future__ import annotations

from pathlib import Path

import numpy as np
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


ENTITY_FEATURES = [
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
]


GRAPH_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "reciprocity",
    "community_size",
    "internal_degree",
]


def add_entity_noise(
    dataset: pd.DataFrame,
    noise_level: float,
    random_state: int = 42,
) -> pd.DataFrame:
    """Add controlled entity-linkage noise to normal accounts."""

    if not 0.0 <= noise_level <= 1.0:
        raise ValueError(
            "noise_level must be between 0.0 and 1.0"
        )

    noisy_dataset = dataset.copy()

    rng = np.random.default_rng(
        random_state
    )

    normal_mask = noisy_dataset["label"] == 0

    for feature in ENTITY_FEATURES:
        mask = normal_mask & (
            rng.random(len(noisy_dataset))
            < noise_level
        )

        noisy_dataset.loc[mask, feature] += 1

    return noisy_dataset


def add_hard_negative_noise(
    dataset: pd.DataFrame,
    difficulty: float,
    random_state: int = 42,
) -> pd.DataFrame:
    """Create legitimate accounts with abuse-like characteristics.

    Hard negatives remain label 0 but receive suspicious-looking
    behavioral, graph, and entity features.
    """

    if not 0.0 <= difficulty <= 1.0:
        raise ValueError(
            "difficulty must be between 0.0 and 1.0"
        )

    hard_negative_dataset = dataset.copy()

    rng = np.random.default_rng(
        random_state
    )

    normal_indices = hard_negative_dataset.index[
        hard_negative_dataset["label"] == 0
    ].tolist()

    if not normal_indices:
        return hard_negative_dataset

    hard_negative_count = max(
        1,
        int(len(normal_indices) * difficulty),
    )

    selected_indices = rng.choice(
        normal_indices,
        size=min(
            hard_negative_count,
            len(normal_indices),
        ),
        replace=False,
    )

    for index in selected_indices:

        # --------------------------------------------------
        # Entity-linkage signals
        # --------------------------------------------------

        hard_negative_dataset.loc[
            index,
            "shared_device_count",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "shared_device_count",
            ],
            2,
        )

        hard_negative_dataset.loc[
            index,
            "shared_ip_count",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "shared_ip_count",
            ],
            2,
        )

        hard_negative_dataset.loc[
            index,
            "shared_payment_count",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "shared_payment_count",
            ],
            2,
        )

        hard_negative_dataset.loc[
            index,
            "multi_signal_link_count",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "multi_signal_link_count",
            ],
            2,
        )

        # --------------------------------------------------
        # Behavioral signals
        # --------------------------------------------------

        current_transaction_count = int(
            hard_negative_dataset.loc[
                index,
                "transaction_count",
            ]
        )

        hard_negative_dataset.loc[
            index,
            "transaction_count",
        ] = int(
            round(current_transaction_count * 1.5)
        )

        hard_negative_dataset.loc[
            index,
            "total_sent",
        ] *= 1.4

        hard_negative_dataset.loc[
            index,
            "total_received",
        ] *= 1.4

        hard_negative_dataset.loc[
            index,
            "active_days",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "active_days",
            ],
            5,
        )

        hard_negative_dataset.loc[
            index,
            "transactions_per_active_day",
        ] = (
            hard_negative_dataset.loc[
                index,
                "transaction_count",
            ]
            / max(
                hard_negative_dataset.loc[
                    index,
                    "active_days",
                ],
                1,
            )
        )

        # --------------------------------------------------
        # Graph signals
        # --------------------------------------------------

        hard_negative_dataset.loc[
            index,
            "in_degree",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "in_degree",
            ],
            2,
        )

        hard_negative_dataset.loc[
            index,
            "out_degree",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "out_degree",
            ],
            2,
        )

        hard_negative_dataset.loc[
            index,
            "total_degree",
        ] = (
            hard_negative_dataset.loc[
                index,
                "in_degree",
            ]
            + hard_negative_dataset.loc[
                index,
                "out_degree",
            ]
        )

        hard_negative_dataset.loc[
            index,
            "reciprocity",
        ] = max(
            hard_negative_dataset.loc[
                index,
                "reciprocity",
            ],
            0.2,
        )

    return hard_negative_dataset


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

        predictions = model.predict(
            X_test
        )

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


def run_hard_negative_analysis(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Evaluate performance as legitimate hard negatives increase."""

    dataset = load_dataset(
        dataset_path
    )

    difficulty_levels = [
        0.0,
        0.10,
        0.20,
        0.30,
        0.40,
        0.50,
    ]

    results = []

    for difficulty in difficulty_levels:

        modified_dataset = add_hard_negative_noise(
            dataset,
            difficulty=difficulty,
        )

        metrics = evaluate_dataset(
            modified_dataset
        )

        results.append(
            {
                "difficulty": difficulty,
                **metrics,
            }
        )

    return pd.DataFrame(results)


def run_combined_robustness_analysis(
    dataset_path: Path | str = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Evaluate robustness under combined entity and hard-negative noise."""

    dataset = load_dataset(
        dataset_path
    )

    difficulty_levels = [
        0.0,
        0.10,
        0.20,
        0.30,
        0.40,
        0.50,
    ]

    results = []

    for difficulty in difficulty_levels:

        modified_dataset = add_entity_noise(
            dataset,
            noise_level=difficulty,
        )

        modified_dataset = add_hard_negative_noise(
            modified_dataset,
            difficulty=difficulty,
        )

        metrics = evaluate_dataset(
            modified_dataset
        )

        results.append(
            {
                "difficulty": difficulty,
                **metrics,
            }
        )

    return pd.DataFrame(results)


if __name__ == "__main__":

    print(
        "\nRobustness Analysis — Hard Negatives"
    )

    print("=" * 60)

    hard_negative_results = (
        run_hard_negative_analysis()
    )

    print(
        hard_negative_results.to_string(
            index=False
        )
    )

    print(
        "\n\nRobustness Analysis — Combined Noise"
    )

    print("=" * 60)

    combined_results = (
        run_combined_robustness_analysis()
    )

    print(
        combined_results.to_string(
            index=False
        )
    )