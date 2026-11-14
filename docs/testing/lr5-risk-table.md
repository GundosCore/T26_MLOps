# Тестирование данных, модели и pipeline (ЛР5)

Здесь описана структура тестов, таблица «риск — тест — ожидаемый отказ» и то, где тесты могут дать ложную уверенность. Тесты команды 1 запускаются командой `python -m pytest -q`; общие fixtures лежат в `tests/conftest.py`.

## Слои тестов

Слой задаётся по имени файла в словаре `LAYER_BY_FILE` в `tests/conftest.py` и превращается в маркер pytest. Один слой запускается командой `python -m pytest -q -m <слой>`. Тест `tests/test_layers.py::test_every_test_has_exactly_one_layer` падает, если у какого-то файла тестов нет слоя.

| Слой | Что проверяет | Файлы тестов |
| --- | --- | --- |
| `data` | контракт данных, валидатор, разбиение | `test_data_contract.py`, `test_validate_dataset.py`, `test_split_cuts.py`, `test_generate_v2.py`, `test_data_negative.py` |
| `evaluation` | метрики, пороги, цель `ArrDelay >= 15` | `test_evaluate.py`, `test_evaluation_target.py` |
| `model` | обучение и устройство model bundle | `test_train_model.py`, `test_model_bundle.py` |
| `api` | интерфейс предсказания `model_io` (HTTP API появится в ЛР6–ЛР7) | `test_model_io.py` |
| `pipeline` | связка компонентов, MLflow, метаданные запуска | `test_pipeline_smoke.py`, `test_train_mlflow.py`, `test_run_meta.py`, `test_dvc_refusal.py` |
| `project` | пакет и сама тестовая инфраструктура | `test_smoke.py`, `test_quality.py`, `test_fixtures.py`, `test_layers.py` |

## Риск — тест — ожидаемый отказ

| Риск | Тест (node ID) | Ожидаемый сигнал |
| --- | --- | --- |
| Строка из будущего попала в train | `tests/test_train_model.py::test_train_split_has_ordered_disjoint_dates`, `tests/test_split_cuts.py::test_validator_and_training_use_the_same_boundaries` | assertion о границах дат разбиения |
| В validation или метриках один класс, вероятность вне 0..1, неверный порог | `tests/test_evaluate.py::test_classification_metrics_rejects_invalid_inputs`, `tests/test_train_model.py::test_train_rejects_invalid_data` | `ValueError` с сообщением про оба класса, диапазон или порог |
| Контракт пропустил значение вне диапазона (час 24) | `tests/test_data_negative.py::test_value_outside_contract_is_rejected[dephour-24-above-max]` | провал проверки валидатора `ranges` |
| Контракт отклоняет допустимую границу (час 23) | `tests/test_data_negative.py::test_boundary_value_is_accepted` | `passed` равен `False` для корректных данных |
| Порог цели изменён (`>= 15` стало `> 15`) | `tests/test_evaluation_target.py::test_arrdelay_15_counts_as_late_in_training`, `tests/test_evaluation_target.py::test_arrdelay_15_counts_as_late_in_validator_report` | `ValueError` про один класс при обучении или неверная доля опоздавших в отчёте валидатора |
| Порядок признаков в bundle изменился | `tests/test_model_bundle.py::test_bundle_declares_features_in_contract_order` | assertion: список признаков не совпадает с `["DepHour", "IsWeekend"]` |
| В bundle нет обязательного поля (например, версии) | `tests/test_model_bundle.py::test_bundle_without_required_key_is_rejected[version]`, `tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain` | `ValueError`: в файле модели нет ключей: `version`; smoke падает на шаге load |
| Обучение не воспроизводится при одном seed | `tests/test_model_bundle.py::test_training_is_deterministic_for_same_seed`, `tests/test_model_bundle.py::test_seed_is_reflected_in_run_params` | различие метрики или вероятностей, либо в параметрах run нет seed |
| Модельный файл повреждён | `tests/test_model_io.py::test_load_bundle_rejects_corrupted_file`, `tests/test_model_io.py::test_main_returns_2_without_traceback_for_corrupted_file` | контролируемый `ValueError`, у командной строки код 2 без трассировки |
| Интерфейс предсказания и bundle расходятся (замена API-теста до ЛР6–ЛР7) | `tests/test_pipeline_smoke.py::test_cli_reports_same_version_and_probability_as_bundle` | версия или вероятность в выводе не совпадают с bundle |
| Сквозная связка validate, train, load, predict рвётся | `tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain` | сообщение assert называет слой отказа (validate, train, load или predict) |
| Эксперимент запущен на данных, не прошедших контракт | `tests/test_train_mlflow.py::test_run_experiment_refuses_data_that_fails_contract` | `ValueError`: набор не прошёл контракт данных |
| Тест изменил эталонный CSV | `tests/test_fixtures.py::test_changing_valid_frame_does_not_touch_reference_csv` | различие SHA-256 эталонного файла |
| Новый файл тестов остался без слоя | `tests/test_layers.py::test_every_test_has_exactly_one_layer` | assertion со списком файлов без слоя |

## Где тесты могут дать ложную уверенность

- **Маленький набор.** Эталон `flights_sample_v1.csv` содержит 24 строки, в validation всего 5. ROC AUC на нём шумный, поэтому тесты модели проверяют форму, диапазон, порядок признаков и повторяемость, а не качество.
- **Порог цели записан в трёх местах:** литерал `15` в `train.py`, `LATE_MINUTES` в `validate_data.py` и `TARGET_THRESHOLD_MINUTES` в `train_mlflow.py`. Тесты ЛР5 закрывают первые два, третье место отдельным тестом не покрыто.
- **Слой API.** HTTP-сервиса пока нет, слой `api` проверяет функции и командную строку `model_io`. Коды ответов, сериализация и сеть не проверяются до ЛР6–ЛР7.
- **DVC.** В CI DVC не ставится, поэтому тест `tests/test_dvc_refusal.py` там пропускается. Положительный отчёт `reports/tests/lr5-pass.xml` снят с установленным DVC.
- **Данные.** Smoke test идёт на эталоне v1 из `tests/fixtures/`, а не на рабочем наборе v2 под DVC.
- **Окружение.** Повторяемость обучения проверена на одной версии scikit-learn и одной платформе.
