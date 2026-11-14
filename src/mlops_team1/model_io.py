"""Загрузка модельного артефакта и повторное предсказание по одной строке.

Модуль импортируется без mlflow: он нужен только для скачивания артефакта из run.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import joblib
import pandas as pd

REQUIRED_KEYS = (
    "model",
    "features",
    "version",
    "split",
    "validation_roc_auc",
    "validation_metrics",
    "parameters",
)


def load_bundle(path: Path) -> dict:
    """Читает файл модели joblib и проверяет, что в нём есть все обязательные ключи."""
    try:
        bundle = joblib.load(path)
    except OSError:
        raise
    except Exception as exc:
        # На повреждённом файле joblib и pickle бросают разные исключения (KeyError, EOFError,
        # ValueError), поэтому приводим их к одному контролируемому ValueError.
        raise ValueError(
            f"Файл модели повреждён или не является файлом joblib: {Path(path).name} "
            f"({type(exc).__name__})"
        ) from exc
    present = set(bundle) if isinstance(bundle, dict) else set()
    missing = [key for key in REQUIRED_KEYS if key not in present]
    if missing:
        kind = "словарь" if isinstance(bundle, dict) else type(bundle).__name__
        raise ValueError(f"В файле модели ({kind}) нет ключей: {', '.join(missing)}")
    return bundle


def predict_proba_row(bundle: dict, dep_hour: int, is_weekend: int) -> float:
    """Вероятность опоздания (ArrDelay >= 15) для одного рейса."""
    if not 0 <= dep_hour <= 23:
        raise ValueError(f"dep_hour должен быть от 0 до 23, получено: {dep_hour}")
    if is_weekend not in (0, 1):
        raise ValueError(f"is_weekend должен быть 0 или 1, получено: {is_weekend}")
    frame = pd.DataFrame([{"DepHour": dep_hour, "IsWeekend": is_weekend}])
    return float(bundle["model"].predict_proba(frame[bundle["features"]])[0, 1])


def download_model(run_id: str, directory: Path) -> Path:
    """Скачивает model/model.joblib из artifact указанного run.

    Адрес сервера берётся из переменной окружения MLFLOW_TRACKING_URI.
    Ошибка MLflow (нет такого run или артефакта) превращается в ValueError,
    чтобы main сообщил о ней кодом 2, а не трассировкой.
    """
    import mlflow
    from mlflow.exceptions import MlflowException

    try:
        local_path = mlflow.artifacts.download_artifacts(
            run_id=run_id, artifact_path="model/model.joblib", dst_path=str(directory)
        )
    except MlflowException as exc:
        raise ValueError(f"Не удалось скачать модель из run {run_id}: {exc}") from exc
    return Path(local_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Предсказание по сохранённой модели")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run-id", help="ID MLflow run, из которого скачать модель")
    source.add_argument("--path", type=Path, help="Путь к локальному файлу model.joblib")
    parser.add_argument("--dep-hour", type=int, default=10)
    parser.add_argument("--is-weekend", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.run_id:
            with tempfile.TemporaryDirectory(prefix="mlops-model-") as temp_dir:
                bundle = load_bundle(download_model(args.run_id, Path(temp_dir)))
        else:
            bundle = load_bundle(args.path)
        probability = predict_proba_row(bundle, args.dep_hour, args.is_weekend)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"bundle_version={bundle['version']}")
    print(f"probability={probability:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
