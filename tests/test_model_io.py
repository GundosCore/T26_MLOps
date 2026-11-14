from pathlib import Path

import joblib
import pytest

from mlops_team1.model_io import REQUIRED_KEYS, load_bundle, main, predict_proba_row
from mlops_team1.train import train_model

FIXTURE = Path(__file__).parents[1] / "tests" / "fixtures" / "flights_sample_v1.csv"


@pytest.fixture
def model(tmp_path: Path) -> Path:
    path = tmp_path / "model.joblib"
    train_model(FIXTURE, path, n_estimators=10, max_depth=3)
    return path


def test_load_bundle_returns_all_required_keys(model: Path) -> None:
    bundle = load_bundle(model)
    assert isinstance(bundle, dict)
    assert set(REQUIRED_KEYS) <= set(bundle)


def test_load_bundle_rejects_file_without_model(model: Path, tmp_path: Path) -> None:
    bundle = joblib.load(model)
    del bundle["model"]
    broken = tmp_path / "broken.joblib"
    joblib.dump(bundle, broken)
    with pytest.raises(ValueError, match="model"):
        load_bundle(broken)


def test_predict_proba_row_returns_probability(model: Path) -> None:
    probability = predict_proba_row(load_bundle(model), 10, 0)
    assert isinstance(probability, float)
    assert 0.0 <= probability <= 1.0


@pytest.mark.parametrize(("dep_hour", "is_weekend"), [(24, 0), (10, 2)])
def test_predict_proba_row_rejects_invalid_input(
    model: Path, dep_hour: int, is_weekend: int
) -> None:
    with pytest.raises(ValueError):
        predict_proba_row(load_bundle(model), dep_hour, is_weekend)


def test_main_prints_probability_for_local_file(
    model: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["--path", str(model), "--dep-hour", "10", "--is-weekend", "0"])
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert any(line.startswith("probability=") for line in lines)


def test_main_returns_2_for_missing_file(tmp_path: Path) -> None:
    assert main(["--path", str(tmp_path / "missing.joblib")]) == 2


CORRUPTIONS = [
    pytest.param(lambda raw: b"not a joblib file", id="garbage-bytes"),
    pytest.param(lambda raw: b"", id="empty-file"),
    pytest.param(lambda raw: raw[: len(raw) // 2], id="truncated-file"),
]


@pytest.mark.parametrize("corrupt", CORRUPTIONS)
def test_load_bundle_rejects_corrupted_file(
    model: Path, tmp_path: Path, corrupt
) -> None:
    broken = tmp_path / "broken.joblib"
    broken.write_bytes(corrupt(model.read_bytes()))
    with pytest.raises(ValueError, match="повреждён"):
        load_bundle(broken)


@pytest.mark.parametrize("corrupt", CORRUPTIONS)
def test_main_returns_2_without_traceback_for_corrupted_file(
    model: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], corrupt
) -> None:
    broken = tmp_path / "broken.joblib"
    broken.write_bytes(corrupt(model.read_bytes()))
    code = main(["--path", str(broken)])
    error = capsys.readouterr().err
    assert code == 2
    assert error.startswith("ERROR: ValueError")
    assert "Traceback" not in error
