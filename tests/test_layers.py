"""Структура тестов ЛР5: каждый собранный тест относится ровно к одному слою."""

import pytest

LAYERS = {"data", "evaluation", "model", "api", "pipeline", "project"}


def test_every_test_has_exactly_one_layer(request: pytest.FixtureRequest) -> None:
    wrong = {}
    for item in request.session.items:
        layers = LAYERS & {mark.name for mark in item.iter_markers()}
        if len(layers) != 1:
            wrong.setdefault(item.path.name, sorted(layers))
    assert not wrong, (
        f"Файлы тестов без слоя или с несколькими слоями: {wrong}. "
        "Добавьте файл в LAYER_BY_FILE в tests/conftest.py."
    )
