from pathlib import Path

import pandas as pd
import pytest

from mlops_team1.evaluate import classification_metrics
from mlops_team1.train import train_model
from mlops_team1.validate_data import validate_dataset


@pytest.fixture
def delays_14_and_15(valid_frame: pd.DataFrame, csv_factory) -> Path:
    """Набор, где ArrDelay чередуется между 15 (опоздание) и 14 (нет).

    Оба значения лежат по обе стороны границы, поэтому оба класса попадают
    в каждую хронологическую часть (14/5/5 строк).
    """
    frame = valid_frame.copy()
    frame["ArrDelay"] = [15 if i % 2 == 0 else 14 for i in range(len(frame))]
    return csv_factory(frame)


def test_arrdelay_15_counts_as_late_in_training(delays_14_and_15: Path, tmp_path: Path) -> None:
    roc_auc = train_model(delays_14_and_15, tmp_path / "model.joblib")

    assert 0.0 <= roc_auc <= 1.0, (
        f"ROC AUC вне диапазона 0..1: {roc_auc}. Если граница цели стала '> 15', "
        "все метки равны 0 и обучение должно было бы отказать"
    )


def test_arrdelay_15_counts_as_late_in_validator_report(
    delays_14_and_15: Path, contract_path: Path
) -> None:
    report = validate_dataset(delays_14_and_15, contract_path)

    parts = report["split"]["parts"]
    rates = [parts[name]["positive_rate"] for name in ("train", "validation", "test")]
    assert rates == [0.5, 0.6, 0.4], (
        f"Доли опоздавших в train, validation, test: {rates}, ожидалось [0.5, 0.6, 0.4]. "
        "Значение 15 должно считаться опозданием, 14 нет"
    )


def test_probability_equal_to_threshold_is_positive() -> None:
    metrics = classification_metrics([0, 1], [0.2, 0.5], threshold=0.5)

    assert metrics["precision"] == pytest.approx(1.0), (
        f"precision={metrics['precision']}: вероятность ровно на пороге 0.5 "
        "должна считаться положительным предсказанием"
    )
    assert metrics["recall"] == pytest.approx(1.0), (
        f"recall={metrics['recall']}: вероятность ровно на пороге 0.5 "
        "должна считаться положительным предсказанием"
    )


def test_known_metric_values() -> None:
    metrics = classification_metrics([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])

    assert metrics["roc_auc"] == pytest.approx(0.75), f"roc_auc={metrics['roc_auc']}"
    assert metrics["precision"] == pytest.approx(1.0), f"precision={metrics['precision']}"
    assert metrics["recall"] == pytest.approx(0.5), f"recall={metrics['recall']}"
    assert metrics["f1"] == pytest.approx(2 / 3), f"f1={metrics['f1']}"