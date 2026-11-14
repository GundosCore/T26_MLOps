# Индивидуальная карточка сдачи ЛР4

## Идентификация

- ФИО: Скворцов Никита
- группа: Т.МО41
- команда и GitHub-логин: команда 1, `snikersito`
- роль в ЛР4 и отличие от роли в ЛР3: Quality and documentation reviewer (загрузка модели из run, тесты, соглашение об MLflow, ревью). В ЛР3 я делал вторую версию данных (`generate_v2.py`, решение о версии v2), в ЛР2 разбиение и документ об утечках.
- issue: [#50](https://github.com/GundosCore/T26_MLOps/issues/50)
- pull request: [#57](https://github.com/GundosCore/T26_MLOps/pull/57) (`chore/issue-50-model-io-docs` → `skvortsov`), затем [#60](https://github.com/GundosCore/T26_MLOps/pull/60) (`skvortsov` → `main`); review в [#51](https://github.com/GundosCore/T26_MLOps/pull/51)
- commit SHA: `742332b514da259f2a13c90a8b37790977ebd8d9` (коммит `main`, тег `lr4-v1`, на нём выполнен мой run)

## Личный проверяемый вклад

Связанная задача: #50. Зелёный CI: [run 42511568201](https://github.com/snikersito/T26_MLOps/actions/runs/42511568201).

1. Загрузка модели и предсказание: `src/mlops_team1/model_io.py` (новый файл), коммит [`7ba6174`](https://github.com/GundosCore/T26_MLOps/commit/7ba6174).
   - `load_bundle` (строки 27–35) читает `model.joblib` и проверяет все 7 обязательных ключей (`REQUIRED_KEYS`, строки 16–24).
   - `predict_proba_row` (строки 38–45) проверяет вход (`DepHour` от 0 до 23, `IsWeekend` равен 0 или 1) и возвращает вероятность опоздания.
   - `download_model` (строки 48–64) скачивает `model/model.joblib` из артефактов run по `--run-id`; ошибка MLflow превращается в `ValueError` (строки 62–63).
   - `main` (строки 77–92) возвращает код 0 и печатает `bundle_version` и `probability`, а при ошибке код 2 и строку `ERROR: …`.
2. Тесты: `tests/test_model_io.py`, коммит [`e2ccb73`](https://github.com/GundosCore/T26_MLOps/commit/e2ccb73), 7 тестов: все ключи на месте (строка 19), нет ключа `model` → `ValueError` (25), вероятность в диапазоне 0..1 (34), неверные `dep_hour` и `is_weekend` → `ValueError` (40–41), CLI возвращает 0 (48), нет файла → код 2 (57).
3. Соглашение об экспериментах: `docs/experiments/mlflow-conventions.md` (новый файл), коммит [`795e209`](https://github.com/GundosCore/T26_MLOps/commit/795e209): имена experiment и run (строки 5–9), 8 тегов с источником каждого (10–24), параметры, метрики, inputs, артефакты (25–33), запуск сервера и обучения (34–52), загрузка модели (53–63), что не коммитить (64–67), почему test закрыт (68–).
4. README, тот же коммит: разделы «Эксперименты (ЛР4)» (строка 141) и «Отклонения от задания (ЛР4)» (строка 151), остальные разделы не тронуты.

Критерий приёмки: `ruff check .` чистый, `pytest` на моей ветке: 55 passed, 1 skipped (тест DVC пропускается без хранилища). Отклонение от задания (ошибка MLflow при скачивании артефакта превращается в `ValueError`, поэтому неизвестный run даёт код 2, а не трассировку) описано в описании PR #57.

## Review работы другого участника и найденная проблема

- PR [#51](https://github.com/GundosCore/T26_MLOps/pull/51) (Станислав, обучение с MLflow). Нашёл утечку: граница разбиения в обучении не сдвигалась до конца дня, поэтому при четырёх рейсах в день один и тот же день попадал и в train, и в validation, а валидатор границу сдвигал. То есть обучение и отчёт валидатора делили данные по-разному.
- Исправление пришло в PR [#53](https://github.com/GundosCore/T26_MLOps/pull/53) (Станислав): общая функция `split_cuts`, которой пользуются и валидатор, и обучение. Закреплено тестом `tests/test_split_cuts.py::test_validator_and_training_use_the_same_boundaries` (на 24 строках по 4 рейса в день обе части дают 16/4/4). Ревью #53 выполнил Владимир.

## MLflow run

- experiment: `mlops-tmo41-team1-flight-delay`
- run ID: `67e4802e0d5a48f6908eaee6de56ef02` (статус `candidate`, выставляется обучением по умолчанию)
- run name: `rf-depth-4`
- Git commit: `742332b514da259f2a13c90a8b37790977ebd8d9` (`git.dirty` = false)
- DVC hash: `12e7b5a02885ff28f6560bd895a1330e`
- SHA-256 данных: `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`
- версия контракта: 2.0.0
- split policy: `chronological-60-20-20` (24 строки train, 8 validation, 8 test; `split_train_end` 2026-01-28, `split_validation_end` 2026-02-05, `split_test_end` 2026-02-13)
- параметры: `max_depth` = 4, `n_estimators` = 80, `random_state` = 42, `target_threshold_minutes` = 15, `probability_threshold` = 0.5
- validation-метрики: ROC AUC 0.714286, precision 1.0, recall 0.428571, F1 0.6, доля положительного класса 0.875
- URI модельного артефакта: `file:C:/project_ML/mlflow-server/mlartifacts/1/67e4802e0d5a48f6908eaee6de56ef02/artifacts/model/model.joblib`

## Индивидуальное воспроизведение

- подготовка: `git fetch upstream`, `git switch --detach upstream/main` (коммит `742332b`, `git status --short` пуст); `python -m pip install "dvc>=3,<4"`; архив `dvc-storage` рядом с репозиторием; `dvc pull` (`1 file fetched and 1 file added`, SHA-256 данных `bf35cf01…cff08`, 780 байт); сервер из папки вне репозитория: `mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts`; обучение: `$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"`, затем `python -m mlops_team1.train_mlflow --data data/flights_sample.csv --contract data/contract.json --experiment mlops-tmo41-team1-flight-delay --max-depth 4`
- команда поиска или открытия run: в интерфейсе MLflow (`http://127.0.0.1:5000`) в поле поиска `tags.data.dvc_hash = "12e7b5a02885ff28f6560bd895a1330e"`; run открывается по ID `67e4802e0d5a48f6908eaee6de56ef02`
- команда загрузки артефакта: `$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"`, затем `python -m mlops_team1.model_io --run-id 67e4802e0d5a48f6908eaee6de56ef02 --dep-hour 10 --is-weekend 0`
- вход smoke test: `DepHour` = 10, `IsWeekend` = 0
- полученный результат: `bundle_version=0.2.0`, `probability=0.7091`
- сравниваемые run (из карточки Станислава и отчёта сравнения): `rf-depth-3`, `948852493dc44fecac6c486b74d204b1`, validation ROC AUC 0.571429, статус rejected; `rf-depth-6`, `0f3f587b777f44238bc0a5f9244eaf7e`, ROC AUC 0.714286, статус candidate. Мой `rf-depth-4` на тех же данных и том же коммите даёт 0.714286, как и глубина 6. Это ожидаемо: в validation 8 строк, ROC AUC меняется шагами по 1/7, поэтому глубины 4 и 6 не различимы, выбор предварительный.
- почему test не использовался для выбора: конфигурации сравниваются только по validation, метрики на test не считаются и не логируются. Если выбирать по test, он станет частью подбора и итоговая оценка будет завышена.

## Отрицательный сценарий

```powershell
python -m mlops_team1.model_io --path nope.joblib
$LASTEXITCODE
python -m mlops_team1.model_io --run-id 00000000000000000000000000000000
$LASTEXITCODE
```

Результат (мой запуск, 12.11.2026): в обоих случаях код `2` и строка `ERROR: …` без трассировки: `ERROR: FileNotFoundError: [Errno 2] No such file or directory: 'nope.joblib'` и `ERROR: ValueError: Не удалось скачать модель из run 00000000000000000000000000000000: Run with id=00000000000000000000000000000000 not found`. Без обёртки в `download_model` (строки 62–63) неизвестный run падал бы с исключением MLflow. Случай с файлом закреплён тестом `test_main_returns_2_for_missing_file`, файл без ключа `model` закреплён тестом `test_load_bundle_rejects_file_without_model`.

## Инженерное решение и риск

- выбранное решение и рассмотренная альтернатива: модель грузится из артефакта run (`mlflow.artifacts.download_artifacts`), а не из случайного локального файла: run хранит модель вместе с тегами `git.commit`, `data.dvc_hash`, `data.sha256`, поэтому по одному run ID видно, на каком коде и данных она обучена. Альтернатива: `mlflow.sklearn.log_model` (формат MLflow с сигнатурой). В команде модель сохраняется как `joblib`-бандл, где кроме модели лежат признаки, версия и границы разбиения, поэтому загрузка идёт через `download_artifacts`.
- основной риск: невоспроизводимый run (грязное рабочее дерево, не та версия данных) и неверный вход или повреждённый файл модели. Я столкнулся с этим при повторе: на чистом `main` файла `data/flights_sample.csv` не было, пока не выполнен `dvc pull`.
- тест, tag, metric или artifact, который обнаруживает проблему: для грязного дерева и версии данных теги `git.dirty`, `data.dvc_hash`, `data.sha256` (у моего run `false`, `12e7b5a0…`, `bf35cf01…`); для файла без ключа `test_load_bundle_rejects_file_without_model`; для неверного входа `test_predict_proba_row_rejects_invalid_input`.

## Использование ИИ

- использованный инструмент или «не использовался»: Claude (Anthropic) в чате проекта. ИИ подготовил черновики `model_io.py`, тестов, `mlflow-conventions.md`, разделов README, описаний PR, текстов ревью и этой карточки, помог найти утечку в PR #51 и исправить замечание Ruff TRY004.
- какие фрагменты проверены самостоятельно: запустил `ruff` и `pytest` на своём компьютере (Windows), сервер MLflow, обучение, `model_io` по run ID, `dvc pull`, отрицательный сценарий; сверил теги, параметры и метрики run через `MlflowClient.search_runs`; прочитал `model_io.py` и могу объяснить, как модель скачивается из run, зачем проверяются ключи и почему ошибка MLflow превращается в код 2.
- какими командами или источниками выполнена проверка: `ruff check .`, `pytest -q`, `python -m mlops_team1.train_mlflow ...`, `python -m mlops_team1.model_io --run-id ...`, `dvc pull`, `Get-FileHash`, `MlflowClient.search_runs(...)`, интерфейс MLflow, страницы PR #51, #53, #57, #60.
