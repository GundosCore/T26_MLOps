# mlops-team1

Учебный проект команды 1 по курсу MLOps (ЛР1): репозиторий и воспроизводимая среда.

## Требования

- Git
- Python **3.12** (проверьте: `python --version`)

## Установка

Клонируйте репозиторий и перейдите в его папку, затем создайте окружение.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Linux или macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

После активации в начале строки терминала должно быть `(.venv)`.

## Проверки

```bash
python -m ruff check .
python -m pytest -q
```

Ожидаемый результат: `All checks passed!` и `2 passed`.

## Запуск

```bash
python -c "import mlops_team1; print(mlops_team1.ping())"
```

Ожидаемый вывод: `pong`.

## Структура

- `src/mlops_team1/` — код проекта
- `tests/` — тесты
- `.github/workflows/ci.yml` — автоматические проверки (CI)
- `data/` — данные (в Git не добавляются)
- `docs/` — документация
