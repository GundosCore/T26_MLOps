"""Интеграционный smoke test ЛР5: validate -> train -> load -> predict."""

from pathlib import Path

import pandas as pd
import pytest

from mlops_team1.model_io import load_bundle, main, predict_proba_row
from mlops_team1.train import train_model
from mlops_team1.validate_data import validate_dataset


def test_validate_train_load_predict_chain(
    valid_frame: pd.DataFrame, csv_factory, contract_path: Path, tmp_path: Path
) -> None:
    data_path = csv_factory(valid_frame)

    # Слой validate: данные проходят контракт.
    report = validate_dataset(data_path, contract_path)
    failed = [check["name"] for check in report["checks"] if not check["passed"]]
    assert report["passed"] is True, f"Слой validate: провалены проверки {failed}"

    # Слой train: обучение во временный файл.
    model_path = tmp_path / "artifacts" / "model.joblib"
    score = train_model(data_path, model_path)
    assert model_path.is_file(), "Слой train: файл модели не создан"
    assert 0.0 <= score <= 1.0, f"Слой train: ROC AUC вне диапазона: {score}"

    # Слой load: файл читается и содержит версию формата.
    bundle = load_bundle(model_path)
    assert bundle["version"] == "0.2.0", f"Слой load: версия {bundle['version']!r}"

    # Слой predict: строка в порядке features, форма и диапазон вероятности.
    row = pd.DataFrame([{"DepHour": 10, "IsWeekend": 0}])[bundle["features"]]
    probabilities = bundle["model"].predict_proba(row)
    assert probabilities.shape == (1, 2), f"Слой predict: форма {probabilities.shape}"
    assert (
        (0.0 <= probabilities) & (probabilities <= 1.0)
    ).all(), "Слой predict: вне [0, 1]"
    assert predict_proba_row(bundle, 10, 0) == pytest.approx(probabilities[0, 1])


def test_cli_reports_same_version_and_probability_as_bundle(
    valid_frame: pd.DataFrame,
    csv_factory,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model_path = tmp_path / "model.joblib"
    train_model(csv_factory(valid_frame), model_path)
    bundle = load_bundle(model_path)

    code = main(["--path", str(model_path), "--dep-hour", "10", "--is-weekend", "0"])
    output = dict(line.split("=", 1) for line in capsys.readouterr().out.splitlines())

    assert code == 0
    assert output["bundle_version"] == bundle["version"]
    assert float(output["probability"]) == pytest.approx(
        predict_proba_row(bundle, 10, 0), abs=1e-4
    )
