# Индивидуальная карточка сдачи ЛР4

## Идентификация

- ФИО: Владимир Псюрников
- Группа: Т.МО41
- Команда и GitHub-логин: команда 1, Chel-ovechek
- Роль в ЛР4 и отличие от роли в ЛР3: Reproducibility reviewer (независимо восстанавливаю данные и два MLflow run тимлида и сверяю результат). В ЛР3 был Documentation reviewer (README, оговорки в документах, ревью карточек).
- Issue: #50
- Pull request: [#58](https://github.com/GundosCore/T26_MLOps/pull/58) (отчёт сравнения); эта карточка идёт отдельным PR
- Commit SHA: `0d9db3b6401d54c68b1bd14a4d27a06a46be0535` (коммит `docs: сравнение двух MLflow run (ЛР4)` в PR #58)

## Личный проверяемый вклад

1. Отчёт сравнения `reports/experiments/lr4-comparison.md` (PR #58, один файл, +56 −0, коммит `0d9db3b`). Критерий приёмки: таблица содержит run ID и метрики run тимлида (`948852493dc44fecac6c486b74d204b1` для глубины 3, `0f3f587b777f44238bc0a5f9244eaf7e` для глубины 6), решение по правилу «по validation ROC AUC, при равенстве меньшая глубина» (глубина 6 — candidate, глубина 3 — rejected), оговорка про validation из 8 строк, раздел воспроизведения. Формулировку решения согласовал с тимлидом до коммита.
2. Независимое воспроизведение двух run на коммите `048a7a4ab0a63de24ed7a0a40ee272f522347612` (изменений в репозитории нет, результат зафиксирован в отчёте и здесь). Критерий приёмки: данные v2 восстановлены, метрики и теги моих run совпадают с run тимлида. Результат: `git status --short` пустой, размер `data/flights_sample.csv` 780 байт, SHA-256 `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`, валидатор вывел 10 строк OK, код 0. Метрики совпали с метриками тимлида до 6-го знака, теги `git.commit`, `git.dirty=false`, `data.dvc_hash`, `data.sha256`, `data.contract_version`, `team.code` совпали.
3. Review другого участника: [PR #59 Екатерины](https://github.com/GundosCore/T26_MLOps/pull/59#pullrequestreview-5837905403) (тесты `evaluate` и `train_model`). Проверил diff, запустил ветку локально (ruff чистый, 65 passed, 1 skipped), сверил сообщения в `match` с `train.py` и `evaluate.py`. Approve с незначительными замечаниями (формат заголовка, заполнение чек-листа и ссылки на CI, слишком широкий `match="пропуски"`). Реакция команды: блокирующих замечаний не было; ответа от автора на момент составления карточки нет.

## MLflow run

Мои run (воспроизведение). Основной run — глубина 6 (candidate), второй — альтернативный.

- Experiment: `mlops-tmo41-team1-flight-delay`
- Run ID: `52fa14defdce47a6ada976768eda516c`
- Run name: `rf-depth-6`
- Git commit: `048a7a4ab0a63de24ed7a0a40ee272f522347612`
- DVC hash: `12e7b5a02885ff28f6560bd895a1330e`
- SHA-256 данных: `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`
- Версия контракта: 2.0.0
- Split policy: `chronological-60-20-20` (24/8/8 строк)
- Изменённый параметр: `max_depth` 3 → 6 (остальное одинаково: `n_estimators=80`, `random_state=42`, порог 0.5)
- Validation-метрики (глубина 6): roc_auc 0.7142857142857143, precision 1.0, recall 0.42857142857142855, f1 0.6, positive_rate 0.875
- URI модельного артефакта: `file:C:/Users/pcurn/OneDrive/Документы/GitHub/MLflow-check/mlartifacts/1/52fa14defdce47a6ada976768eda516c/artifacts` + `model/model.joblib`

## Индивидуальное воспроизведение

- Команда поиска run: в интерфейсе MLflow (`http://127.0.0.1:5000/#/experiments/1/runs`) строка поиска `tags.data.dvc_hash = "12e7b5a02885ff28f6560bd895a1330e"`, результат «2 matching runs» (`rf-depth-6`, `rf-depth-3`); также `MlflowClient("http://127.0.0.1:5000").get_run(<run_id>)` с выводом тегов, метрик и параметров.
- Команда загрузки артефакта: `mlflow.artifacts.download_artifacts(run_id="52fa14defdce47a6ada976768eda516c", artifact_path="model/model.joblib")`, затем `joblib.load`.
- Вход smoke test: одна строка `DepHour=18, IsWeekend=1` (признаки из словаря модели `["DepHour", "IsWeekend"]`).
- Полученный результат: словарь модели содержит ключи `features, model, parameters, split, validation_metrics, validation_roc_auc, version`; `version` 0.2.0; `split` `{'train_end': 24, 'validation_end': 32}`; `parameters` `{'n_estimators': 80, 'max_depth': 6, 'random_state': 42}`; `validation_roc_auc` 0.7142857142857143 совпадает с метрикой run; вероятность опоздания для входа 1.0 (у глубины 3: 0.9751643148518149). Smoke test проверяет, что артефакт загружается и работает, но не качество модели.
- Сравниваемый альтернативный run ID: `578fa5295c1342ffabc32372d237c773` (`rf-depth-3`, validation ROC AUC 0.5714285714285714). Run тимлида: `948852493dc44fecac6c486b74d204b1` (глубина 3) и `0f3f587b777f44238bc0a5f9244eaf7e` (глубина 6).
- Почему test не использовался для выбора: выбор делается только по validation, test-период (8 последних строк, до 2026-02-13) закрыт, чтобы итоговая оценка не стала подогнанной под выбор модели. В отчёте и в метриках run использованы только validation-значения.

## Инженерное решение и риск

- Выбранное решение и рассмотренная альтернатива: глубина 6 как candidate, потому что её validation ROC AUC выше (0.714286 против 0.571429). Альтернатива — глубина 3: более простая модель, выбиралась бы при равенстве метрик по правилу команды.
- Основной риск: выбор по 8 строкам validation (7 опоздавших, 1 нет). ROC AUC принимает значения с шагом 1/7, разница 0.571429 → 0.714286 равна одной паре ранжирования, поэтому преимущество глубины 6 могло получиться случайно. Precision, recall и F1 у обеих моделей одинаковы, при пороге 0.5 различий нет.
- Что обнаруживает проблему: метрика `validation_positive_rate` (0.875) и параметр `split_validation_rows` (8) в run, а также раздел «Ограничение выборки» в `lr4-comparison.md`. Подмену данных обнаруживают теги `data.sha256` и `data.dvc_hash`, незафиксированные правки кода — `git.dirty`. Границы разбиения проверяет тест `tests/test_train_mlflow.py::test_run_experiment_logs_boundaries_shifted_to_end_of_day`.
- Вопрос преподавателя и ответ: «Почему вывод "глубина 6 лучше глубины 3" нельзя считать доказанным?» Ответ: validation содержит 8 строк, из них одна нулевая, поэтому ROC AUC измеряется по 7 парам; разница в одну пару лежит в пределах случайности, остальные метрики равны, а test для выбора не использовался. Для надёжного вывода нужно больше данных или несколько запусков с разными seed.

## Использование ИИ

- Инструмент: Claude (Anthropic), в чате.
- Что делал ИИ: пошаговые инструкции по командам, черновики текстов ревью, отчёта `lr4-comparison.md`, описания PR и этой карточки, объяснение предупреждений MLflow и тестов.
- Какие фрагменты проверены самостоятельно: все команды (восстановление данных, валидатор, запуск MLflow-сервера, два run, скрипт чтения артефактов, ruff и pytest) выполнены мной, результаты видел на своём экране; метрики и теги сверил в интерфейсе MLflow и по выводу `MlflowClient`; ревью PR #59 сделано по diff и локальному запуску.
- Какими командами и источниками проверка выполнена: `git status --short`, `Get-FileHash`, `python -m mlops_team1.validate_data ...`, `python -m ruff check .`, `python -m pytest -q`, `git diff --stat`, `Select-String` по `train.py` и `evaluate.py`, скрипт с `MlflowClient` и `mlflow.artifacts.download_artifacts`; источники: задание ЛР4, инструкция тимлида и мой отчёт `lr4-comparison.md`.
