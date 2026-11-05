import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Пропускаем тест в CI, если DVC не установлен
pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("dvc") is None,
    reason="DVC is not installed, skipping DVC refusal test"
)


def test_dvc_status_detects_modification(tmp_path: Path):
    """
    Сценарий: файл изменён вручную без dvc add.
    Ожидание: 
      - dvc status --quiet возвращает код 1
      - обычный dvc status содержит слово 'modified'
    """
    env = os.environ.copy()
    env["DVC_NO_ANALYTICS"] = "1"

    # 1. Инициализируем DVC без SCM во временной папке
    subprocess.run(
        [sys.executable, "-m", "dvc", "init", "--no-scm"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    # 2. Копируем тестовую фикстуру во временную папку
    fixture_path = Path(__file__).parent / "fixtures" / "flights_sample_v1.csv"
    target_csv = tmp_path / "flights_sample.csv"
    shutil.copy(fixture_path, target_csv)

    # 3. Добавляем файл под контроль DVC
    subprocess.run(
        [sys.executable, "-m", "dvc", "add", str(target_csv)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    # 4. Проверяем, что статус чистый (код 0)
    result_clean = subprocess.run(
        [sys.executable, "-m", "dvc", "status", "--quiet"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=False,  # Явно указываем, что не хотим падения
    )
    assert result_clean.returncode == 0, f"Expected clean status (0), got {result_clean.returncode}"

    # 5. Модифицируем файл (дописываем строку)
    with open(target_csv, "a", encoding="utf-8") as f:
        f.write("2026-01-29,9,0,10\n")

    # 6a. Проверяем через --quiet: должен вернуть код 1 (без вывода)
    result_quiet = subprocess.run(
        [sys.executable, "-m", "dvc", "status", "--quiet"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result_quiet.returncode == 1, (
        f"Expected modified status code 1 from --quiet, got {result_quiet.returncode}"
    )

    # 6b. Проверяем через обычный dvc status: в выводе должно быть слово 'modified'
    result_verbose = subprocess.run(
        [sys.executable, "-m", "dvc", "status"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    output = (result_verbose.stdout + result_verbose.stderr).lower()
    assert "modified" in output, (
        f"Expected 'modified' in dvc status output, got:\nstdout: {result_verbose.stdout}\nstderr: {result_verbose.stderr}"
    )