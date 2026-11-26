# ЛР6. Индивидуальная карточка Скворцова Никиты

Учебная группа Т.МО41, команда № 1. GitHub: snikersito.
Роль: Quality reviewer.

## Задача и вклад
[Личная issue #83](https://github.com/GundosCore/T26_MLOps/issues/83), [общая #77](https://github.com/GundosCore/T26_MLOps/issues/77).
Мои коммиты в main: 5581ac7 (`test: контрактные тесты Dockerfile и Compose (ЛР6)`), 0571f21 (`docs: таблица рисков контейнера (ЛР6)`, PR #89).
Dockerfile, compose.yaml и .dockerignore написаны Екатериной Головатенко (PR #85), я их не менял.

## Личный артефакт
`tests/test_container_contract.py`: 12 статических тестов, которые читают Dockerfile, compose.yaml и .dockerignore как текст (pytest, `yaml.safe_load`). Для них в `pyproject.toml` добавлена зависимость `pyyaml>=6,<7` в группе `dev`.

Тесты: стадии `quality` и `runtime`; quality gate (ruff, pytest, validation, обучение); модель копируется из стадии quality; `USER 10001:10001`; healthcheck по `/readyz` без curl; `CMD` в exec-форме с портом 8080; нет тега `latest`; нет поля `version` в Compose; `read_only`, `tmpfs`, `cap_drop: [ALL]`, `no-new-privileges`; порт хоста через `APP_PORT`; нет секретов в `environment`; `.dockerignore` исключает `.git`, `.env`, данные, модели, кэши.

Таблица рисков: [docs/containers/lr6-risk-table.md](https://github.com/GundosCore/T26_MLOps/blob/main/docs/containers/lr6-risk-table.md). 9 рисков в формате «риск, ограничение, проверка» (статический тест и динамическая команда Docker) и раздел «Что тесты не доказывают».

## Что тесты не доказывают
Тесты проверяют текст файлов, а не образ. Они не показывают, что образ собирается, контейнер становится healthy, модель лежит в `/app/models`, а запись вне `/tmp` реально блокируется. Эти свойства проверяют динамические команды из таблицы и отказы Docker, которые воспроизвели Екатерина и Станислав (раздел «Воспроизведённые отказы» в таблице рисков). Сам я эти два отказа в Docker не запускал.

## Ревью
Одобрил PR #85 (Dockerfile, compose.yaml, .dockerignore). Docker при этом ревью я не запускал: проверка была по тексту файлов и по зелёному CI.

## Использование ИИ и самостоятельная работа
Использован Claude (Anthropic) как помощник: он подготовил текст тестов и таблицы рисков, а также команды проверки. Файлы в репозиторий я создавал, запускал `ruff` и `pytest`, коммитил и открывал PR сам через GitHub Desktop. Claude не является соавтором коммитов. Объяснение тестов и ограничений на защите остаётся за мной.