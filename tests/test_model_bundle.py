import re
from pathlib import Path

import joblib
import pandas as pd
import pytest

from mlops_team1.model_io import main
from mlops_team1.train import FEATURES, train_model
from mlops_team1.validate_data import split_cuts

EXPECTED_FEATURES = ["DepHour", "IsWeekend"]
REQUIRED_KEYS = {
    "model",
    "features",
    "version",
    "split",
    "validation_roc_auc",
    "validation_metrics",
    "parameters",
}


@pytest.fixture
def bundle(trained_model_path: Path) -> dict:
    return joblib.load(trained_model_path)


def _validation_part(frame: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """Validation-фрагмент в том же порядке, в каком его видит train_model."""
    data = frame.copy()
    data["FlightDate"] = pd.to_datetime(data["FlightDate"])
    data = data.sort_values("FlightDate", kind="stable").reset_index(drop=True)
    split = bundle["split"]
    return data.iloc[split["train_end"] : split["validation_end"]][FEATURES]


def test_bundle_has_required_keys(bundle: dict) -> None:
    missing = REQUIRED_KEYS - set(bundle)
    assert not missing, f"В bundle нет обязательных ключей: {sorted(missing)}"


def test_bundle_features_keep_exact_order(bundle: dict) -> None:
    assert bundle["features"] == EXPECTED_FEATURES, (
        f"Порядок признаков в bundle: {bundle['features']}, ожидалось {EXPECTED_FEATURES}. "
        "Клиент строит DataFrame по этому списку, перестановка меняет смысл столбцов"
    )


def test_bundle_version_is_semver_string(bundle: dict) -> None:
    version = bundle["version"]
    assert isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version), (
        f"version={version!r}: ожидалась строка вида 'X.Y.Z'"
    )


def test_bundle_parameters_and_seed_are_saved(
    tmp_path: Path, valid_frame: pd.DataFrame, csv_factory
) -> None:
    data_path = csv_factory(valid_frame)
    model_path = tmp_path / "custom.joblib"
    train_model(data_path, model_path, n_estimators=7, max_depth=3, random_state=11)

    saved = joblib.load(model_path)

    assert saved["parameters"] == {"n_estimators": 7, "max_depth": 3, "random_state": 11}, (
        f"parameters={saved['parameters']}"
    )
    assert saved["model"].random_state == 11, f"random_state модели: {saved['model'].random_state}"


def test_bundle_split_bounds_are_ordered(bundle: dict, valid_frame: pd.DataFrame) -> None:
    split = bundle["split"]
    assert 0 < split["train_end"] < split["validation_end"] < len(valid_frame), (
        f"split={split}, строк в наборе: {len(valid_frame)}"
    )


def test_bundle_split_matches_split_cuts(bundle: dict, valid_frame: pd.DataFrame) -> None:
    dates = sorted(pd.to_datetime(valid_frame["FlightDate"]).tolist())
    train_end, validation_end = split_cuts(dates)

    assert bundle["split"] == {"train_end": train_end, "validation_end": validation_end}, (
        f"split в bundle {bundle['split']}, split_cuts даёт ({train_end}, {validation_end})"
    )


def test_bundle_validation_metrics_are_consistent(bundle: dict) -> None:
    metrics = bundle["validation_metrics"]

    assert {"roc_auc", "precision", "recall", "f1"} <= set(metrics), f"ключи: {sorted(metrics)}"
    for name in ("roc_auc", "precision", "recall", "f1"):
        assert 0.0 <= metrics[name] <= 1.0, f"{name}={metrics[name]} вне диапазона 0..1"
    assert bundle["validation_roc_auc"] == pytest.approx(metrics["roc_auc"]), (
        "validation_roc_auc расходится с validation_metrics['roc_auc']"
    )


def test_model_has_predict_proba_and_class_order(bundle: dict) -> None:
    model = bundle["model"]

    assert hasattr(model, "predict_proba"), "У модели нет метода predict_proba"
    assert list(model.classes_) == [0, 1], (
        f"classes_={list(model.classes_)}: столбец 1 должен быть вероятностью опоздания"
    )


def test_predict_proba_shape_and_range_for_one_row(bundle: dict) -> None:
    row = pd.DataFrame([{"DepHour": 18, "IsWeekend": 1}])[bundle["features"]]

    proba = bundle["model"].predict_proba(row)

    assert proba.shape == (1, 2), f"Форма предсказания {proba.shape}, ожидалась (1, 2)"
    assert 0.0 <= proba[0, 1] <= 1.0, f"P(late)={proba[0, 1]} вне диапазона 0..1"
    assert proba[0].sum() == pytest.approx(1.0), f"Сумма вероятностей {proba[0].sum()}"


def test_training_is_deterministic_for_same_seed(
    tmp_path: Path, valid_frame: pd.DataFrame, csv_factory
) -> None:
    data_path = csv_factory(valid_frame)
    first_path = tmp_path / "first.joblib"
    second_path = tmp_path / "second.joblib"

    first_auc = train_model(data_path, first_path, n_estimators=10, random_state=5)
    second_auc = train_model(data_path, second_path, n_estimators=10, random_state=5)

    assert first_auc == pytest.approx(second_auc), f"ROC AUC: {first_auc} и {second_auc}"
    first, second = joblib.load(first_path), joblib.load(second_path)
    part = _validation_part(valid_frame, first)
    assert first["model"].predict_proba(part)[:, 1] == pytest.approx(
        second["model"].predict_proba(part)[:, 1]
    ), "Вероятности на validation различаются при одинаковом seed"


def test_seed_is_saved_in_bundle(tmp_path: Path, valid_frame: pd.DataFrame, csv_factory) -> None:
    data_path = csv_factory(valid_frame)
    for seed in (1, 2):
        model_path = tmp_path / f"seed-{seed}.joblib"
        train_model(data_path, model_path, n_estimators=10, random_state=seed)

        saved_seed = joblib.load(model_path)["parameters"]["random_state"]

        assert saved_seed == seed, f"В bundle seed={saved_seed}, обучали с {seed}"


def test_cli_reports_same_version_as_bundle(
    trained_model_path: Path, bundle: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["--path", str(trained_model_path)])

    lines = capsys.readouterr().out.splitlines()
    assert code == 0, f"main вернул код {code}"
    assert f"bundle_version={bundle['version']}" in lines, (
        f"Вывод main: {lines}, версия в bundle: {bundle['version']}"
    )


def test_seed_is_reflected_in_run_params(
    tmp_path: Path, valid_frame: pd.DataFrame, csv_factory, contract_path: Path
) -> None:
    mlflow = pytest.importorskip("mlflow")
    from mlops_team1.train_mlflow import run_experiment

    previous = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri(f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    try:
        experiment = "lr5-seed"
        mlflow.create_experiment(experiment, artifact_location=(tmp_path / "artifacts").as_uri())

        run_id = run_experiment(csv_factory(valid_frame), contract_path, experiment, 10, 3, 7)

        params = mlflow.MlflowClient().get_run(run_id).data.params
        assert params["random_state"] == "7", f"random_state в run: {params.get('random_state')}"
    finally:
        mlflow.set_tracking_uri(previous)