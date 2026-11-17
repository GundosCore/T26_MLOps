# ЛР6. Индивидуальная карточка Екатерины Головатенко

Учебная группа Т.МО41, команда № 1. GitHub: ekaterinagolowatenko.
Роли: Image engineer и Runtime security engineer.
Дата проверок: 17.11.2026. Среда: Ubuntu 26.04 через WSL, Python 3.12, Docker Engine 29.10.0, Docker Compose v5.7.1.

## Задача и вклад
[Личная issue #81](https://github.com/GundosCore/T26_MLOps/issues/81), [общая #77](https://github.com/GundosCore/T26_MLOps/issues/77).
[PR реализации #85](https://github.com/GundosCore/T26_MLOps/pull/85) в golovatenko, reviewer snikersito.
Коммиты: 9856a04 (Dockerfile и .dockerignore), 9033aa1 (Compose).
Изменены только Dockerfile, .dockerignore и compose.yaml. API, smoke-скрипт и контрактные тесты относятся к другим участникам.

Критерий приёмки: quality gate блокирует некорректную сборку; итоговый контейнер healthy, работает как 10001:10001, ограничивает запись и capabilities, runtime не содержит tests, данных, .git, .env и dev-инструментов.

## Артефакт
Образ: mlops-flight-delay:lr6-9033aa1.
Коммит: 9033aa1045b26c63d5affc83518972721d97c57d.
Image ID: sha256:6ae39f09bb7aee95e85233eb662980ce7ac0f5cba572af9dca7d17bbdec2ac96.
Размер по docker image inspect: 838100008 байт.
Модель: bundle 0.2.0, MODEL_PATH=/app/models/model.joblib.
Базовый образ: python:3.12-slim; digest сборки sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b.
Зависимости ограничены диапазонами pyproject.toml, lock-файла нет: тег SHA связывает образ с кодом, но не гарантирует побайтовое повторение будущей сборки.

## Проверки и результаты
- python -m ruff check .: All checks passed!
- python -m pytest -q: 130 passed, 1 skipped; DVC-проверка пропущена.
- python -m pytest -q -m api: 29 passed.
- python -m pytest -q tests/test_api.py: 16 passed.
- docker build: quality gate, validation (все OK), обучение (Validation ROC AUC 0.417), сборка wheels и runtime успешны.
- docker compose up --detach --wait --wait-timeout 60: healthy.
- docker compose exec app id: uid=10001(app) gid=10001(app).
- /app содержит только models. pytest, ruff, mlflow отсутствуют в runtime.
- /app/lr6-check: OSError Errno 30 Read-only file system; запись в /tmp успешна.
- inspect: ReadonlyRootfs=true, CapDrop=[ALL], SecurityOpt=[no-new-privileges:true], tmpfs /tmp:size=16m,mode=1777.
- Реальный HTTP POST /predict с dep_hour=9, is_weekend=0: HTTP 200, delay_probability=0.8291666666666666, delayed=true, threshold=0.5, model_version=0.2.0, непустой request_id.
- [CI PR #85](https://github.com/GundosCore/T26_MLOps/actions/runs/44065306749): success.

## Кэш
Повторная неизменённая сборка: CACHED.
В контролируемом опыте изменена только строка README: COPY pyproject.toml и установка зависимостей остались CACHED; COPY README, gate, wheels и зависимые runtime-слои перестроились. README восстановлен автоматически. Ранний опыт на git archive дополнительно менял метаданные контекста и не использовался как доказательство изменения только README.

## Негативный сценарий
Ожидаемый сигнал заранее: tests/test_quality.py::test_ping_returns_clean_nonempty_string падает, runtime-образ lr6-defect не создаётся.
После коммитов на отдельной временной копии assert result != "" заменён на assert result == "".
Команда: docker build --progress=plain --tag mlops-flight-delay:lr6-defect .
Факт: код завершения 1; 1 failed, 129 passed, 1 skipped; FAILED tests/test_quality.py::test_ping_returns_clean_nonempty_string.
docker image inspect mlops-flight-delay:lr6-defect не нашёл образ. Рабочая ветка не изменялась.
COPY --from=quality связывает runtime с успешным завершением quality.

## Решения и риски
| Риск | Ограничение | Проверка |
|---|---|---|
| Плохой код или данные | gate Ruff, pytest, validation перед runtime | дефект остановил сборку |
| Лишние файлы и данные | .dockerignore и выборочные COPY | /app только models |
| Избыточные права | USER 10001:10001, cap_drop ALL, no-new-privileges | id и inspect |
| Изменение файлов приложения | read_only и tmpfs /tmp | запись /app запрещена, /tmp разрешена |
| Процесс жив без модели | healthcheck /readyz | healthy; API-тесты для 503 |
| Изменение зависимостей | диапазоны версий, сохранённый image ID | будущая сборка может отличаться |

Обучение выполняется на Git-фикстуре, потому что основной CSV управляется DVC. В quality также нужен data/flights_sample.csv.dvc: test_run_meta читает оттуда хеш. Первый build выявил отсутствие этого файла (1 failed, 129 passed, 1 skipped); исправлено добавлением COPY метаданных, без исключения теста. Контрактные контейнерные тесты и smoke исключены из build gate по договорённости команды; полный pytest запускается локально и в CI.

## Ревью
[Одобрение API PR #84](https://github.com/GundosCore/T26_MLOps/pull/84#pullrequestreview-5936368506).
Проверены четыре файла, совпадение с PR #79, отсутствие конфликтов, Ruff и CI. На момент ревью локальный pytest в доступном Windows-окружении был заблокирован; это явно указано в опубликованном ревью. Позже все наборы успешно выполнены Codex в Ubuntu WSL.

## Доказательства
На ноутбуке: ~/T26_MLOps-lr6/reports/container/.
Файлы: lr6-inspect.txt, lr6-container-inspect.json, lr6-history.txt, lr6-app.log, lr6-build-fixed.log, lr6-final-build.log, lr6-cache.log, lr6-cache-readme-verified.log, lr6-defect.log.
Отчёты не входят в PR реализации: по договорённости там только три файла. Для публикации отчётов в Git требуется отдельное изменение правил reports/ тимлидом.

## Использование ИИ и самостоятельная работа
Использован Codex (OpenAI). Екатерина самостоятельно выполнила установку Docker, проверки version/Compose/hello-world, создание ветки/worktree, исходный pytest (130 passed, 1 skipped), создание файлов и первую сборку; её выводы приведены в переписке. Она также опубликовала review PR #84 с помощью подготовленного текста.
Codex подготовил файлы, диагностировал недостающие DVC-метаданные и внёс исправление, затем сам выполнил повторные тесты, build, Compose, security-проверки и опыты кэша/дефекта через WSL, создал коммиты и PR.
Повторная самостоятельная проверка Екатериной исправленного образа и объяснение решений на защите ещё не подтверждены. Результаты автоматизированных запусков не выдаются за её самостоятельные действия.
