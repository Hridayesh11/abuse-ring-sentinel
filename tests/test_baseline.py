import pandas as pd
import pytest

from models.baseline import (
    BEHAVIORAL_FEATURES,
    FEATURE_COLUMNS,
    RING_LINKAGE_FEATURES,
    analyze_feature_importance,
    evaluate_model,
    load_dataset,
    run_baseline,
    run_feature_ablation,
    run_k_fold_cross_validation,
    split_dataset,
    train_dummy_baseline,
    train_logistic_baseline,
)

DATASET_PATH = "datasets/abuse_ring_dataset.csv"


def test_load_dataset_returns_dataframe():
    dataset = load_dataset(DATASET_PATH)

    assert isinstance(dataset, pd.DataFrame)
    assert not dataset.empty


def test_load_dataset_contains_required_features():
    dataset = load_dataset(DATASET_PATH)

    assert set(FEATURE_COLUMNS).issubset(dataset.columns)
    assert "account_id" in dataset.columns
    assert "label" in dataset.columns


def test_load_dataset_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        load_dataset("datasets/does_not_exist.csv")


def test_split_dataset_preserves_features_and_labels():
    dataset = load_dataset(DATASET_PATH)

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    assert list(X_train.columns) == FEATURE_COLUMNS
    assert list(X_test.columns) == FEATURE_COLUMNS

    assert len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)

    assert len(X_train) + len(X_test) == len(dataset)


def test_dummy_baseline_is_fitted():
    dataset = load_dataset(DATASET_PATH)

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    model = train_dummy_baseline(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    assert len(predictions) == len(X_test)
    assert probabilities.shape[0] == len(X_test)
    assert probabilities.shape[1] == 2


def test_logistic_baseline_is_fitted():
    dataset = load_dataset(DATASET_PATH)

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    model = train_logistic_baseline(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)

    assert len(predictions) == len(X_test)
    assert probabilities.shape == (len(X_test), 2)

    assert "scaler" in model.named_steps
    assert "classifier" in model.named_steps


def test_evaluate_model_returns_expected_metrics():
    dataset = load_dataset(DATASET_PATH)

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    model = train_logistic_baseline(X_train, y_train)

    metrics = evaluate_model(model, X_test, y_test)

    expected_metrics = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    }

    assert set(metrics) == expected_metrics

    for value in metrics.values():
        assert 0.0 <= value <= 1.0


def test_run_baseline_returns_both_models():
    results = run_baseline(DATASET_PATH)

    assert set(results) == {
        "dummy",
        "logistic_regression",
    }

    expected_metrics = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    }

    for model_metrics in results.values():
        assert set(model_metrics) == expected_metrics


def test_k_fold_cross_validation_returns_both_models():
    dataset = load_dataset(DATASET_PATH)

    results = run_k_fold_cross_validation(
        dataset,
        n_splits=5,
    )

    assert set(results) == {
        "dummy",
        "logistic_regression",
    }

    expected_metrics = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    }

    for model_metrics in results.values():
        assert set(model_metrics) == expected_metrics

        for value in model_metrics.values():
            assert 0.0 <= value <= 1.0


def test_feature_ablation_returns_expected_groups():
    dataset = load_dataset(DATASET_PATH)

    feature_groups = {
        "behavioral_only": BEHAVIORAL_FEATURES,
        "ring_linkage_only": RING_LINKAGE_FEATURES,
        "full_model": FEATURE_COLUMNS,
    }

    results = run_feature_ablation(
        dataset,
        feature_groups,
        n_splits=5,
    )

    assert set(results) == {
        "behavioral_only",
        "ring_linkage_only",
        "full_model",
    }

    expected_metrics = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
    }

    for model_metrics in results.values():
        assert set(model_metrics) == expected_metrics

        for value in model_metrics.values():
            assert 0.0 <= value <= 1.0


def test_feature_importance_contains_all_features():
    dataset = load_dataset(DATASET_PATH)

    importance = analyze_feature_importance(dataset)

    assert list(importance.columns) == [
        "feature",
        "coefficient",
        "absolute_importance",
    ]

    assert set(importance["feature"]) == set(FEATURE_COLUMNS)

    assert len(importance) == len(FEATURE_COLUMNS)


def test_feature_importance_is_sorted():
    dataset = load_dataset(DATASET_PATH)

    importance = analyze_feature_importance(dataset)

    values = importance["absolute_importance"].tolist()

    assert values == sorted(values, reverse=True)