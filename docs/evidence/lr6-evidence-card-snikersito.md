# ЛР6. Индивидуальная карточка Скворцова Никиты Дмитриевича

Учебная группа Т.МО41, команда № 1. GitHub: snikersito.

## Командная версия ЛР6
Аннотированный тег `lr6-v1` указывает на коммит `f2b320f5dacd32a8025333fa04f361e08ccf69ba`. Командный образ `mlops-flight-delay:lr6-98c7a6f` собран из коммита `98c7a6f`, Image ID `sha256:9b1c2fff98a9c514b0788ba79bfae11f8e9cf8e9df7019c76fb271d0584901dc` (совпадает с `reports/container/lr6-inspect.txt` в main).

## Роль
Quality reviewer. В ЛР5 я был Evaluation test engineer и писал `tests/test_evaluation_target.py` (граница цели и метрики на пороге). В ЛР6 я проверяю не метрики, а контракт контейнера: что Dockerfile, Compose и .dockerignore содержат заявленные ограничения.

## Задача и вклад
[Личная issue #83](https://github.com/GundosCore/T26_MLOps/issues/83), [общая #77](https://github.com/GundosCore/T26_MLOps/issues/77).
Критерии приёмки из issue #83:
- тесты проверяют по файлам: non-root USER, нет latest, нет поля version в Compose, healthcheck по /readyz;
- таблица рисков покрывает минимум шесть строк из раздела 16 задания;
- воспроизведены минимум два отказа (по разделу 15) с командой и фрагментом лога.

Мои коммиты в main: 5581ac7 (`test: контрактные тесты Dockerfile и Compose (ЛР6)`), 0571f21 (`docs: таблица рисков контейнера (ЛР6)`, PR #89). Dockerfile, compose.yaml и .dockerignore написала Екатерина Головатенко (PR #85), я их не менял.

## Личный артефакт
`tests/test_container_contract.py`: 12 статических тестов, которые читают Dockerfile, compose.yaml и .dockerignore как текст (pytest, `yaml.safe_load`). Для них в `pyproject.toml` добавлена зависимость `pyyaml>=6,<7` в группе `dev`.

Тесты: стадии quality и runtime; quality gate (ruff, pytest, validation, обучение); модель копируется из стадии quality; `USER 10001:10001`; healthcheck по `/readyz` без curl; `CMD` в exec-форме с портом 8080; нет тега latest; нет поля version в Compose; read_only, tmpfs, cap_drop ALL, no-new-privileges; порт хоста через APP_PORT; нет секретов в environment; .dockerignore исключает .git, .env, данные, модели, кэши.

Таблица рисков: [docs/containers/lr6-risk-table.md](https://github.com/GundosCore/T26_MLOps/blob/main/docs/containers/lr6-risk-table.md). 9 рисков в формате «риск, ограничение, проверка» и раздел «Что тесты не доказывают». Критерий 1 и 2 выполнены моими файлами. Критерий 3: два отказа в Docker воспроизвели Екатерина и Станислав, их описание добавлено в раздел «Воспроизведённые отказы» (коммит 7766727). Сам я эти отказы в Docker не запускал.

## Проверка
Команда: `python -m pytest -q tests/test_container_contract.py`. Результат на коммите b42c616 (main): `12 passed`.

## Defect injection
Ожидаемый сигнал назван заранее: падает `tests/test_container_contract.py::test_runtime_runs_as_non_root_with_explicit_ids`.
Дефект на временной ветке `scratch/lr6-defect` от upstream/main: в `Dockerfile` строка `USER 10001:10001` заменена на `USER root` (`git diff --stat`: 1 insertion, 1 deletion).
Команда: `python -m pytest -q "tests/test_container_contract.py::test_runtime_runs_as_non_root_with_explicit_ids"`.
Факт: `1 failed`, `AssertionError: в Dockerfile нет строки 'USER <uid>:<gid>' с числовыми значениями`.
Весь файл: `1 failed, 11 passed`. Правка откатана `git restore Dockerfile`, ветка удалена, в PR дефект не попадал.
Что это показывает: статический тест ловит запуск от root. Чего не ловит: образ может собраться неверно при правильном тексте Dockerfile.

## Инженерное решение
Тесты читают текст файлов, а не собирают образ. Альтернатива: запускать `docker build` и `docker compose up` из pytest. Я выбрал текст, потому что набор работает за доли секунды, не требует Docker в CI и ловит самые частые поломки (root, latest, потерянные ограничения). Цена выбора: тесты не доказывают, что образ собирается и контейнер становится healthy. Это закрывают динамические команды из таблицы рисков и отказы, воспроизведённые в Docker.

## Ревью
Одобрил PR #85 (Dockerfile, compose.yaml, .dockerignore). Docker при этом ревью я не запускал: проверка была по тексту файлов и по зелёному CI.

## Использование ИИ и самостоятельная работа
Использован Claude (Anthropic) как помощник: он подготовил текст тестов и таблицы рисков, а также команды проверки. Файлы в репозиторий я создавал, запускал ruff и pytest, провёл defect injection, коммитил и открывал PR сам через GitHub Desktop. Claude не является соавтором коммитов. Объяснение тестов и ограничений на защите остаётся за мной.