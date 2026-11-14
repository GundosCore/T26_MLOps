# Индивидуальная карточка сдачи ЛР4

## Идентификация

- ФИО: Соловцов Станислав Алексеевич
- группа: Т.МО41
- команда и GitHub-логин: команда 1, GundosCore
- роль в ЛР4 и отличие от роли в ЛР3: Experiment owner и Model engineer (код обучения и MLflow-запуска, соглашение о тегах, запуск сервера и двух run). В ЛР3 была роль DVC engineer (инициализация DVC, remote, версии данных v1 и v2), в ЛР2 контракт данных и репозиторий.
- issue: [#50](https://github.com/GundosCore/T26_MLOps/issues/50)
- pull request: [#51](https://github.com/GundosCore/T26_MLOps/pull/51) (этап 1, слит merge-коммитом `ebf3fe8`), [#53](https://github.com/GundosCore/T26_MLOps/pull/53) (этап 1б, слит merge-коммитом `50e22a3`), review в [#58](https://github.com/GundosCore/T26_MLOps/pull/58)
- commit SHA: `048a7a4ab0a63de24ed7a0a40ee272f522347612` (коммит `main`, на котором выполнены run)

## Личный проверяемый вклад

1. Этап 1, PR #51 ([diff](https://github.com/GundosCore/T26_MLOps/pull/51/files)). Перенос кода обучения и оценки из стартового проекта преподавателя с заменой модуля на `mlops_team1`; функция `validate_dataset` в валидаторе; чтение DVC-хеша в формате DVC 3 (`- md5:`) в `run_meta.py`; тег `team.code`, файлы `run_summary.md` и `environment/requirements.txt`; правила `.gitignore` (`reports/*` с исключением `reports/experiments/`, `mlflow.db`, `mlartifacts/`); extras `tracking` и установка `.[dev,tracking]` в CI. Критерий приёмки: `ruff` чистый, на моей машине `45 passed`, каждый run получает восемь обязательных тегов.
2. Этап 1б, PR #53 ([diff](https://github.com/GundosCore/T26_MLOps/pull/53/files)). Общая функция `split_cuts`: границы train, validation и test сдвигаются к концу дня одинаково у валидатора и у обучения (замечание Никиты в review PR #51: на данных с несколькими рейсами в день границы расходились). Критерий приёмки: тест `tests/test_split_cuts.py::test_validator_and_training_use_the_same_boundaries` (на 24 строках по 4 рейса в день валидатор и обучение дают разбиение 16/4/4).
3. Review PR #58 (Владимир, отчёт сравнения двух run). Сверил run ID, коммит `048a7a4`, метрики и арифметику (recall 3 из 7, шаг ROC AUC 1/7, разница одна пара ранжирования). Замечания не блокирующие: команду запуска сервера в блоке воспроизведения пометить как отдельный терминал и обновить фразу про `validation.status`. Реакция: после review в PR не добавлялось коммитов (в PR один коммит), отчёт слит как есть.

## MLflow run

- experiment: `mlops-tmo41-team1-flight-delay`
- run ID: `0f3f587b777f44238bc0a5f9244eaf7e` (выбранный, статус candidate)
- run name: `rf-depth-6`
- Git commit: `048a7a4ab0a63de24ed7a0a40ee272f522347612` (`git.dirty` = false)
- DVC hash: `12e7b5a02885ff28f6560bd895a1330e`
- SHA-256 данных: `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`
- версия контракта: 2.0.0
- split policy: `chronological-60-20-20` (24 строки train, 8 validation, 8 test)
- изменённый параметр: `max_depth` 3 -> 6 (`n_estimators` = 80 и `random_state` = 42 у обоих run)
- validation-метрики: ROC AUC 0.714286, precision 1.0, recall 0.428571, F1 0.6, доля положительного класса 0.875
- URI модельного артефакта: C:/projects/Secret Hitler/MLflow-storage/mlartifacts/1/0f3f587b777f44238bc0a5f9244eaf7e/artifacts/model/model.joblib

## Индивидуальное воспроизведение

- команда поиска или открытия run: в интерфейсе MLflow (`http://127.0.0.1:5000`) в поле поиска `tags.data.dvc_hash = "12e7b5a02885ff28f6560bd895a1330e"` находит оба run; нужный run открывается по ID `0f3f587b777f44238bc0a5f9244eaf7e`
- команда загрузки артефакта: `$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"`, затем `python -m mlops_team1.model_io --run-id 0f3f587b777f44238bc0a5f9244eaf7e`
- вход smoke test: `DepHour` = 10, `IsWeekend` = 0 (значения по умолчанию)
- полученный результат: `bundle_version=0.2.0`, `probability=0.7579`
- сравниваемый альтернативный run ID: `948852493dc44fecac6c486b74d204b1` (`rf-depth-3`, validation ROC AUC 0.571429, статус rejected)
- почему test не использовался для выбора: конфигурации сравниваются только по validation ROC AUC, метрики на test не считаются и не логируются. В обучении test-период нужен только для проверки, что в нём есть оба класса. Если выбирать по test, он станет частью подбора и итоговая оценка будет завышена.

## Инженерное решение и риск

- выбранное решение и рассмотренная альтернатива: менять только `max_depth` (3 и 6) при 80 деревьях в обоих run, чтобы разницу метрик можно было отнести к одному параметру. Альтернатива: менять сразу `n_estimators` и `max_depth`, как в примере команд задания (80/3 и 160/6), но тогда непонятно, что именно дало изменение.
- основной риск: расхождение границ разбиения между валидатором и обучением (один день попадает и в train, и в validation) и неверный DVC-хеш в теге run.
- тест, tag, metric или artifact, который обнаруживает проблему: для границ `tests/test_split_cuts.py::test_validator_and_training_use_the_same_boundaries`, параметры run `split_train_rows`, `split_validation_rows`, `split_test_rows` и артефакт `reports/split_manifest.json`; для хеша тест `tests/test_run_meta.py::test_read_dvc_md5_supports_dvc3_format` и тег `data.dvc_hash`.

## Использование ИИ

- использованный инструмент или «не использовался»: Claude (Anthropic) в чате проекта. ИИ помог разобрать задание и распределить роли, подготовил перенос кода стартового проекта и правки (`validate_dataset`, чтение DVC-хеша, `split_cuts`), тесты, описания PR, комментарии review и инструкции по запуску MLflow.
- какие фрагменты проверены самостоятельно: запустил `ruff` и `pytest` на своей машине (Windows); запустил сервер MLflow и два run; сверил метрики и теги run в таблице `search_runs`; выставил `validation.status` (глубина 3 rejected, глубина 6 candidate); загрузил модель по run ID и получил предсказание; прочитал и согласовал отчёт сравнения.
- какими командами или источниками выполнена проверка: `python -m ruff check .`, `python -m pytest -q`, `python -m mlops_team1.train_mlflow ...`, `python -m mlops_team1.model_io --run-id ...`, `mlflow.search_runs(...)`, `MlflowClient.get_run(...)`, интерфейс MLflow, страницы PR #51, #53 и #58.
